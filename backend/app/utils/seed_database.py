"""Deterministic database seeding and demo validation for KARNA."""

import logging

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine, init_db
from app.memory.sqlite_memory_provider import SQLiteMemoryProvider
from app.models.correction import Correction
from app.models.fix_statistics import FixStatistics
from app.models.incident import Incident
from app.models.memory_record import MemoryRecord
from app.models.outcome import Outcome
from app.repositories.memory_repository import MemoryRepository
from app.repositories.outcome_repository import OutcomeRepository
from app.repositories.correction_repository import CorrectionRepository
from app.repositories.incident_repository import IncidentRepository
from app.services.analytics_service import AnalyticsService
from app.services.incident_analysis_service import IncidentAnalysisService
from app.services.recommendation_service import Recommendation, RecommendationService
from app.utils.demo_data import DEMO_CORRECTIONS, DEMO_INCIDENTS, DEMO_META_MEMORIES

logger = logging.getLogger(__name__)


def seed_demo_database() -> None:
    """Replace local KARNA data with the deterministic demo dataset.

    The function is intentionally explicit: it drops only tables registered in
    the KARNA metadata, recreates them, and then inserts the demo corpus.

    Raises:
        SQLAlchemyError: If table initialization or data persistence fails.
    """
    logger.warning("Resetting the local KARNA database with demo data")
    Base.metadata.drop_all(bind=engine)
    init_db()

    try:
        with SessionLocal() as database_session:
            incidents = _insert_incidents(database_session)
            outcomes = _insert_outcomes(database_session, incidents)
            _insert_incident_and_outcome_memories(database_session, incidents, outcomes)
            _insert_corrections_and_meta_memories(database_session, incidents)
            _insert_fix_statistics(database_session, outcomes)
            database_session.commit()
    except SQLAlchemyError:
        logger.exception("Unable to seed the KARNA demo database")
        raise

    logger.info(
        "Seeded KARNA demo database with %d incidents, %d corrections, and %d meta-memories",
        len(DEMO_INCIDENTS),
        len(DEMO_CORRECTIONS),
        len(DEMO_META_MEMORIES),
    )


def _insert_incidents(database_session: Session) -> list[Incident]:
    """Insert the canonical incident source records.

    Args:
        database_session: Active session used for fixture persistence.

    Returns:
        Persisted incidents in the same order as the source fixtures.
    """
    incidents = [
        Incident(
            title=fixture.title,
            description=fixture.description,
            root_cause=fixture.root_cause,
            service_name=fixture.category,
            severity="SEV-2" if fixture.category == "Database" else "SEV-3",
            created_at=fixture.timestamp,
        )
        for fixture in DEMO_INCIDENTS
    ]
    database_session.add_all(incidents)
    database_session.flush()
    return incidents


def _insert_outcomes(
    database_session: Session,
    incidents: list[Incident],
) -> list[Outcome]:
    """Insert one observed fix outcome per demo incident.

    Args:
        database_session: Active session used for fixture persistence.
        incidents: Persisted incidents corresponding to source fixtures.

    Returns:
        Persisted outcomes in the same order as the source fixtures.
    """
    outcomes = [
        Outcome(
            incident_id=incidents[index].id,
            fix_applied=fixture.fix,
            success=fixture.success,
            notes=(
                "Service recovered after remediation."
                if fixture.success
                else "Remediation did not restore service; further diagnosis was required."
            ),
            created_at=fixture.timestamp,
        )
        for index, fixture in enumerate(DEMO_INCIDENTS)
    ]
    database_session.add_all(outcomes)
    database_session.flush()
    return outcomes


