"""Services that turn engineer feedback into durable KARNA memory."""

from app.memory.abstract_memory import AbstractMemoryProvider
from app.models.correction import Correction
from app.models.memory_record import MemoryRecord
from app.models.outcome import Outcome
from app.repositories.correction_repository import CorrectionRepository
from app.repositories.outcome_repository import OutcomeRepository


class LearningService:
    """Closes the incident-response learning loop through feedback records."""

    def __init__(
        self,
        outcome_repository: OutcomeRepository,
        correction_repository: CorrectionRepository,
        memory_provider: AbstractMemoryProvider,
    ) -> None:
        """Initialize repositories and the active provider through injection.

        Args:
            outcome_repository: Repository for outcome persistence.
            correction_repository: Repository for correction persistence.
            memory_provider: Provider used to create retrievable learning memory.
        """
        self._outcome_repository = outcome_repository
        self._correction_repository = correction_repository
        self._memory_provider = memory_provider

    def record_outcome(
        self,
        *,
        incident_id: int,
        fix_applied: str,
        success: bool,
        notes: str | None = None,
    ) -> Outcome:
        """Persist an applied-fix outcome and create linked outcome memory.

        Args:
            incident_id: Identifier of the resolved or unresolved incident.
            fix_applied: Final remediation action used by the engineer.
            success: Whether the action resolved the incident.
            notes: Optional observations about the result.

        Returns:
            The stored outcome record in the caller-managed transaction.
        """
        outcome = self._outcome_repository.create_outcome(
            incident_id=incident_id,
            fix_applied=fix_applied,
            success=success,
            notes=notes,
        )
        outcome_label = "success" if success else "failure"
        note_segment = f" Notes: {notes.strip()}" if notes and notes.strip() else ""
        self._memory_provider.store_outcome_memory(
            incident_id=incident_id,
            content=(
                f"Applied fix: {fix_applied.strip()}. "
                f"Outcome: {outcome_label}.{note_segment}"
            ),
        )
        return outcome

    def record_correction(
        self,
        *,
        incident_id: int,
        original_root_cause: str | None,
        corrected_root_cause: str,
        reason: str,
    ) -> Correction:
        """Persist an engineer correction and add correction-driven memory.

        Args:
            incident_id: Identifier of the corrected incident.
            original_root_cause: Previous diagnosis, when known.
            corrected_root_cause: Engineer-validated replacement diagnosis.
            reason: Supporting explanation for the correction.

        Returns:
            The stored correction record in the caller-managed transaction.
        """
        correction = self._correction_repository.create_correction(
            incident_id=incident_id,
            original_root_cause=original_root_cause,
            corrected_root_cause=corrected_root_cause,
            reason=reason,
        )
        previous_diagnosis = original_root_cause or "No prior diagnosis recorded"
        self._memory_provider.store_correction_memory(
            incident_id=incident_id,
            content=(
                f"Previous diagnosis: {previous_diagnosis}. "
                f"Correct diagnosis: {corrected_root_cause.strip()}. "
                f"Reason: {reason.strip()}"
            ),
        )
        self.create_meta_memory(
            incident_id=incident_id,
            previous_diagnosis=previous_diagnosis,
            corrected_diagnosis=corrected_root_cause,
        )
        return correction

    def create_meta_memory(
        self,
        *,
        incident_id: int,
        previous_diagnosis: str,
        corrected_diagnosis: str,
    ) -> MemoryRecord:
        """Create an actionable lesson from a root-cause correction.

        Args:
            incident_id: Identifier of the incident that produced the lesson.
            previous_diagnosis: Earlier diagnosis that should be reconsidered.
            corrected_diagnosis: Engineer-validated diagnosis to favor.

        Returns:
            A correction-type memory containing the reusable operational lesson.
        """
        previous = previous_diagnosis.strip()
        corrected = corrected_diagnosis.strip()
        if not previous or not corrected:
            raise ValueError("Meta-memory diagnoses must not be empty.")

        return self._memory_provider.store_correction_memory(
            incident_id=incident_id,
            content=(
                "When incident symptoms resemble a previous diagnosis of "
                f"{previous}, prefer checking {corrected} before repeating "
                "the earlier remediation path."
            ),
        )
