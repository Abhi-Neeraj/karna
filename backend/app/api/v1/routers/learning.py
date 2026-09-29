"""Learning-loop routes for outcome and correction feedback."""

from collections.abc import Generator
from typing import Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.memory.sqlite_memory_provider import SQLiteMemoryProvider
from app.repositories.correction_repository import CorrectionRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.outcome_repository import OutcomeRepository
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["Learning"])


class OutcomeLearningPayload(BaseModel):
    """API payload recording an applied-fix outcome."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    incident_id: int = Field(..., gt=0, description="Source incident identifier.")
    recommendation_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Optional client correlation ID. Recommendation persistence is not "
            "part of the current data model."
        ),
    )
    fix_applied: str = Field(
        ...,
        min_length=3,
        max_length=10_000,
        description="Actual remediation action applied by the engineer.",
    )
    successful: bool = Field(
        default=False,
        description="Backward-compatible full-success flag.",
    )
    outcome_status: Literal["worked", "failed", "partial_success"] | None = Field(
        default=None,
        description="Observed remediation result; partial success is retained in notes.",
    )
    notes: str | None = Field(
        default=None,
        max_length=10_000,
        description="Optional observations about the applied fix.",
    )


class CorrectionLearningPayload(BaseModel):
    """API payload recording an engineer root-cause correction."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    incident_id: int = Field(..., gt=0, description="Corrected incident identifier.")
    previous_diagnosis: str | None = Field(
        default=None,
        max_length=10_000,
        description="Prior root-cause assessment, if one existed.",
    )
    correct_diagnosis: str = Field(
        ...,
        min_length=3,
        max_length=10_000,
        description="Engineer-validated root cause.",
    )
    explanation: str = Field(
        ...,
        min_length=3,
        max_length=10_000,
        description="Evidence supporting the corrected diagnosis.",
    )


class LearningResponse(BaseModel):
    """Confirmation returned after a learning event is committed."""

    id: int = Field(gt=0, description="Stored outcome or correction identifier.")
    incident_id: int = Field(gt=0, description="Associated incident identifier.")
    message: str = Field(description="Human-readable learning confirmation.")


def get_learning_service(
    database_session: Session = Depends(get_db),
) -> Generator[LearningService, None, None]:
    """Provide a transactional learning service for one request.

    Args:
        database_session: Request-scoped SQLAlchemy session supplied by FastAPI.

    Yields:
        A learning service whose complete feedback event is committed on success.
    """
    memory_repository = MemoryRepository(database_session)
    service = LearningService(
        outcome_repository=OutcomeRepository(database_session),
        correction_repository=CorrectionRepository(database_session),
        memory_provider=SQLiteMemoryProvider(memory_repository),
    )
    try:
        yield service
    except Exception:
        database_session.rollback()
        raise
    else:
        database_session.commit()


@router.post(
    "/outcome",
    response_model=LearningResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an applied-fix outcome",
)
def record_outcome(
    payload: OutcomeLearningPayload,
    service: LearningService = Depends(get_learning_service),
) -> LearningResponse:
    """Store an outcome and linked outcome memory through the learning service.

    Args:
        payload: Applied fix and its observed success or failure.
        service: Transactional learning service dependency.

    Returns:
        Confirmation of the stored outcome learning event.
    """
    notes = payload.notes or ""
    if payload.outcome_status == "partial_success":
        notes = f"[partial_success] {notes}".strip()
    successful = (
        payload.outcome_status == "worked"
        if payload.outcome_status is not None
        else payload.successful
    )
    outcome = service.record_outcome(
        incident_id=payload.incident_id,
        fix_applied=payload.fix_applied,
        success=successful,
        notes=notes or None,
    )
    return LearningResponse(
        id=outcome.id,
        incident_id=outcome.incident_id,
        message="Outcome stored and added to operational memory.",
    )


@router.post(
    "/correction",
    response_model=LearningResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an engineer correction",
)
def record_correction(
    payload: CorrectionLearningPayload,
    service: LearningService = Depends(get_learning_service),
) -> LearningResponse:
    """Store a correction and its reusable meta-memory lesson.

    Args:
        payload: Previous and corrected diagnosis plus supporting explanation.
        service: Transactional learning service dependency.

    Returns:
        Confirmation of the stored correction learning event.
    """
    correction = service.record_correction(
        incident_id=payload.incident_id,
        original_root_cause=payload.previous_diagnosis,
        corrected_root_cause=payload.correct_diagnosis,
        reason=payload.explanation,
    )
    return LearningResponse(
        id=correction.id,
        incident_id=correction.incident_id,
        message="Correction stored and added to organizational memory.",
    )
