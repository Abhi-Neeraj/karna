"""Pydantic schema for the KARNA Memory Inspector experience."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryInspectorResponse(BaseModel):
    """Inspectable memory evidence and outcome-aware recommendation ranking."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: int = Field(
        ...,
        gt=0,
        description="Identifier of the incident whose memory evidence is displayed.",
        examples=[42],
    )
    recalled_memories: list[dict[str, Any]] = Field(
        ...,
        description="Historical memory records recalled for the analyzed incident.",
        examples=[[{"memory_id": 15, "source_incident_id": 34}]],
    )
    similarity_scores: dict[int, float] = Field(
        ...,
        description="Similarity score by recalled memory identifier, expressed from 0 to 100.",
        examples=[{"15": 92.0}],
    )
    recommended_fixes: list[dict[str, Any]] = Field(
        ...,
        description="Ranked fixes and their outcome-aware recommendation contributions.",
        examples=[[{"fix": "Patch connection leak", "rank": 1}]],
    )
    success_rates: dict[str, float] = Field(
        ...,
        description="Historical success rate by fix name, expressed from 0 to 1.",
        examples=[{"Patch connection leak": 1.0}],
    )
    evidence: list[dict[str, Any]] = Field(
        ...,
        description="Detailed provenance and ranking rationale for displayed recommendations.",
        examples=[[{"memory_id": 15, "outcome": "success", "contribution": 0.92}]],
    )
