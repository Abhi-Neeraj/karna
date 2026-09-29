"""Regression tests for KARNA's memory-centric demo flow."""

import os
import unittest

os.environ["KARNA_DEBUG"] = "false"

from app.core.database import SessionLocal
from app.memory.sqlite_memory_provider import SQLiteMemoryProvider
from app.repositories.correction_repository import CorrectionRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.outcome_repository import OutcomeRepository
from app.services.analytics_service import AnalyticsService
from app.services.incident_analysis_service import IncidentAnalysisService
from app.services.learning_service import LearningService
from app.services.recommendation_service import RecommendationService
from app.utils.seed_database import seed_demo_database


class KarnaDemoFlowTests(unittest.TestCase):
    """Verify recall, ranking, learning, corrections, and analytics."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create a deterministic corpus shared by the regression tests."""
        seed_demo_database()

    def setUp(self) -> None:
        """Open a fresh session and construct the provider for each test."""
        self.session = SessionLocal()
        self.memory_repository = MemoryRepository(self.session)
        self.memory_provider = SQLiteMemoryProvider(self.memory_repository)

    def tearDown(self) -> None:
        """Discard test-local changes and close the database session."""
        self.session.rollback()
        self.session.close()

    def test_memory_recall_returns_connection_evidence(self) -> None:
        """Memory recall finds records for a connection-related query."""
        memories = self.memory_provider.recall_memories(query="connection", limit=5)
        self.assertGreater(len(memories), 0)

    def test_recommendation_ranking_prefers_proven_connection_fix(self) -> None:
        """Outcome and similarity scoring ranks the proven fix first."""
        result = RecommendationService(
            self.memory_provider,
            OutcomeRepository(self.session),
        ).generate_recommendations(
            query="database connection pool exhaustion",
            keywords=["database", "connection", "pool", "latency"],
            memory_enabled=True,
            limit=3,
        )
        self.assertEqual(result.recommendations[0].fix, "Restart connection pool")
        self.assertGreater(
            result.recommendations[0].recommendation_score,
            result.recommendations[1].recommendation_score,
        )

    def test_learning_loop_creates_outcome_memory(self) -> None:
        """Recording a result persists an outcome and retrievable memory."""
        service = LearningService(
            outcome_repository=OutcomeRepository(self.session),
            correction_repository=CorrectionRepository(self.session),
            memory_provider=self.memory_provider,
        )
        service.record_outcome(
            incident_id=1,
            fix_applied="Patch leaked connection lifecycle",
            success=True,
        )
        self.assertTrue(
            any(
                memory.memory_type == "outcome"
                and "Patch leaked connection lifecycle" in memory.content
                for memory in self.memory_provider.get_memory_by_incident(incident_id=1)
            )
        )

    def test_correction_creates_reusable_meta_memory(self) -> None:
        """An engineer correction produces a correction memory and meta-memory."""
        service = LearningService(
            outcome_repository=OutcomeRepository(self.session),
            correction_repository=CorrectionRepository(self.session),
            memory_provider=self.memory_provider,
        )
        service.record_correction(
            incident_id=1,
            original_root_cause="Database overload",
            corrected_root_cause="Database timeout",
            reason="Database timeout matched the query execution logs.",
        )
        corrections = CorrectionRepository(self.session).get_by_incident(1)
        correction_memories = [
            memory
            for memory in self.memory_provider.get_memory_by_incident(incident_id=1)
            if memory.memory_type == "correction"
        ]
        self.assertTrue(any(item.corrected_root_cause == "Database timeout" for item in corrections))
        self.assertGreaterEqual(len(correction_memories), 3)

    def test_analytics_reports_seeded_learning_metrics(self) -> None:
        """Analytics aggregates seeded incident, correction, and memory records."""
        snapshot = AnalyticsService(
            incident_repository=IncidentRepository(self.session),
            outcome_repository=OutcomeRepository(self.session),
            correction_repository=CorrectionRepository(self.session),
            memory_repository=self.memory_repository,
        ).get_dashboard_metrics()
        self.assertEqual(snapshot.total_incidents, 33)
        self.assertEqual(snapshot.corrections_count, 10)
        self.assertEqual(snapshot.memory_count, 86)
        self.assertGreater(len(snapshot.top_fixes), 0)

    def test_incident_analysis_identifies_latency_context(self) -> None:
        """Deterministic analysis supplies category and retrieval terms."""
        result = IncidentAnalysisService().analyze(
            title="API latency spike greater than 10 seconds",
            description="API requests show high latency and repeated timeout errors.",
        )
        self.assertEqual(result.category, "High Latency")
        self.assertIn("latency", result.keywords)


if __name__ == "__main__":
    unittest.main()
