"""Database repository for provider-neutral operational memory records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory_record import MemoryRecord


class MemoryRepository:
    """Provides database-only operations for ``MemoryRecord`` entries."""

    def __init__(self, database_session: Session) -> None:
        """Initialize the repository with a caller-managed database session.

        Args:
            database_session: Active SQLAlchemy session used for persistence.
        """
        self._database_session = database_session

    def create_memory(
        self,
        *,
        incident_id: int,
        memory_type: str,
        content: str,
    ) -> MemoryRecord:
        """Add a memory record to the current transaction and return it.

        Args:
            incident_id: Identifier of the memory's source incident.
            memory_type: Classification of the stored operational memory.
            content: Searchable memory content.

        Returns:
            The pending memory record with its database-generated identifier.

        Raises:
            ValueError: If required memory fields are invalid.
        """
        if incident_id <= 0:
            raise ValueError("Incident ID must be positive.")
        if not memory_type.strip() or not content.strip():
            raise ValueError("Memory type and content must not be empty.")

        memory_record = MemoryRecord(
            incident_id=incident_id,
            memory_type=memory_type,
            content=content,
        )
        self._database_session.add(memory_record)
        self._database_session.flush()
        self._database_session.refresh(memory_record)
        return memory_record

    def get_by_incident(self, incident_id: int) -> list[MemoryRecord]:
        """Retrieve all memory records sourced from an incident.

        Args:
            incident_id: Identifier of the source incident.

        Returns:
            Memory records in chronological creation order.

        Raises:
            ValueError: If the identifier is not positive.
        """
        if incident_id <= 0:
            raise ValueError("Incident ID must be positive.")

        statement = (
            select(MemoryRecord)
            .where(MemoryRecord.incident_id == incident_id)
            .order_by(MemoryRecord.created_at.asc())
        )
        return list(self._database_session.scalars(statement).all())

    def get_by_type(self, memory_type: str) -> list[MemoryRecord]:
        """Retrieve memory records matching an exact memory classification.

        Args:
            memory_type: Memory classification to query.

        Returns:
            Matching records in reverse chronological creation order.

        Raises:
            ValueError: If the memory type is empty.
        """
        normalized_memory_type = memory_type.strip()
        if not normalized_memory_type:
            raise ValueError("Memory type must not be empty.")

        statement = (
            select(MemoryRecord)
            .where(MemoryRecord.memory_type == normalized_memory_type)
            .order_by(MemoryRecord.created_at.desc())
        )
        return list(self._database_session.scalars(statement).all())

    def get_all(self) -> list[MemoryRecord]:
        """Retrieve all memory records in reverse chronological creation order."""
        statement = select(MemoryRecord).order_by(MemoryRecord.created_at.desc())
        return list(self._database_session.scalars(statement).all())
