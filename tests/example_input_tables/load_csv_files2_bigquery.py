#!/usr/bin/env python
"""
Bulk-load all CSV files in this folder into BigQuery.

Usage examples:

1) Use default GOOGLE_CLOUD_PROJECT and autodetect schema:
   python load_csv_files2_bigquery.py --dataset_id=my_dataset

2) Explicit project:
   python load_csv_files2_bigquery.py \
       --project_id=poc-piloturl-nonprod \
       --dataset_id=gold_layer

3) Custom location (e.g. asia-southeast1):
   python load_csv_files2_bigquery.py \
       --project_id=poc-piloturl-nonprod \
       --dataset_id=gold_layer \
       --location=asia-southeast1
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import List, Optional

from google.cloud import bigquery


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load all CSV files in this folder into BigQuery tables."
    )
    parser.add_argument(
        "--project_id",
        type=str,
        default=os.getenv("GOOGLE_CLOUD_PROJECT"),
        help="GCP project ID (default: from GOOGLE_CLOUD_PROJECT env var)",
    )
    parser.add_argument(
        "--dataset_id",
        type=str,
        required=True,
        help="BigQuery dataset ID (required)",
    )
    parser.add_argument(
        "--location",
        type=str,
        default=None,
        help="BigQuery location (e.g. asia-southeast1). Optional.",
    )
    parser.add_argument(
        "--skip_leading_rows",
        type=int,
        default=1,
        help="Number of header rows to skip in each CSV (default: 1).",
    )
    parser.add_argument(
        "--no_autodetect",
        action="store_true",
        help="Disable schema autodetect (you would then need to define schema manually in code).",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="If set, only print what would be done, do not actually load tables.",
    )
    return parser.parse_args()


def get_csv_files(folder: Path) -> List[Path]:
    """Return a list of CSV files in the given folder (non-recursive)."""
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".csv")


def make_bq_client(project_id: str, location: Optional[str]) -> bigquery.Client:
    if not project_id:
        raise ValueError(
            "Project ID is not set. Use --project_id or set GOOGLE_CLOUD_PROJECT."
        )

    client = bigquery.Client(project=project_id, location=location)
    return client


def load_single_csv_to_bq(
    client: bigquery.Client,
    csv_path: Path,
    project_id: str,
    dataset_id: str,
    skip_leading_rows: int = 1,
    autodetect: bool = True,
    dry_run: bool = False,
) -> None:
    """
    Load a single CSV file to BigQuery.
    Automatically uses the CSV header row as column names.
    BOM-safe and delimiter-aware.

    Extra safety:
    - Detects delimiter (",", "|" or tab).
    - Validates that data rows have the same number of columns as the header.
      If not, raises a ValueError so we don't create a half-broken table.
    """

    table_id = f"{project_id}.{dataset_id}.{csv_path.stem}"
    logger.info("Preparing load job: file=%s -> table=%s", csv_path, table_id)

    # ---------- Read header row (BOM-safe) ----------
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        header_line = f.readline().rstrip("\n\r")

        if not header_line:
            raise ValueError(f"CSV {csv_path.name} has empty first line (no header)")

        # Detect delimiter: prefer ',' but support '|' and '\t'
        delimiter = ","
        if "|" in header_line:
            delimiter = "|"
        elif "\t" in header_line:
            delimiter = "\t"

        raw_cols = header_line.replace("\ufeff", "").split(delimiter)

        column_names: list[str] = []
        for raw in raw_cols:
            clean = raw.strip()
            if not clean:
                continue  # drop empty header cells (e.g. trailing comma)
            clean = "".join(ch for ch in clean if ch.isprintable())
            if clean:
                column_names.append(clean)

        if not column_names:
            raise ValueError(
                f"CSV {csv_path.name} has no valid column names after cleaning"
            )

        expected_cols = len(column_names)

        # ---------- Quick validation of a few data rows ----------
        import csv as _csv

        reader = _csv.reader(f, delimiter=delimiter)
        for line_no, row in enumerate(reader, start=2):
            # skip completely empty lines
            if not row or all(cell.strip() == "" for cell in row):
                continue
            if len(row) != expected_cols:
                raise ValueError(
                    f"Column count mismatch in {csv_path.name} at line {line_no}: "
                    f"expected {expected_cols}, got {len(row)}. "
                    f"Row={row!r}"
                )
            # We only need to sample a few lines
            if line_no > 20:
                break

    logger.info(
        "Detected delimiter='%s' and columns=%s for file=%s",
        delimiter,
        column_names,
        csv_path.name,
    )

    # ---------- Build schema ----------
    schema = [
        bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.STRING)
        for col in column_names
    ]

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=skip_leading_rows,
        autodetect=autodetect,  # types only
        schema=schema,          # enforce column names
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        field_delimiter=delimiter,
    )

    if dry_run:
        logger.info("[DRY RUN] Would load %s into %s", csv_path.name, table_id)
        logger.info("Schema would be: %s", [f"{c.name}:{c.field_type}" for c in schema])
        return

    # ---------- Execute load job ----------
    with csv_path.open("rb") as f:
        load_job = client.load_table_from_file(
            f,
            table_id,
            job_config=job_config,
        )

    logger.info("Started job %s for file %s", load_job.job_id, csv_path.name)
    result = load_job.result()
    logger.info(
        "Completed load for %s. Output rows: %s",
        csv_path.name,
        getattr(result, "output_rows", "unknown"),
    )

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    args = parse_args()

    # Folder where this script lives (tests/example_input_tables).
    folder = Path(__file__).resolve().parent
    logger.info("Looking for CSV files in folder: %s", folder)

    csv_files = get_csv_files(folder)
    if not csv_files:
        logger.warning("No CSV files found in %s", folder)
        return

    logger.info("Found %d CSV files: %s", len(csv_files), [f.name for f in csv_files])

    client = make_bq_client(args.project_id, args.location)

    for csv_path in csv_files:
        try:
            load_single_csv_to_bq(
                client=client,
                csv_path=csv_path,
                project_id=args.project_id,
                dataset_id=args.dataset_id,
                skip_leading_rows=args.skip_leading_rows,
                autodetect=not args.no_autodetect,
                dry_run=args.dry_run,
            )
        except Exception as e:
            logger.exception("Failed to load %s: %s", csv_path.name, e)


if __name__ == "__main__":
    main()
