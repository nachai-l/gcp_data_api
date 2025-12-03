"""
functions/models/external_api.py

Pydantic models for the external E-portfolio / CV Orchestrator API.

These models define:
- Request/response schemas used by the external API layer
- Field-level validation and defaults
- Typed containers that will later be mapped to internal CV engine schemas

They are imported and used by the FastAPI app in `api.py` (and related routers)
to validate incoming JSON payloads and to provide OpenAPI schema documentation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional


class ClientMetadata(BaseModel):
    channel: str = Field(..., description="Client channel, e.g. web or mobile")
    locale: Optional[str] = Field(None, description="BCP-47 locale, e.g. th-TH")
    app_version: Optional[str] = Field(None)


class GenerateCVRequest(BaseModel):
    request_id: Optional[str] = Field(
        None, description="Optional client-side correlation ID"
    )
    user_id: str = Field(..., min_length=1)

    language: str = Field("en")
    language_tone: str = Field("formal")

    template_id: str
    sections: List[str]

    target_role_id: Optional[str] = None
    target_jd_id: Optional[str] = None

    user_input_cv_text_by_section: Dict[str, str] = Field(default_factory=dict)
    comments_by_section: Dict[str, str] = Field(default_factory=dict)

    client_metadata: Optional[ClientMetadata] = None

    @field_validator("sections")
    @classmethod
    def validate_sections(cls, v: List[str]) -> List[str]:
        allowed = {
            "profile_summary",
            "skills",
            "education",
            "experience",
            "projects",
            "activities",
            "awards",
            "training",
            "publications",
            "extracurriculars",
            "references",
            "additional_info",
        }
        deduped = []
        for s in v:
            if s not in allowed:
                raise ValueError(f"Unsupported section: {s}")
            if s not in deduped:
                deduped.append(s)
        return deduped
