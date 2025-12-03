# functions/utils/config_loader.py
#
# Central configuration loader for eport_data_api.
# Loads parameters/config.yaml and exposes project-wide settings.
#
# Used by: repositories, BigQuery client, orchestrator, API.

from __future__ import annotations

import yaml
from pathlib import Path
from functools import lru_cache
from pydantic import BaseModel


class AppSettings(BaseModel):
    gcp_project_id: str
    bq_dataset: str
    tables: dict
    columns: dict


@lru_cache()
def get_settings() -> AppSettings:
    """Load parameters/config.yaml and return AppSettings."""
    config_path = (
        Path(__file__).resolve().parent.parent.parent
        / "parameters"
        / "config.yaml"
    )

    if not config_path.exists():
        raise FileNotFoundError(f"Missing config.yaml at: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return AppSettings(**raw)
