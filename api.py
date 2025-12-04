# api.py
#
# FastAPI entrypoint for the E-portfolio Data API (Data Gathering layer).
#
# Responsibility:
# - Expose HTTP GET endpoints to read student profile data and
#   role / JD / template taxonomy from BigQuery (via repository classes).
# - Provide simple "hydrated" objects by delegating to the internal
#   data-gathering orchestrator.
#
# Deployment model:
# - Packaged in Docker and deployed to Cloud Run.
# - Typically called by a separate Orchestrator / CV Generation service.
#

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from repositories.student_repo import StudentRepository
from repositories.role_repo import RoleRepository
from functions.orchestrator.eport_data_gathering_orchestrator import (
    hydrate_student_profile,
    hydrate_role_taxonomy,
    hydrate_jd_taxonomy,
    get_template_info,
)

app = FastAPI(
    title="E-portfolio Data API",
    version="0.1.0",
    description="Data access layer for student profiles, role/JD taxonomy, and templates.",
)

# Instantiate repositories once (simple pattern; can later swap to DI if needed)
student_repo = StudentRepository()
role_repo = RoleRepository()


# ------------ System endpoints ------------


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Basic health check endpoint for uptime monitoring."""
    return {"status": "ok"}


# ------------ Student endpoints ------------


@app.get("/v1/students/{user_id}/core", tags=["students"])
async def get_student_core(user_id: str) -> dict:
    """
    Return core student row from the `student` table.

    This is a thin wrapper over StudentRepository.get_student_core and is useful
    for debugging or when the caller wants raw table data instead of the fully
    hydrated profile.
    """
    core = student_repo.get_student_core(user_id)
    if not core:
        raise HTTPException(status_code=404, detail="Student not found")
    return core


@app.get("/v1/students/{user_id}/full-profile", tags=["students"])
async def get_full_student_profile(user_id: str) -> dict:
    """
    Return a hydrated student_profile object.

    Combines data from multiple tables:
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
    try:
        profile = await hydrate_student_profile(user_id)
    except ValueError as e:
        # Orchestrator uses ValueError when core student row is missing
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "user_id": user_id,
        "student_profile": profile,
    }


# ------------ Role taxonomy endpoints ------------


@app.get("/v1/roles/{role_id}/core", tags=["roles"])
async def get_role_core(role_id: str) -> dict:
    """
    Return basic role taxonomy record plus required skills.

    This endpoint gives raw table-shaped data:
    - role_taxonomy_roles
    - role_taxonomy_required_skills
    """
    role = role_repo.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    skills = role_repo.get_role_required_skills(role_id)
    return {
        "role": role,
        "required_skills": skills,
    }


@app.get("/v1/roles/{role_id}/taxonomy", tags=["roles"])
async def get_role_taxonomy(role_id: str) -> dict:
    """
    Return normalized target_role_taxonomy object.

    This is the preferred endpoint for the external Orchestrator service.
    """
    taxonomy = hydrate_role_taxonomy(role_id)
    if taxonomy is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return taxonomy


# ------------ JD taxonomy endpoints ------------

@app.get("/v1/jds/{jd_id}/core", tags=["jds"])
async def get_jd_core(jd_id: str) -> dict:
    """Return raw JD taxonomy row from jd_taxonomy table."""
    jd = role_repo.get_jd(jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="JD not found")
    return jd


@app.get("/v1/jds/{jd_id}/taxonomy", tags=["jds"])
async def get_jd_taxonomy(jd_id: str) -> dict:
    """
    Return hydrated JD taxonomy:
    - job title, company, industry
    - required skills
    - responsibilities
    """
    taxonomy = hydrate_jd_taxonomy(jd_id)
    if taxonomy is None:
        raise HTTPException(status_code=404, detail="JD not found")
    return taxonomy


# ------------ Template endpoints ------------

@app.get("/v1/templates/{template_id}", tags=["templates"])
async def get_template(template_id: str) -> dict:
    """Return template_info record used by the CV generation service."""
    template = get_template_info(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
