# functions/orchestrator/eport_data_gathering_orchestrator.py
#
# E-portfolio Data-Gathering Orchestrator.
#
# Responsibility:
# - Aggregate data from student / role / JD / template repositories
#   into hydrated objects for the external Orchestrator / CV engine.
# - Keep all BigQuery details hidden behind repository classes.
#

from __future__ import annotations

from typing import Any, Dict, Optional

from repositories.student_repo import StudentRepository
from repositories.role_repo import RoleRepository

__all__ = [
    "hydrate_student_profile",
    "hydrate_role_taxonomy",
    "hydrate_jd_taxonomy",
    "get_template_info",
    # async variants (for Option A1 parallelization)
    "ahydrate_role_taxonomy",
    "ahydrate_jd_taxonomy",
    "aget_template_info",
]

# Global, lightweight singletons (can be swapped to DI later if needed)
_student_repo = StudentRepository()
_role_repo = RoleRepository()


# ---------------- Student aggregation ----------------


async def hydrate_student_profile(user_id: str) -> Dict[str, Any]:
    """
    Aggregate all student-related tables into a single profile dict.

    Uses a single nested BigQuery query (Option B) via
    StudentRepository.get_student_full_profile_nested(), which returns:

    - Core student columns (s.*)
    - Nested arrays for:
        education, experience, skills, awards,
        extracurriculars, publications, training,
        references, additional_info

    Missing data in child tables is safe: BigQuery returns [] for each ARRAY.
    """
    row = _student_repo.get_student_full_profile_nested(user_id)

    if row is None:
        # Explicit error so API layer can convert to 404.
        raise ValueError(f"No student core record found for user_id={user_id}")

    # Keys that are nested arrays (we don't want them in personal_info)
    array_keys = {
        "education",
        "experience",
        "skills",
        "awards",
        "extracurriculars",
        "publications",
        "training",
        "references",
        "additional_info",
    }

    # Everything else is treated as core student info (previously get_student_core)
    personal_info = {k: v for k, v in row.items() if k not in array_keys}

    return {
        "personal_info": personal_info,
        "education": row.get("education", []) or [],
        "experience": row.get("experience", []) or [],
        "skills": row.get("skills", []) or [],
        "awards": row.get("awards", []) or [],
        "extracurriculars": row.get("extracurriculars", []) or [],
        "publications": row.get("publications", []) or [],
        "training": row.get("training", []) or [],
        "references": row.get("references", []) or [],
        "additional_info": row.get("additional_info", []) or [],
    }


# ---------------- Role taxonomy aggregation (sync) ----------------


def hydrate_role_taxonomy(role_id: str) -> Optional[Dict[str, Any]]:
    """
    Aggregate role + required skills into a target_role_taxonomy-like dict.

    Uses:
    - role_taxonomy_roles
    - role_taxonomy_required_skills
    """
    role = _role_repo.get_role(role_id)
    if role is None:
        return None

    required_skills = _role_repo.get_role_required_skills(role_id)

    return {
        "role_id": role_id,
        "role_title": role.get("role_title"),
        "role_description": role.get("role_description"),
        "role_required_skills": required_skills,
    }


# ---------------- JD taxonomy aggregation (sync) ----------------


def hydrate_jd_taxonomy(jd_id: str) -> Optional[Dict[str, Any]]:
    """
    Aggregate JD core info + required skills + responsibilities into
    a target_jd_taxonomy-like dict.

    Uses:
    - jd_taxonomy
    - jd_taxonomy_required_skills
    - jd_taxonomy_responsibilities
    """
    jd = _role_repo.get_jd(jd_id)
    if jd is None:
        return None

    skills = _role_repo.get_jd_required_skills(jd_id)
    responsibilities = _role_repo.get_jd_responsibilities(jd_id)

    return {
        "jd_id": jd_id,
        "job_title": jd.get("job_title"),
        "company_name": jd.get("company_name"),
        "company_industry": jd.get("company_industry"),
        "job_required_skills": skills,
        "job_responsibilities": responsibilities,
    }


# ---------------- Template lookup (sync) ----------------


def get_template_info(template_id: str) -> Optional[Dict[str, Any]]:
    """
    Thin wrapper to fetch template_info record.

    Shape should match what the CV generation service expects:
    - template_id
    - template_name
    - style
    - font_family
    - color_scheme
    - section_limits / character limits
    """
    return _role_repo.get_template_info(template_id)


# ---------------- Async variants for Option A1 ----------------


async def ahydrate_role_taxonomy(role_id: str) -> Optional[Dict[str, Any]]:
    """
    Async version of hydrate_role_taxonomy, using RoleRepository async methods.

    Intended for use with asyncio.gather alongside other async calls.
    """
    role = await _role_repo.aget_role(role_id)
    if role is None:
        return None

    required_skills = await _role_repo.aget_role_required_skills(role_id)

    return {
        "role_id": role_id,
        "role_title": role.get("role_title"),
        "role_description": role.get("role_description"),
        "role_required_skills": required_skills,
    }


async def ahydrate_jd_taxonomy(jd_id: str) -> Optional[Dict[str, Any]]:
    """
    Async version of hydrate_jd_taxonomy, using RoleRepository async methods.
    """
    jd = await _role_repo.aget_jd(jd_id)
    if jd is None:
        return None

    skills = await _role_repo.aget_jd_required_skills(jd_id)
    responsibilities = await _role_repo.aget_jd_responsibilities(jd_id)

    return {
        "jd_id": jd_id,
        "job_title": jd.get("job_title"),
        "company_name": jd.get("company_name"),
        "company_industry": jd.get("company_industry"),
        "job_required_skills": skills,
        "job_responsibilities": responsibilities,
    }


async def aget_template_info(template_id: str) -> Optional[Dict[str, Any]]:
    """
    Async version of get_template_info, using RoleRepository async methods.
    """
    return await _role_repo.aget_template_info(template_id)
