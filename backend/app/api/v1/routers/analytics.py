"""Read-only analytics routes for the KARNA API."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.correction_repository import CorrectionRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.outcome_repository import OutcomeRepository
from app.services.analytics_service import AnalyticsService, FixPerformance

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class AnalyticsSummaryResponse(BaseModel):
    """Dashboard summary returned by the analytics endpoint."""

    total_incidents: int = Field(ge=0, description="Total stored incidents.")
    resolved_incidents: int = Field(
        ge=0,
        description="Incidents with at least one successful outcome.",
    )
    corrections: int = Field(ge=0, description="Engineer correction count.")
    memory_records: int = Field(ge=0, description="Retrievable memory record count.")
    learning_improvement: float = Field(
        ge=0,
        le=100,
        description="Percentage of recorded outcomes that are successful.",
    )


class TopFixResponse(BaseModel):
    """Top-fix performance entry returned by analytics."""

    fix: str = Field(description="Applied remediation action.")
    success_rate: float = Field(
        ge=0,
        le=1,
        description="Historical success rate for this action.",
    )


def get_analytics_service(
    database_session: Session = Depends(get_db),
) -> AnalyticsService:
    """Build a read-only analytics service from request-scoped repositories.

    Args:
        database_session: Request-scoped SQLAlchemy session supplied by FastAPI.

    Returns:
        Analytics service configured with repository dependencies.
    """
    return AnalyticsService(
        incident_repository=IncidentRepository(database_session),
        outcome_repository=OutcomeRepository(database_session),
        correction_repository=CorrectionRepository(database_session),
        memory_repository=MemoryRepository(database_session),
    )


@router.get("/summary", response_model=AnalyticsSummaryResponse, summary="Get analytics summary")
def get_analytics_summary(
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummaryResponse:
    """Return the primary dashboard learning metrics.

    Args:
        service: Injected read-only analytics service.

    Returns:
        Aggregate incident, correction, memory, and learning metrics.
    """
    snapshot = service.get_dashboard_metrics()
    return AnalyticsSummaryResponse(
        total_incidents=snapshot.total_incidents,
        resolved_incidents=snapshot.resolved_incidents,
        corrections=snapshot.corrections_count,
        memory_records=snapshot.memory_count,
        learning_improvement=snapshot.learning_improvement,
    )


@router.get(
    "/top-fixes",
    response_model=list[TopFixResponse],
    summary="Get top outcome-backed fixes",
)
def get_top_fixes(
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[TopFixResponse]:
    """Return fixes ordered by historical success evidence.

    Args:
        service: Injected read-only analytics service.

    Returns:
        Outcome-aware fix performance entries.
    """
    performances: list[FixPerformance] = service.get_success_rates()
    return [
        TopFixResponse(fix=performance.fix, success_rate=performance.success_rate)
        for performance in performances
    ]
