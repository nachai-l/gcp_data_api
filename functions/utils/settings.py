# functions/utils/settings.py
#
# Centralized configuration loader for the E-port Data API.
# Reads parameters/config.yaml (nested structure) and exposes
# a flattened AppSettings object used by repositories and clients.

from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Global app configuration with flattened, convenient fields."""

    # Core GCP / BigQuery config
    gcp_project_id: str = Field(..., description="GCP project ID")
    bq_dataset_id: str = Field(..., description="BigQuery dataset ID")
    bq_location: str = Field("asia-southeast1", description="BigQuery region")

    # Logical table-name mapping, used to build the `allowed` dict
    table_names: Dict[str, str] = Field(
        default_factory=dict,
        description="Logical → physical BigQuery table name mapping",
    )

    # Which sections the downstream CV generation is allowed to touch
    allowed_sections: List[str] = Field(default_factory=list)

    # Default ordering + limits for some queries
    default_ordering: Dict[str, str] = Field(default_factory=dict)
    default_limit_single_row: int = Field(1)

    # Common column/key names
    columns: Dict[str, str] = Field(default_factory=dict)

    class Config:
        env_prefix = ""  # no prefix required
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> AppSettings:
    """
    Load settings from parameters/config.yaml and/or env vars.

    Matches YAML of the form:

        gcp:
          project_id: poc-piloturl-nonprod
          dataset: gold_layer
          location: asia-southeast1

        tables:
          student: "student"
          ...

        allowed_sections:
          - profile_summary
          ...

        defaults:
          ordering:
            education: "ORDER BY start_year DESC, end_year DESC"
            ...
          limit_single_row: 1

        columns:
          key_user_id: "user_id"
          ...

    """
    # Locate YAML relative to this file
    yaml_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "parameters",
        "config.yaml",
    )
    yaml_path = os.path.abspath(yaml_path)

    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Config file not found: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    gcp_cfg = raw.get("gcp", {}) or {}
    tables_cfg = raw.get("tables", {}) or {}
    defaults_cfg = raw.get("defaults", {}) or {}
    ordering_cfg = defaults_cfg.get("ordering", {}) or {}
    limit_single_row = defaults_cfg.get("limit_single_row", 1)
    allowed_sections = raw.get("allowed_sections", []) or []
    columns_cfg = raw.get("columns", {}) or {}

    flattened = {
        # gcp.* in your YAML
        "gcp_project_id": raw.get("gcp_project_id") or gcp_cfg.get("project_id"),
        "bq_dataset_id": raw.get("bq_dataset_id") or gcp_cfg.get("dataset"),
        "bq_location": raw.get("bq_location") or gcp_cfg.get("location", "asia-southeast1"),

        "table_names": tables_cfg,
        "allowed_sections": allowed_sections,
        "default_ordering": ordering_cfg,
        "default_limit_single_row": limit_single_row,
        "columns": columns_cfg,
    }

    return AppSettings(**flattened)
