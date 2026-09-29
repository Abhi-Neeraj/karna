"""Provider-agnostic contract for KARNA operational memory."""

from abc import ABC, abstractmethod

from app.models.memory_record import MemoryRecord


class AbstractMemoryProvider(ABC):
    """Defines the memory operations used by KARNA application services."""

    @abstractmethod
    def store_incident_memory(
        self,
        *,
        incident_id: int,
        content: str,
    ) -> MemoryRecord:
        """Store retrievable memory describing an incident.

        Args:
            incident_id: Identifier of the source incident.
            content: Normalized searchable incident context.

        Returns:
            The stored incident memory record.
        """

    @abstractmethod
    def store_outcome_memory(
        self,
        *,
        incident_id: int,
        content: str,
    ) -> MemoryRecord:
        """Store retrievable memory describing an incident outcome.

        Args:
            incident_id: Identifier of the source incident.
            content: Normalized searchable outcome context.

        Returns:
            The stored outcome memory record.
        """

    @abstractmethod
    def store_correction_memory(
        self,
        *,
        incident_id: int,
        content: str,
    ) -> MemoryRecord:
        """Store retrievable memory describing an engineer correction.

        Args:
            incident_id: Identifier of the corrected incident.
            content: Normalized searchable correction context.

        Returns:
            The stored correction memory record.
        """

    @abstractmethod
    def recall_memories(self, *, query: str, limit: int) -> list[MemoryRecord]:
        """Recall memories matching a query using provider-specific retrieval.

        Args:
            query: Incident context used to locate relevant memories.
            limit: Maximum number of matching memory records to return.

        Returns:
            Matching memory records in provider-defined retrieval order.
        """

    @abstractmethod
    def get_memory_by_incident(self, *, incident_id: int) -> list[MemoryRecord]:
        """Return all memories that retain provenance to one incident.

        Args:
            incident_id: Identifier of the source incident.

        Returns:
            All memory records linked to the incident.
        """

    @abstractmethod
    def get_all_memories(self) -> list[MemoryRecord]:
        """Return all memories made available by the provider.

        Returns:
            All stored operational memory records.
        """
