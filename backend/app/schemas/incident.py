"""Pydantic schemas for incident analysis requests and responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IncidentAnalyzeRequest(BaseModel):
    """Validated incident context submitted for KARNA analysis."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Concise title describing the operational incident.",
        examples=["Database Connection Pool Exhausted"],
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=10_000,
        description="Detailed symptoms and relevant incident context.",
        examples=["Checkout requests fail because the primary database pool is exhausted."],
    )
    service_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Optional affected service or component name.",
        examples=["checkout-api"],
    )
    severity: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="Optional incident severity label.",
        examples=["SEV-2"],
    )


class IncidentResponse(BaseModel):
    """Evidence-backed recommendation returned after incident analysis."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: int = Field(
        ...,
        gt=0,
        description="Persistent identifier of the analyzed incident.",
        examples=[42],
    )
    recommended_fixes: list[dict[str, Any]] = Field(
        ...,
        description="Ranked candidate fixes with supporting recommendation details.",
        examples=[[{"fix": "Patch connection leak", "rank": 1}]],
    )
    confidence_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Evidence-derived confidence score for the leading recommendation.",
        examples=[92.5],
    )
    similar_incidents: list[dict[str, Any]] = Field(
        ...,
        description="Historical incidents recalled as relevant evidence.",
        examples=[[{"incident_id": 34, "similarity_score": 92.0}]],
    )
    evidence: list[dict[str, Any]] = Field(
        ...,
        description="Inspectable memory and outcome evidence behind recommendation ranking.",
        examples=[[{"memory_id": 15, "outcome": "success"}]],
    )
