"""Memory-backed recommendation routes for the KARNA API."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.memory.sqlite_memory_provider import SQLiteMemoryProvider
from app.repositories.memory_repository import MemoryRepository
from app.repositories.outcome_repository import OutcomeRepository
from app.services.incident_analysis_service import IncidentAnalysisService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


class RecommendationPayload(BaseModel):
    """API payload for a generic or memory-backed recommendation request."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10, max_length=10_000)
    logs: str | None = Field(default=None, max_length=50_000)
    memory_enabled: bool = Field(
        default=True,
        description="Whether historical operational memory may influence guidance.",
    )


class RecommendedFixResponse(BaseModel):
    """One ranked fix returned by the recommendation endpoint."""

    fix: str = Field(description="Recommended remediation action.")
    success_rate: float = Field(ge=0, le=1, description="Historical fix success rate.")
    success_count: int = Field(ge=0, description="Recorded successful outcomes.")
    failure_count: int = Field(ge=0, description="Recorded failed outcomes.")
    memory_similarity: float = Field(
        ge=0,
        le=1,
        description="Similarity of supporting incident memories.",
    )
    recommendation_score: float = Field(
        ge=0,
        le=1,
        description="Outcome-and-memory score used for ranking.",
    )
    confidence_score: float = Field(
        ge=0,
        le=100,
        description="Evidence-derived confidence.",
    )


class RecommendationResponse(BaseModel):
    """Recommendation endpoint response."""

    recommendations: list[RecommendedFixResponse] = Field(
        description="Fixes ranked using the selected memory mode."
    )


def get_recommendation_service(
    database_session: Session = Depends(get_db),
) -> RecommendationService:
    """Build a recommendation service with the active SQLite memory provider.

    Args:
        database_session: Request-scoped SQLAlchemy session supplied by FastAPI.

    Returns:
        A service configured with repository-backed memory and outcome access.
    """
    memory_repository = MemoryRepository(database_session)
    memory_provider = SQLiteMemoryProvider(memory_repository)
    outcome_repository = OutcomeRepository(database_session)
    return RecommendationService(memory_provider, outcome_repository)


def get_incident_analysis_service() -> IncidentAnalysisService:
    """Provide the stateless incident-context analysis dependency.

    Returns:
        A deterministic incident-analysis service instance.
    """
    return IncidentAnalysisService()


@router.post("", response_model=RecommendationResponse, summary="Get fix recommendations")
def get_recommendations(
    payload: RecommendationPayload,
    service: RecommendationService = Depends(get_recommendation_service),
    analysis_service: IncidentAnalysisService = Depends(get_incident_analysis_service),
) -> RecommendationResponse:
    """Return generic or historical outcome-backed fix recommendations.

    Args:
        payload: Incident context and the selected memory mode.
        service: Injected recommendation service.
        analysis_service: Injected incident-context analysis service.

    Returns:
        Ranked recommendations suitable for the incident response workspace.
    """
    analysis = analysis_service.analyze(
        title=payload.title,
        description=payload.description,
        logs=payload.logs,
    )
    result = service.generate_recommendations(
        query=analysis.summary,
        keywords=analysis.keywords,
        memory_enabled=payload.memory_enabled,
    )
    return RecommendationResponse(
        recommendations=[
            RecommendedFixResponse(
                fix=recommendation.fix,
                success_rate=recommendation.success_rate,
                success_count=recommendation.success_count,
                failure_count=recommendation.failure_count,
                memory_similarity=recommendation.memory_similarity,
                recommendation_score=recommendation.recommendation_score,
                confidence_score=recommendation.confidence_score,
            )
            for recommendation in result.recommendations
        ]
    )
