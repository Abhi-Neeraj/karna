"""Database repository for engineer correction persistence operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.correction import Correction


class CorrectionRepository:
    """Provides database-only operations for ``Correction`` records."""

    def __init__(self, database_session: Session) -> None:
        """Initialize the repository with a caller-managed database session.

        Args:
            database_session: Active SQLAlchemy session used for persistence.
        """
        self._database_session = database_session

    def create_correction(
        self,
        *,
        incident_id: int,
        original_root_cause: str | None,
        corrected_root_cause: str,
        reason: str,
    ) -> Correction:
        """Add an engineer correction to the current transaction.

        Args:
            incident_id: Identifier of the corrected incident.
            original_root_cause: Previous diagnosis, when one existed.
            corrected_root_cause: Engineer-validated diagnosis.
            reason: Supporting correction rationale.

        Returns:
            The pending correction with its database-generated identifier.

        Raises:
            ValueError: If required correction fields are invalid.
        """
        if incident_id <= 0:
            raise ValueError("Incident ID must be positive.")
        if not corrected_root_cause.strip() or not reason.strip():
            raise ValueError("Corrected root cause and reason must not be empty.")

        correction = Correction(
            incident_id=incident_id,
            original_root_cause=original_root_cause,
            corrected_root_cause=corrected_root_cause,
            reason=reason,
        )
        self._database_session.add(correction)
        self._database_session.flush()
        self._database_session.refresh(correction)
        return correction

    def get_by_incident(self, incident_id: int) -> list[Correction]:
        """Retrieve all corrections for an incident in creation order.

        Args:
            incident_id: Identifier of the associated incident.

        Returns:
            Persisted corrections for the requested incident.

        Raises:
            ValueError: If the identifier is not positive.
        """
        if incident_id <= 0:
            raise ValueError("Incident ID must be positive.")

        statement = (
            select(Correction)
            .where(Correction.incident_id == incident_id)
            .order_by(Correction.created_at.asc())
        )
        return list(self._database_session.scalars(statement).all())

    def get_all(self) -> list[Correction]:
        """Retrieve all corrections in reverse chronological creation order."""
        statement = select(Correction).order_by(Correction.created_at.desc())
        return list(self._database_session.scalars(statement).all())
