# repositories/role_repo.py
#
# Data-access layer for role / JD / template taxonomy tables in BigQuery.
# Hides raw SQL details behind simple Python methods.

from __future__ import annotations

from typing import Any, Dict, List, Optional

from database.bigquery_client import run_query, async_run_query
from functions.utils.settings import get_settings


class RoleRepository:
    """Repository for role_taxonomy, jd_taxonomy, and template_info tables."""

    def __init__(self) -> None:
        settings = get_settings()

        self.project_id = settings.gcp_project_id
        self.dataset_id = settings.bq_dataset_id
        self.location = settings.bq_location

        tables = settings.table_names

        # Fully-qualified table names
        self.tables: Dict[str, str] = {
            "roles": f"{self.project_id}.{self.dataset_id}.{tables['role_taxonomy_roles']}",
            "role_required_skills": (
                f"{self.project_id}.{self.dataset_id}.{tables['role_taxonomy_required_skills']}"
            ),
            "jds": f"{self.project_id}.{self.dataset_id}.{tables['jd_taxonomy']}",
            "jd_required_skills": (
                f"{self.project_id}.{self.dataset_id}.{tables['jd_taxonomy_required_skills']}"
            ),
            "jd_responsibilities": (
                f"{self.project_id}.{self.dataset_id}.{tables['jd_taxonomy_responsibilities']}"
            ),
            # 🔥 templates
            "template_info": (
                f"{self.project_id}.{self.dataset_id}.{tables['template_info']}"
            ),
        }

    # ---------- Role taxonomy (sync) ----------

    def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Return single role_taxonomy_roles row, or None if not found."""
        table = self.tables["roles"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE role_id = "{role_id}"
        LIMIT 1
        """
        rows = run_query(sql)
        return rows[0] if rows else None

    def get_role_required_skills(self, role_id: str) -> List[Dict[str, Any]]:
        """Return all required skills for a given role_id."""
        table = self.tables["role_required_skills"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE role_id = "{role_id}"
        ORDER BY skill_id
        """
        return run_query(sql)

    # ---------- JD taxonomy (sync) ----------

    def get_jd(self, jd_id: str) -> Optional[Dict[str, Any]]:
        """Return single jd_taxonomy row, or None if not found."""
        table = self.tables["jds"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE jd_id = "{jd_id}"
        LIMIT 1
        """
        rows = run_query(sql)
        return rows[0] if rows else None

    def get_jd_required_skills(self, jd_id: str) -> List[Dict[str, Any]]:
        """Return all required skills for a given JD."""
        table = self.tables["jd_required_skills"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE jd_id = "{jd_id}"
        ORDER BY skill_id
        """
        return run_query(sql)

    def get_jd_responsibilities(self, jd_id: str) -> List[Dict[str, Any]]:
        """Return ordered responsibilities for a JD."""
        table = self.tables["jd_responsibilities"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE jd_id = "{jd_id}"
        ORDER BY responsibility_index
        """
        return run_query(sql)

    # ---------- Templates (sync) ----------

    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Return single template_info row, or None if not found.

        Expected columns (from CSV):
        - template_id
        - name
        - style
        - font_family
        - color_scheme
        - max_chars_per_section
        - max_pages
        """
        table = self.tables["template_info"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE template_id = "{template_id}"
        LIMIT 1
        """
        rows = run_query(sql)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Async counterparts (for Option A1 parallelization)
    # ------------------------------------------------------------------

    async def aget_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Async version of get_role, suitable for asyncio.gather."""
        table = self.tables["roles"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE role_id = "{role_id}"
        LIMIT 1
        """
        rows = await async_run_query(sql)
        return rows[0] if rows else None

    async def aget_role_required_skills(self, role_id: str) -> List[Dict[str, Any]]:
        """Async version of get_role_required_skills."""
        table = self.tables["role_required_skills"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE role_id = "{role_id}"
        ORDER BY skill_id
        """
        return await async_run_query(sql)

    async def aget_jd(self, jd_id: str) -> Optional[Dict[str, Any]]:
        """Async version of get_jd."""
        table = self.tables["jds"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE jd_id = "{jd_id}"
        LIMIT 1
        """
        rows = await async_run_query(sql)
        return rows[0] if rows else None

    async def aget_jd_required_skills(self, jd_id: str) -> List[Dict[str, Any]]:
        """Async version of get_jd_required_skills."""
        table = self.tables["jd_required_skills"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE jd_id = "{jd_id}"
        ORDER BY skill_id
        """
        return await async_run_query(sql)

    async def aget_jd_responsibilities(self, jd_id: str) -> List[Dict[str, Any]]:
        """Async version of get_jd_responsibilities."""
        table = self.tables["jd_responsibilities"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE jd_id = "{jd_id}"
        ORDER BY responsibility_index
        """
        return await async_run_query(sql)

    async def aget_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Async version of get_template_info."""
        table = self.tables["template_info"]
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE template_id = "{template_id}"
        LIMIT 1
        """
        rows = await async_run_query(sql)
        return rows[0] if rows else None
