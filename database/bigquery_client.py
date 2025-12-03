# database/bigquery_client.py
#
# Thin BigQuery client wrapper.
# Uses settings from parameters/config.yaml via get_settings().

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from google.cloud import bigquery

from functions.utils.settings import get_settings


@lru_cache()
def get_bigquery_client() -> bigquery.Client:
    """Return a singleton BigQuery client configured with project & location."""
    settings = get_settings()
    return bigquery.Client(
        project=settings.gcp_project_id,
        location=settings.bq_location,
    )


def run_query(sql: str, job_config: Optional[bigquery.job.QueryJobConfig] = None) -> List[Dict[str, Any]]:
    """Execute a SQL query and return rows as list[dict]."""
    client = get_bigquery_client()
    query_job = client.query(sql, job_config=job_config)
    rows = query_job.result()
    return [dict(row) for row in rows]
