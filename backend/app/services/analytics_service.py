"""Read-only learning and memory analytics for KARNA demonstrations."""

from dataclasses import dataclass

from app.repositories.correction_repository import CorrectionRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.outcome_repository import OutcomeRepository


@dataclass(frozen=True, slots=True)
class FixPerformance:
    """Outcome evidence aggregated for one applied fix."""

    fix: str
    success_count: int
    failure_count: int
    success_rate: float


@dataclass(frozen=True, slots=True)
class AnalyticsSnapshot:
    """Dashboard-ready summary of KARNA's operational learning state."""

    total_incidents: int
    resolved_incidents: int
    corrections_count: int
    memory_count: int
    top_fixes: list[FixPerformance]
    learning_improvement: float


@dataclass(frozen=True, slots=True)
class MemoryModeComparison:
    """Evidence comparison that makes Memory Off and Memory On visible."""

    memory_off_evidence_count: int
    memory_on_evidence_count: int
    outcome_backed_fix_count: int


@dataclass(slots=True)
class _FixCounts:
    """Internal mutable counter used while aggregating outcome rows."""

    display_name: str
    success_count: int = 0
    failure_count: int = 0


class AnalyticsService:
    """Generates read-only metrics from repository-provided records."""

    def __init__(
        self,
        incident_repository: IncidentRepository,
        outcome_repository: OutcomeRepository,
        correction_repository: CorrectionRepository,
        memory_repository: MemoryRepository,
    ) -> None:
        """Initialize repositories used to read analytics source records.

        Args:
            incident_repository: Source for incident totals.
            outcome_repository: Source for resolution and fix-performance data.
            correction_repository: Source for correction learning counts.
            memory_repository: Source for memory corpus metrics.
        """
        self._incident_repository = incident_repository
        self._outcome_repository = outcome_repository
        self._correction_repository = correction_repository
        self._memory_repository = memory_repository

    def get_incident_counts(self) -> tuple[int, int]:
        """Return total incidents and incidents with at least one success outcome.

        Returns:
            A tuple of total incident count and resolved incident count.
        """
        incidents = self._incident_repository.get_all()
        resolved_incident_ids = {
            outcome.incident_id
            for outcome in self._outcome_repository.get_all()
            if outcome.success
        }
        return len(incidents), len(resolved_incident_ids)

    def get_success_rates(self) -> list[FixPerformance]:
        """Aggregate recorded outcome success rates for every applied fix.

        Returns:
            Fix performance records ordered by rate, successes, then name.
        """
        counts_by_fix: dict[str, _FixCounts] = {}
        for outcome in self._outcome_repository.get_all():
            normalized_fix = outcome.fix_applied.strip().casefold()
            counts = counts_by_fix.setdefault(
                normalized_fix,
                _FixCounts(display_name=outcome.fix_applied.strip()),
            )
            if outcome.success:
                counts.success_count += 1
            else:
                counts.failure_count += 1

        performances = [
            FixPerformance(
                fix=counts.display_name,
                success_count=counts.success_count,
                failure_count=counts.failure_count,
                success_rate=self._success_rate(counts),
            )
            for counts in counts_by_fix.values()
        ]
        return sorted(
            performances,
            key=lambda performance: (
                performance.success_rate,
                performance.success_count,
                performance.fix.casefold(),
            ),
            reverse=True,
        )

    def get_learning_metrics(self) -> tuple[int, float]:
        """Return correction count and outcome-based learning improvement score.

        The improvement score is the percentage of recorded outcomes that are
        successful. It is an evidence-quality signal rather than an MTTR claim.

        Returns:
            A tuple of correction count and success percentage from 0 to 100.
        """
        corrections_count = len(self._correction_repository.get_all())
        outcomes = self._outcome_repository.get_all()
        successful_outcomes = sum(outcome.success for outcome in outcomes)
        improvement = (
            round(successful_outcomes / len(outcomes) * 100, 2)
            if outcomes
            else 0.0
        )
        return corrections_count, improvement

    def get_memory_growth(self) -> int:
        """Return the current number of retrievable operational memories.

        Returns:
            Total memory corpus size, suitable for trend snapshots over time.
        """
        return len(self._memory_repository.get_all())

    def get_dashboard_metrics(self, *, top_fix_limit: int = 5) -> AnalyticsSnapshot:
        """Build the complete dashboard summary from read-only repository data.

        Args:
            top_fix_limit: Maximum number of successful fixes to include.

        Returns:
            A dashboard-ready operational learning snapshot.

        Raises:
            ValueError: If the requested top-fix limit is not positive.
        """
        if top_fix_limit <= 0:
            raise ValueError("Top fix limit must be positive.")

        total_incidents, resolved_incidents = self.get_incident_counts()
        corrections_count, learning_improvement = self.get_learning_metrics()
        return AnalyticsSnapshot(
            total_incidents=total_incidents,
            resolved_incidents=resolved_incidents,
            corrections_count=corrections_count,
            memory_count=self.get_memory_growth(),
            top_fixes=self.get_success_rates()[:top_fix_limit],
            learning_improvement=learning_improvement,
        )

    def get_memory_mode_comparison(self) -> MemoryModeComparison:
        """Return metrics that distinguish generic and memory-backed guidance.

        Returns:
            Evidence counts for Memory Off and Memory On plus the number of
            outcome-backed fix candidates available to Memory On analysis.
        """
        memory_count = self.get_memory_growth()
        return MemoryModeComparison(
            memory_off_evidence_count=0,
            memory_on_evidence_count=memory_count,
            outcome_backed_fix_count=len(self.get_success_rates()),
        )

    @staticmethod
    def _success_rate(counts: _FixCounts) -> float:
        """Calculate a safe success rate from aggregate outcome counts."""
        total = counts.success_count + counts.failure_count
        return counts.success_count / total if total else 0.0
