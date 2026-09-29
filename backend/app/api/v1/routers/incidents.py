"""Incident-analysis routes for the KARNA API."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.services.incident_analysis_service import IncidentAnalysisService

router = APIRouter(prefix="/incidents", tags=["Incidents"])


class IncidentAnalysisPayload(BaseModel):
    """API payload describing an incident to analyze."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Concise incident title.",
        examples=["Database Connection Pool Exhausted"],
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=10_000,
        description="Detailed incident symptoms and context.",
        examples=["Checkout requests fail because the database pool is exhausted."],
    )
    logs: str | None = Field(
        default=None,
        max_length=50_000,
        description="Optional relevant log excerpt.",
        examples=["TimeoutError: connection pool exhausted"],
    )


class IncidentAnalysisResponse(BaseModel):
    """Normalized incident context returned to the API client."""

    summary: str = Field(description="Concise normalized incident summary.")
    category: str = Field(description="Detected incident category.")
    symptoms: list[str] = Field(description="Detected symptom cues.")
    keywords: list[str] = Field(description="Normalized retrieval keywords.")
    technologies: list[str] = Field(description="Detected technology cues.")


def get_incident_analysis_service() -> IncidentAnalysisService:
    """Provide the stateless deterministic analysis service.

    Returns:
        A service instance for a single incident analysis operation.
    """
    return IncidentAnalysisService()


@router.post(
    "/analyze",
    response_model=IncidentAnalysisResponse,
    summary="Analyze incident context",
)
def analyze_incident(
    payload: IncidentAnalysisPayload,
    service: IncidentAnalysisService = Depends(get_incident_analysis_service),
) -> IncidentAnalysisResponse:
    """Extract normalized context from an incoming incident report.

    Args:
        payload: Validated incident title, description, and optional logs.
        service: Injected deterministic incident-analysis service.

    Returns:
        Normalized symptoms, technologies, keywords, category, and summary.
    """
    analysis = service.analyze(
        title=payload.title,
        description=payload.description,
        logs=payload.logs,
    )
    return IncidentAnalysisResponse(
        summary=analysis.summary,
        category=analysis.category,
        symptoms=analysis.symptoms,
        keywords=analysis.keywords,
        technologies=analysis.technologies,
    )