def _insert_incident_and_outcome_memories(
    database_session: Session,
    incidents: list[Incident],
    outcomes: list[Outcome],
) -> None:
    """Create retrievable incident and outcome memory for every fixture.

    Args:
        database_session: Active session used for memory persistence.
        incidents: Persisted incident source records.
        outcomes: Persisted outcome source records.
    """
    memories: list[MemoryRecord] = []
    for index, fixture in enumerate(DEMO_INCIDENTS):
        outcome_label = "Success" if fixture.success else "Failure"
        memories.extend(
            (
                MemoryRecord(
                    incident_id=incidents[index].id,
                    memory_type="incident",
                    content=(
                        f"Category: {fixture.category}. Title: {fixture.title}. "
                        f"Symptoms: {', '.join(fixture.symptoms)}. "
                        f"Root cause: {fixture.root_cause}."
                    ),
                    created_at=fixture.timestamp,
                ),
                MemoryRecord(
                    incident_id=outcomes[index].incident_id,
                    memory_type="outcome",
                    content=(
                        f"Fix applied: {fixture.fix}. Outcome: {outcome_label}. "
                        f"Incident category: {fixture.category}."
                    ),
                    created_at=fixture.timestamp,
                ),
            )
        )
    database_session.add_all(memories)
    database_session.flush()


def _insert_corrections_and_meta_memories(
    database_session: Session,
    incidents: list[Incident],
) -> None:
    """Insert correction events and their reusable organizational lessons.

    Args:
        database_session: Active session used for fixture persistence.
        incidents: Persisted incident source records.
    """
    corrections: list[Correction] = []
    memories: list[MemoryRecord] = []
    for correction in DEMO_CORRECTIONS:
        source_incident = incidents[correction.incident_index]
        corrections.append(
            Correction(
                incident_id=source_incident.id,
                original_root_cause=correction.previous_diagnosis,
                corrected_root_cause=correction.corrected_diagnosis,
                reason=correction.explanation,
                created_at=source_incident.created_at,
            )
        )
        memories.append(
            MemoryRecord(
                incident_id=source_incident.id,
                memory_type="correction",
                content=(
                    f"Previous diagnosis: {correction.previous_diagnosis}. "
                    f"Correct diagnosis: {correction.corrected_diagnosis}. "
                    f"Reason: {correction.explanation}"
                ),
                created_at=source_incident.created_at,
            )
        )

    for meta_memory in DEMO_META_MEMORIES:
        source_incident = incidents[meta_memory.incident_index]
        memories.append(
            MemoryRecord(
                incident_id=source_incident.id,
                memory_type="correction",
                content=meta_memory.content,
                created_at=source_incident.created_at,
            )
        )

    database_session.add_all(corrections)
    database_session.add_all(memories)
    database_session.flush()


def _insert_fix_statistics(
    database_session: Session,
    outcomes: list[Outcome],
) -> None:
    """Persist materialized fix success and failure counts for demo inspection.

    Args:
        database_session: Active session used for fixture persistence.
        outcomes: Persisted outcomes used to calculate aggregate statistics.
    """
    counts: dict[str, list[int]] = {}
    for outcome in outcomes:
        success_count, failure_count = counts.setdefault(outcome.fix_applied, [0, 0])
        if outcome.success:
            success_count += 1
        else:
            failure_count += 1
        counts[outcome.fix_applied] = [success_count, failure_count]

    statistics = [
        FixStatistics(
            fix_name=fix_name,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_count / (success_count + failure_count),
        )
        for fix_name, (success_count, failure_count) in counts.items()
    ]
    database_session.add_all(statistics)
    database_session.flush()


