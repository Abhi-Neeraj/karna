"""Database repository for incident persistence operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident import Incident


class IncidentRepository:
    """Provides database-only operations for ``Incident`` records."""

    def __init__(self, database_session: Session) -> None:
        """Initialize the repository with a caller-managed database session.

        Args:
            database_session: Active SQLAlchemy session used for persistence.
        """
        self._database_session = database_session

    def create_incident(
        self,
        *,
        title: str,
        description: str,
        root_cause: str | None = None,
        service_name: str | None = None,
        severity: str | None = None,
    ) -> Incident:
        """Add an incident to the current transaction and return it.

        Args:
            title: Concise incident title.
            description: Detailed incident context.
            root_cause: Optional known root cause.
            service_name: Optional affected service name.
            severity: Optional incident severity.

        Returns:
            The pending incident with its database-generated identifier.

        Raises:
            ValueError: If required incident text is empty.
        """
        if not title.strip() or not description.strip():
            raise ValueError("Incident title and description must not be empty.")

        incident = Incident(
            title=title,
            description=description,
            root_cause=root_cause,
            service_name=service_name,
            severity=severity,
        )
        self._database_session.add(incident)
        self._database_session.flush()
        self._database_session.refresh(incident)
        return incident

    def get_by_id(self, incident_id: int) -> Incident | None:
        """Retrieve one incident by its primary key.

        Args:
            incident_id: Persistent incident identifier.

        Returns:
            The matching incident, or ``None`` when it does not exist.

        Raises:
            ValueError: If the identifier is not positive.
        """
        if incident_id <= 0:
            raise ValueError("Incident ID must be positive.")

        return self._database_session.get(Incident, incident_id)

    def get_all(self) -> list[Incident]:
        """Retrieve all incidents in reverse chronological creation order."""
        statement = select(Incident).order_by(Incident.created_at.desc())
        return list(self._database_session.scalars(statement).all())

    def delete_incident(self, incident: Incident) -> None:
        """Mark an incident and its cascading child records for deletion.

        Args:
            incident: Persistent incident instance to delete.
        """
        self._database_session.delete(incident)
        self._database_session.flush()

    def search_by_service(self, service_name: str) -> list[Incident]:
        """Retrieve incidents associated with an exact service name.

        Args:
            service_name: Service name to query.

        Returns:
            Matching incidents in reverse chronological creation order.

        Raises:
            ValueError: If the service name is empty.
        """
        normalized_service_name = service_name.strip()
        if not normalized_service_name:
            raise ValueError("Service name must not be empty.")

        statement = (
            select(Incident)
            .where(Incident.service_name == normalized_service_name)
            .order_by(Incident.created_at.desc())
        )
        return list(self._database_session.scalars(statement).all())
