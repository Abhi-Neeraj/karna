"""Explainable memory-inspector route for KARNA recommendations."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.memory.sqlite_memory_provider import SQLiteMemoryProvider
from app.repositories.incident_repository import IncidentRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.outcome_repository import OutcomeRepository
from app.services.incident_analysis_service import IncidentAnalysisService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/memory-inspector", tags=["Memory Inspector"])


class MemoryInspectorResponse(BaseModel):
    """Traceable evidence explaining one incident recommendation run."""

    incident: dict[str, object] = Field(description="Incident context under review.")
    recalled_memories: list[dict[str, object]] = Field(
        description="Relevant incident memories and lexical match evidence."
    )
    matched_symptoms: list[str] = Field(
        description="Symptoms extracted from the inspected incident."
    )
    recommended_fixes: list[dict[str, object]] = Field(
        description="Outcome-and-memory-ranked remediation options."
    )
    ranking_reason: list[str] = Field(
        description="Human-readable rationale for each ranked fix."
    )
    confidence_breakdown: dict[str, float] = Field(
        description="Leading-fix outcome, similarity, score, and confidence signals."
    )


@router.get("/{incident_id}", response_model=MemoryInspectorResponse)
def inspect_memory(
    incident_id: int,
    database_session: Session = Depends(get_db),
) -> MemoryInspectorResponse:
    """Show exactly which historical evidence influenced an incident's guidance."""
    incident_repository = IncidentRepository(database_session)
    incident = incident_repository.get_by_id(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found.")

    memory_provider = SQLiteMemoryProvider(MemoryRepository(database_session))
    analysis = IncidentAnalysisService().analyze(
        title=incident.title,
        description=incident.description,
    )
    result = RecommendationService(
        memory_provider=memory_provider,
        outcome_repository=OutcomeRepository(database_session),
    ).generate_recommendations(
        query=analysis.summary,
        keywords=analysis.keywords,
        memory_enabled=True,
        limit=5,
    )
    fixes = [
        {
            "fix": item.fix,
            "success_count": item.success_count,
            "failure_count": item.failure_count,
            "success_rate": item.success_rate,
            "memory_similarity": item.memory_similarity,
            "recommendation_score": item.recommendation_score,
            "confidence_score": item.confidence_score,
            "evidence_incidents": item.evidence_incidents,
        }
        for item in result.recommendations
    ]
    leading = result.recommendations[0] if result.recommendations else None
    return MemoryInspectorResponse(
        incident={
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "root_cause": incident.root_cause,
        },
        recalled_memories=[
            {
                "memory_id": item.memory.id,
                "incident_id": item.memory.incident_id,
                "similarity_score": item.similarity_score,
                "matched_terms": item.matched_terms,
                "content": item.memory.content,
            }
            for item in result.recalled_memories
        ],
        matched_symptoms=analysis.symptoms,
        recommended_fixes=fixes,
        ranking_reason=[
            (
                f"{item.fix}: success rate {item.success_rate:.0%} × 0.7 + "
                f"memory similarity {item.memory_similarity:.0%} × 0.3 = "
                f"{item.recommendation_score:.2f}."
            )
            for item in result.recommendations
        ],
        confidence_breakdown=(
            {
                "success_rate": leading.success_rate,
                "memory_similarity": leading.memory_similarity,
                "recommendation_score": leading.recommendation_score,
                "confidence_score": leading.confidence_score,
            }
            if leading
            else {}
        ),
    )
