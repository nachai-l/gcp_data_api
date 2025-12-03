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
]

# Global, lightweight singletons (can be swapped to DI later if needed)
_student_repo = StudentRepository()
_role_repo = RoleRepository()


# ---------------- Student aggregation ----------------


def hydrate_student_profile(user_id: str) -> Dict[str, Any]:
    """
    Aggregate all student-related tables into a single profile dict.

    Pulls from:
    - student
    - education
    - experience
    - skills
    - awards
    - extracurriculars
    - publications
    - training
    - references
    - additional_info
    """
    core = _student_repo.get_student_core(user_id)

    if core is None:
        # Explicit error so API layer can convert to 404.
        raise ValueError(f"No student core record found for user_id={user_id}")

    education = _student_repo.get_student_education(user_id)
    experience = _student_repo.get_student_experience(user_id)
    skills = _student_repo.get_student_skills(user_id)
    awards = _student_repo.get_student_awards(user_id)
    extracurriculars = _student_repo.get_student_extracurriculars(user_id)
    publications = _student_repo.get_student_publications(user_id)
    training = _student_repo.get_student_training(user_id)
    references = _student_repo.get_student_references(user_id)
    additional_info = _student_repo.get_student_additional_info(user_id)

    return {
        "personal_info": core,
        "education": education,
        "experience": experience,
        "skills": skills,
        "awards": awards,
        "extracurriculars": extracurriculars,
        "publications": publications,
        "training": training,
        "references": references,
        "additional_info": additional_info,
    }


# ---------------- Role taxonomy aggregation ----------------


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


# ---------------- JD taxonomy aggregation ----------------


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


# ---------------- Template lookup ----------------


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
