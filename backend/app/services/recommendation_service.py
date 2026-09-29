"""Outcome-aware, memory-similarity recommendation generation for KARNA."""

from dataclasses import dataclass
from datetime import datetime
import re

from app.memory.abstract_memory import AbstractMemoryProvider
from app.models.memory_record import MemoryRecord
from app.repositories.outcome_repository import OutcomeRepository


@dataclass(frozen=True, slots=True)
class RecalledMemory:
    """A retrieved memory with transparent lexical relevance evidence."""

    memory: MemoryRecord
    similarity_score: float
    matched_terms: list[str]


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A ranked fix candidate supported by historical operational evidence."""

    fix: str
    success_count: int
    failure_count: int
    success_rate: float
    memory_similarity: float
    recommendation_score: float
    evidence_incidents: list[int]
    confidence_score: float


@dataclass(frozen=True, slots=True)
class RecommendationResult:
    """Recommendation output, recalled evidence, and Memory On/Off state."""

    recommendations: list[Recommendation]
    recalled_memories: list[RecalledMemory]
    memory_enabled: bool


@dataclass(slots=True)
class _FixEvidence:
    """Internal aggregate used to score a single historical fix."""

    success_count: int
    failure_count: int
    evidence_incidents: set[int]
    most_recent_outcome_at: datetime
    similarity_total: float
    similarity_samples: int


class RecommendationService:
    """Ranks historical fixes using outcomes and similarity-weighted memory."""

    _GENERIC_FIXES: tuple[str, ...] = (
        "Review recent error logs and affected dependency health.",
        "Verify configuration, capacity, and connection limits.",
        "Compare current behavior with the incident runbook before applying changes.",
    )
    _TOKEN_PATTERN = re.compile(r"[a-z][a-z0-9._-]{2,}")

    def __init__(
        self,
        memory_provider: AbstractMemoryProvider,
        outcome_repository: OutcomeRepository,
    ) -> None:
        """Initialize memory and outcome dependencies through injection."""
        self._memory_provider = memory_provider
        self._outcome_repository = outcome_repository

    def generate_recommendations(
        self,
        *,
        query: str,
        keywords: list[str],
        memory_enabled: bool,
        limit: int = 3,
    ) -> RecommendationResult:
        """Generate generic or outcome-and-memory-backed recommendations."""
        if not query.strip():
            raise ValueError("Recommendation query must not be empty.")
        if limit <= 0:
            raise ValueError("Recommendation limit must be positive.")
        if not memory_enabled:
            return RecommendationResult(
                recommendations=self._generic_recommendations(limit),
                recalled_memories=[],
                memory_enabled=False,
            )

        recalled_memories = self._recall_memories(
            query=query,
            keywords=keywords,
            limit=max(limit * 10, 20),
        )
        recommendations = self._rank_historical_fixes(recalled_memories)
        return RecommendationResult(
            recommendations=(recommendations or self._generic_recommendations(limit))[:limit],
            recalled_memories=recalled_memories,
            memory_enabled=True,
        )

    def _recall_memories(
        self,
        *,
        query: str,
        keywords: list[str],
        limit: int,
    ) -> list[RecalledMemory]:
        """Recall candidate records and return relevance-scored incident evidence."""
        query_terms = self._tokens(" ".join([query, *keywords]))
        candidates: dict[int, MemoryRecord] = {}
        for term in sorted(query_terms):
            for memory in self._memory_provider.recall_memories(query=term, limit=limit):
                candidates.setdefault(memory.id, memory)

        correction_similarity_by_incident: dict[int, float] = {}
        for memory in candidates.values():
            if memory.memory_type == "correction":
                correction_similarity_by_incident[memory.incident_id] = max(
                    correction_similarity_by_incident.get(memory.incident_id, 0.0),
                    self._similarity(query_terms, self._tokens(memory.content)),
                )
        recalled = [
            RecalledMemory(
                memory=memory,
                similarity_score=min(
                    self._similarity(query_terms, self._tokens(memory.content))
                    + correction_similarity_by_incident.get(memory.incident_id, 0.0)
                    * 0.15,
                    1.0,
                ),
                matched_terms=sorted(query_terms & self._tokens(memory.content)),
            )
            for memory in candidates.values()
            if memory.memory_type == "incident"
        ]
        return sorted(
            (memory for memory in recalled if memory.similarity_score > 0),
            key=lambda memory: (memory.similarity_score, memory.memory.created_at),
            reverse=True,
        )[:limit]

    def _rank_historical_fixes(
        self,
        recalled_memories: list[RecalledMemory],
    ) -> list[Recommendation]:
        """Group fixes and sort by transparent recommendation score descending."""
        evidence_by_fix: dict[str, _FixEvidence] = {}
        for recalled_memory in recalled_memories:
            incident_id = recalled_memory.memory.incident_id
            for outcome in self._outcome_repository.get_by_incident(incident_id):
                evidence = evidence_by_fix.setdefault(
                    outcome.fix_applied,
                    _FixEvidence(
                        success_count=0,
                        failure_count=0,
                        evidence_incidents=set(),
                        most_recent_outcome_at=outcome.created_at,
                        similarity_total=0.0,
                        similarity_samples=0,
                    ),
                )
                if outcome.success:
                    evidence.success_count += 1
                else:
                    evidence.failure_count += 1
                evidence.evidence_incidents.add(incident_id)
                evidence.similarity_total += recalled_memory.similarity_score
                evidence.similarity_samples += 1
                evidence.most_recent_outcome_at = max(
                    evidence.most_recent_outcome_at,
                    outcome.created_at,
                )

        ranked_evidence = sorted(
            evidence_by_fix.items(),
            key=lambda item: (
                self._recommendation_score(item[1]),
                item[1].success_count,
                item[1].most_recent_outcome_at,
            ),
            reverse=True,
        )
        return [
            Recommendation(
                fix=fix,
                success_count=evidence.success_count,
                failure_count=evidence.failure_count,
                success_rate=self._success_rate(evidence),
                memory_similarity=self._memory_similarity(evidence),
                recommendation_score=self._recommendation_score(evidence),
                evidence_incidents=sorted(evidence.evidence_incidents),
                confidence_score=self._confidence_score(evidence),
            )
            for fix, evidence in ranked_evidence
        ]

    @staticmethod
    def _success_rate(evidence: _FixEvidence) -> float:
        """Calculate a fix success rate from recorded outcomes."""
        total = evidence.success_count + evidence.failure_count
        return evidence.success_count / total if total else 0.0

    @staticmethod
    def _memory_similarity(evidence: _FixEvidence) -> float:
        """Return average evidence similarity for a fix."""
        return (
            evidence.similarity_total / evidence.similarity_samples
            if evidence.similarity_samples
            else 0.0
        )

    def _recommendation_score(self, evidence: _FixEvidence) -> float:
        """Return score = success rate * 0.7 + similarity * 0.3."""
        return round(
            self._success_rate(evidence) * 0.7
            + self._memory_similarity(evidence) * 0.3,
            4,
        )

    def _confidence_score(self, evidence: _FixEvidence) -> float:
        """Return bounded confidence from score and supporting incident coverage."""
        coverage = min(len(evidence.evidence_incidents) / 5, 1.0)
        return round((self._recommendation_score(evidence) * 0.8 + coverage * 0.2) * 100, 2)

    @classmethod
    def _tokens(cls, text: str) -> set[str]:
        """Normalize meaningful lexical tokens for MVP similarity scoring."""
        return set(cls._TOKEN_PATTERN.findall(text.casefold()))

    @staticmethod
    def _similarity(query_terms: set[str], memory_terms: set[str]) -> float:
        """Calculate query-term coverage without penalizing detailed memories."""
        return len(query_terms & memory_terms) / len(query_terms) if query_terms else 0.0

    def _generic_recommendations(self, limit: int) -> list[Recommendation]:
        """Return cautious guidance that does not use organizational memory."""
        return [
            Recommendation(
                fix=fix,
                success_count=0,
                failure_count=0,
                success_rate=0.0,
                memory_similarity=0.0,
                recommendation_score=0.0,
                evidence_incidents=[],
                confidence_score=0.0,
            )
            for fix in self._GENERIC_FIXES[:limit]
        ]
