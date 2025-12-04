# repositories/student_repo.py
#
# Data access layer for student-related tables.

from __future__ import annotations

from typing import Any, Dict, List, Optional

from database.bigquery_client import run_query
from functions.utils.settings import get_settings


class StudentRepository:
    def __init__(self) -> None:
        self.settings = get_settings()
        t = self.settings.table_names
        cols = self.settings.columns
        ordering = self.settings.default_ordering

        self.user_col = cols["key_user_id"]

        self.tbl_student = t["student"]
        self.tbl_education = t["education"]
        self.tbl_experience = t["experience"]
        self.tbl_awards = t["awards"]
        self.tbl_extracurriculars = t["extracurriculars"]
        self.tbl_skills = t["skills"]
        self.tbl_publications = t["publications"]
        self.tbl_references = t["references"]
        self.tbl_training = t["training"]
        self.tbl_additional_info = t["additional_info"]

        self.order_education = ordering.get("education", "")
        self.order_experience = ordering.get("experience", "")

    # ---- helpers ----

    def _select_many(self, table: str, where: str = "") -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"SELECT * FROM `{self.settings.gcp_project_id}.{dataset}.{table}`"
        if where:
            sql += f" WHERE {where}"
        return run_query(sql)

    def _select_by_user(self, table: str, extra: str = "") -> List[Dict[str, Any]]:
        # NOTE: This helper is currently unused; left as-is to avoid breaking callers.
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{table}`
            WHERE {self.user_col} = '{self._user_id}'
        """
        return run_query(sql)

    # ---- public methods used by orchestrator (existing) ----

    def get_student_core(self, user_id: str) -> Optional[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_student}`
            WHERE {self.user_col} = '{user_id}'
            LIMIT {self.settings.default_limit_single_row}
        """
        rows = run_query(sql)
        return rows[0] if rows else None

    def get_student_education(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_education}`
            WHERE {self.user_col} = '{user_id}'
            {self.order_education}
        """
        return run_query(sql)

    def get_student_experience(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_experience}`
            WHERE {self.user_col} = '{user_id}'
            {self.order_experience}
        """
        return run_query(sql)

    def get_student_skills(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_skills}`
            WHERE {self.user_col} = '{user_id}'
        """
        return run_query(sql)

    def get_student_awards(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_awards}`
            WHERE {self.user_col} = '{user_id}'
        """
        return run_query(sql)

    def get_student_extracurriculars(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_extracurriculars}`
            WHERE {self.user_col} = '{user_id}'
        """
        return run_query(sql)

    def get_student_publications(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_publications}`
            WHERE {self.user_col} = '{user_id}'
        """
        return run_query(sql)

    def get_student_training(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_training}`
            WHERE {self.user_col} = '{user_id}'
        """
        return run_query(sql)

    def get_student_references(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_references}`
            WHERE {self.user_col} = '{user_id}'
        """
        return run_query(sql)

    def get_student_additional_info(self, user_id: str) -> List[Dict[str, Any]]:
        dataset = self.settings.bq_dataset_id
        sql = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{dataset}.{self.tbl_additional_info}`
            WHERE {self.user_col} = '{user_id}'
        """
        return run_query(sql)

    # ---- NEW: Single nested-query for full student profile (Option B) ----

    def get_student_full_profile_nested(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a student's full profile (core + all child tables) using a single
        BigQuery query with ARRAY(...) sub-selects.

        - Missing data in child tables is safe: BigQuery returns [] (empty array).
        - Returns None if the student core row is not found.
        """
        dataset = self.settings.bq_dataset_id
        project = self.settings.gcp_project_id

        # These will typically be like "ORDER BY end_date DESC" or empty string.
        order_edu = self.order_education or ""
        order_exp = self.order_experience or ""

        sql = f"""
            SELECT
              s.*,

              -- Education
              ARRAY(
                SELECT AS STRUCT e.*
                FROM `{project}.{dataset}.{self.tbl_education}` e
                WHERE e.{self.user_col} = '{user_id}'
                {order_edu}
              ) AS education,

              -- Experience
              ARRAY(
                SELECT AS STRUCT ex.*
                FROM `{project}.{dataset}.{self.tbl_experience}` ex
                WHERE ex.{self.user_col} = '{user_id}'
                {order_exp}
              ) AS experience,

              -- Skills
              ARRAY(
                SELECT AS STRUCT sk.*
                FROM `{project}.{dataset}.{self.tbl_skills}` sk
                WHERE sk.{self.user_col} = '{user_id}'
              ) AS skills,

              -- Awards
              ARRAY(
                SELECT AS STRUCT a.*
                FROM `{project}.{dataset}.{self.tbl_awards}` a
                WHERE a.{self.user_col} = '{user_id}'
              ) AS awards,

              -- Extracurriculars
              ARRAY(
                SELECT AS STRUCT exu.*
                FROM `{project}.{dataset}.{self.tbl_extracurriculars}` exu
                WHERE exu.{self.user_col} = '{user_id}'
              ) AS extracurriculars,

              -- Publications
              ARRAY(
                SELECT AS STRUCT p.*
                FROM `{project}.{dataset}.{self.tbl_publications}` p
                WHERE p.{self.user_col} = '{user_id}'
              ) AS publications,

              -- Training
              ARRAY(
                SELECT AS STRUCT tr.*
                FROM `{project}.{dataset}.{self.tbl_training}` tr
                WHERE tr.{self.user_col} = '{user_id}'
              ) AS training,

              -- References
              ARRAY(
                SELECT AS STRUCT r.*
                FROM `{project}.{dataset}.{self.tbl_references}` r
                WHERE r.{self.user_col} = '{user_id}'
              ) AS references,

              -- Additional Info
              ARRAY(
                SELECT AS STRUCT ai.*
                FROM `{project}.{dataset}.{self.tbl_additional_info}` ai
                WHERE ai.{self.user_col} = '{user_id}'
              ) AS additional_info

            FROM `{project}.{dataset}.{self.tbl_student}` AS s
            WHERE s.{self.user_col} = '{user_id}'
            LIMIT {self.settings.default_limit_single_row}
        """

        rows = run_query(sql)
        return rows[0] if rows else None
