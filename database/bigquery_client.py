# database/bigquery_client.py
#
# Thin BigQuery client wrapper.
# Now includes async_run_query() for parallel repo calls.
# Uses settings from parameters/config.yaml via get_settings().

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, Dict, List, Optional

from google.cloud import bigquery

from functions.utils.settings import get_settings


# ---------------------------------------------------------------------------
# Client Singleton
# ---------------------------------------------------------------------------

@lru_cache()
def get_bigquery_client() -> bigquery.Client:
    """Return a singleton BigQuery client configured with project & location."""
    settings = get_settings()
    return bigquery.Client(
        project=settings.gcp_project_id,
        location=settings.bq_location,
    )


# ---------------------------------------------------------------------------
# Synchronous Query (used by Option B – nested student query)
# ---------------------------------------------------------------------------

def run_query(
    sql: str,
    job_config: Optional[bigquery.job.QueryJobConfig] = None
) -> List[Dict[str, Any]]:
    """Execute SQL synchronously and return list[dict]."""
    client = get_bigquery_client()
    query_job = client.query(sql, job_config=job_config)
    rows = query_job.result()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Async Wrapper (used by Option A1 – parallel repo calls)
# ---------------------------------------------------------------------------

async def async_run_query(
    sql: str,
    job_config: Optional[bigquery.job.QueryJobConfig] = None
) -> List[Dict[str, Any]]:
    """
    Execute SQL using a thread so that multiple queries can be run in parallel.
    """
    loop = asyncio.get_running_loop()

    def _run():
        return run_query(sql, job_config)

    return await loop.run_in_executor(None, _run)
