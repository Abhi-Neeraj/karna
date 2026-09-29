"""Database repository for incident outcome persistence operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outcome import Outcome


class OutcomeRepository:
    """Provides database-only operations for ``Outcome`` records."""

    def __init__(self, database_session: Session) -> None:
        """Initialize the repository with a caller-managed database session.

        Args:
            database_session: Active SQLAlchemy session used for persistence.
        """
        self._database_session = database_session

    def create_outcome(
        self,
        *,
        incident_id: int,
        fix_applied: str,
        success: bool,
        notes: str | None = None,
    ) -> Outcome:
        """Add an outcome to the current transaction and return it.

        Args:
            incident_id: Identifier of the associated incident.
            fix_applied: Final remediation action applied by the engineer.
            success: Whether the applied fix resolved the incident.
            notes: Optional result observations.

        Returns:
            The pending outcome with its database-generated identifier.

        Raises:
            ValueError: If the incident ID is invalid or fix text is empty.
        """
        if incident_id <= 0:
            raise ValueError("Incident ID must be positive.")
        if not fix_applied.strip():
            raise ValueError("Applied fix must not be empty.")

        outcome = Outcome(
            incident_id=incident_id,
            fix_applied=fix_applied,
            success=success,
            notes=notes,
        )
        self._database_session.add(outcome)
        self._database_session.flush()
        self._database_session.refresh(outcome)
        return outcome

    def get_by_incident(self, incident_id: int) -> list[Outcome]:
        """Retrieve all outcomes for an incident in creation order.

        Args:
            incident_id: Identifier of the associated incident.

        Returns:
            Persisted outcomes for the requested incident.

        Raises:
            ValueError: If the identifier is not positive.
        """
        if incident_id <= 0:
            raise ValueError("Incident ID must be positive.")

        statement = (
            select(Outcome)
            .where(Outcome.incident_id == incident_id)
            .order_by(Outcome.created_at.asc())
        )
        return list(self._database_session.scalars(statement).all())

    def get_all(self) -> list[Outcome]:
        """Retrieve all outcomes in reverse chronological creation order."""
        statement = select(Outcome).order_by(Outcome.created_at.desc())
        return list(self._database_session.scalars(statement).all())
