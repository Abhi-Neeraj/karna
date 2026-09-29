"""Health endpoint for the KARNA API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Public service-health response."""

    status: str = Field(description="Current API health state.", examples=["healthy"])
    service: str = Field(description="Stable service identifier.", examples=["karna"])
    version: str = Field(description="Running API version.", examples=["1.0.0"])


@router.get("", response_model=HealthResponse, summary="Check API health")
def get_health() -> HealthResponse:
    """Return the API's lightweight liveness status.

    Returns:
        A static response confirming that the KARNA API is available.
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name.casefold(),
        version=settings.app_version,
    )
