"""SQLite-backed implementation of KARNA's operational memory contract."""

from app.memory.abstract_memory import AbstractMemoryProvider
from app.models.memory_record import MemoryRecord
from app.repositories.memory_repository import MemoryRepository


class SQLiteMemoryProvider(AbstractMemoryProvider):
    """Stores and recalls provider-neutral memory records through SQLite."""

    _INCIDENT_MEMORY_TYPE = "incident"
    _OUTCOME_MEMORY_TYPE = "outcome"
    _CORRECTION_MEMORY_TYPE = "correction"

    def __init__(self, memory_repository: MemoryRepository) -> None:
        """Initialize the provider with its injected persistence repository.

        Args:
            memory_repository: Repository used for all memory record access.
        """
        self._memory_repository = memory_repository

    def store_incident_memory(
        self,
        *,
        incident_id: int,
        content: str,
    ) -> MemoryRecord:
        """Store a new incident-context memory record.

        Args:
            incident_id: Identifier of the source incident.
            content: Searchable incident context.

        Returns:
            The stored incident memory record.
        """
        return self._memory_repository.create_memory(
            incident_id=incident_id,
            memory_type=self._INCIDENT_MEMORY_TYPE,
            content=content,
        )

    def store_outcome_memory(
        self,
        *,
        incident_id: int,
        content: str,
    ) -> MemoryRecord:
        """Store a new outcome-history memory record.

        Args:
            incident_id: Identifier of the source incident.
            content: Searchable outcome context.

        Returns:
            The stored outcome memory record.
        """
        return self._memory_repository.create_memory(
            incident_id=incident_id,
            memory_type=self._OUTCOME_MEMORY_TYPE,
            content=content,
        )

    def store_correction_memory(
        self,
        *,
        incident_id: int,
        content: str,
    ) -> MemoryRecord:
        """Store a new engineer-correction memory record.

        Args:
            incident_id: Identifier of the corrected incident.
            content: Searchable correction context.

        Returns:
            The stored correction memory record.
        """
        return self._memory_repository.create_memory(
            incident_id=incident_id,
            memory_type=self._CORRECTION_MEMORY_TYPE,
            content=content,
        )

    def recall_memories(self, *, query: str, limit: int) -> list[MemoryRecord]:
        """Return recent memory records whose content contains the query text.

        This MVP provider deliberately uses case-insensitive substring matching.
        It preserves the repository's reverse-chronological ordering and does not
        calculate semantic relevance or recommendation scores.

        Args:
            query: Text to match against stored memory content.
            limit: Maximum number of matching records to return.

        Returns:
            At most ``limit`` case-insensitive content matches.

        Raises:
            ValueError: If query text is empty or limit is not positive.
        """
        normalized_query = query.strip().casefold()
        if not normalized_query:
            raise ValueError("Memory recall query must not be empty.")
        if limit <= 0:
            raise ValueError("Memory recall limit must be positive.")

        matching_memories: list[MemoryRecord] = []
        for memory_record in self._memory_repository.get_all():
            if normalized_query in memory_record.content.casefold():
                matching_memories.append(memory_record)
            if len(matching_memories) == limit:
                break

        return matching_memories

    def get_memory_by_incident(self, *, incident_id: int) -> list[MemoryRecord]:
        """Return all records retaining provenance to an incident.

        Args:
            incident_id: Identifier of the source incident.

        Returns:
            Memory records linked to the requested incident.
        """
        return self._memory_repository.get_by_incident(incident_id)

    def get_all_memories(self) -> list[MemoryRecord]:
        """Return all SQLite-backed operational memory records.

        Returns:
            All memory records available to this provider.
        """
        return self._memory_repository.get_all()