def run_demo_validation() -> bool:
    """Validate corpus size, recall, and outcome-aware ranking after seeding.

    Returns:
        ``True`` only when all required demo checks pass.
    """
    with SessionLocal() as database_session:
        incident_count = _count_rows(database_session, Incident)
        outcome_count = _count_rows(database_session, Outcome)
        correction_count = _count_rows(database_session, Correction)
        memory_count = _count_rows(database_session, MemoryRecord)

        memory_provider = SQLiteMemoryProvider(MemoryRepository(database_session))
        recalled_memories = memory_provider.recall_memories(query="connection", limit=5)
        recommendation_service = RecommendationService(
            memory_provider=memory_provider,
            outcome_repository=OutcomeRepository(database_session),
        )
        recommendation_result = recommendation_service.generate_recommendations(
            query="database connection pool exhaustion",
            keywords=["database", "connection", "pool", "latency"],
            memory_enabled=True,
            limit=10,
        )
        analysis = IncidentAnalysisService().analyze(
            title="API latency spike greater than 10 seconds",
            description="The API has high latency and repeated request timeout errors.",
        )
        analytics = AnalyticsService(
            incident_repository=IncidentRepository(database_session),
            outcome_repository=OutcomeRepository(database_session),
            correction_repository=CorrectionRepository(database_session),
            memory_repository=MemoryRepository(database_session),
        ).get_dashboard_metrics()
        learning_memory_count = len(
            memory_provider.get_memory_by_incident(incident_id=1)
        )
        correction_memory_count = len(
            [
                memory
                for memory in memory_provider.get_memory_by_incident(incident_id=1)
                if memory.memory_type == "correction"
            ]
        )

    expected_memory_count = len(DEMO_INCIDENTS) * 2 + len(DEMO_CORRECTIONS) + len(
        DEMO_META_MEMORIES
    )
    expected_top_fix = "Restart connection pool"
    top_fix = (
        recommendation_result.recommendations[0].fix
        if recommendation_result.recommendations
        else None
    )
    checks = {
        "Incident count": incident_count == len(DEMO_INCIDENTS),
        "Outcome count": outcome_count == len(DEMO_INCIDENTS),
        "Correction count": correction_count == len(DEMO_CORRECTIONS),
        "Memory count": memory_count == expected_memory_count,
        "Memory recall": len(recalled_memories) > 0,
        "Recommendation ranking": top_fix == expected_top_fix,
        "Incident analysis": analysis.category == "High Latency",
        "Learning loop": learning_memory_count >= 2,
        "Correction learning": correction_memory_count >= 2,
        "Analytics": (
            analytics.total_incidents == len(DEMO_INCIDENTS)
            and analytics.corrections_count == len(DEMO_CORRECTIONS)
            and analytics.memory_count == expected_memory_count
        ),
    }

    for check_name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} - {check_name}")
    _print_demo_examples(recalled_memories, recommendation_result.recommendations)
    return all(checks.values())


def _count_rows(database_session: Session, model_class: type[Base]) -> int:
    """Return the number of rows for a mapped model class.

    Args:
        database_session: Active session used for validation reads.
        model_class: SQLAlchemy mapped class being counted.

    Returns:
        Number of persisted rows for the model.
    """
    count = database_session.scalar(select(func.count()).select_from(model_class))
    return int(count or 0)


def _print_demo_examples(
    recalled_memories: list[MemoryRecord],
    recommendations: list[Recommendation],
) -> None:
    """Print concise inspectable recall and ranking examples for demo rehearsal.

    Args:
        recalled_memories: Memory matches returned by the provider.
        recommendations: Ranked recommendations returned by the service.
    """
    print("\nMemory recall sample:")
    for memory in recalled_memories[:3]:
        print(f"- Memory {memory.id} | incident {memory.incident_id} | {memory.memory_type}")

    print("\nRecommendation ranking sample:")
    for recommendation in recommendations[:3]:
        print(
            f"- {recommendation.fix}: {recommendation.success_count} success, "
            f"{recommendation.failure_count} failure, "
            f"rate={recommendation.success_rate:.0%}, "
            f"similarity={recommendation.memory_similarity:.2f}, "
            f"score={recommendation.recommendation_score:.2f}, "
            f"confidence={recommendation.confidence_score:.1f}"
        )


if __name__ == "__main__":
    seed_demo_database()
    validation_passed = run_demo_validation()
    raise SystemExit(0 if validation_passed else 1)
