# cv_orchestrator/data_fetcher.py

import asyncio
import os
import httpx


# Load from environment; default to local during development
DATA_API_URL = os.getenv("DATA_API_URL", "http://localhost:8001")


async def fetch_all_data(user_id: str, role_id: str, jd_id: str, template_id: str):
    """
    Fetch student profile, role taxonomy, JD taxonomy, and template info
    concurrently from the Data API.

    Uses httpx.AsyncClient and asyncio.gather for performance.
    """

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            student_fut = client.get(f"{DATA_API_URL}/v1/students/{user_id}/full-profile")
            role_fut = client.get(f"{DATA_API_URL}/v1/roles/{role_id}/taxonomy")
            jd_fut = client.get(f"{DATA_API_URL}/v1/jds/{jd_id}/taxonomy")
            template_fut = client.get(f"{DATA_API_URL}/v1/templates/{template_id}")

            # Run 4 requests concurrently
            (
                student_resp,
                role_resp,
                jd_resp,
                template_resp,
            ) = await asyncio.gather(
                student_fut,
                role_fut,
                jd_fut,
                template_fut,
            )

            # Raise for any HTTP error (404, 500, etc.)
            student_resp.raise_for_status()
            role_resp.raise_for_status()
            jd_resp.raise_for_status()
            template_resp.raise_for_status()

            # Decode JSON
            student = student_resp.json()
            role = role_resp.json()
            jd = jd_resp.json()
            template = template_resp.json()

            return {
                "student_profile": student["student_profile"],
                "role_taxonomy": role,
                "jd_taxonomy": jd,
                "template_info": template,
            }

        except httpx.HTTPStatusError as e:
            # Clean error that shows which call failed
            raise RuntimeError(
                f"Data API returned {e.response.status_code} for {e.request.url}"
            ) from e

        except httpx.RequestError as e:
            raise RuntimeError(
                f"Network error calling Data API: {str(e)}"
            ) from e
