"""Pydantic schema for KARNA learning analytics."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsResponse(BaseModel):
    """Aggregate metrics describing KARNA memory and learning activity."""

    model_config = ConfigDict(from_attributes=True)

    total_incidents: int = Field(
        ...,
        ge=0,
        description="Total number of incident records stored by KARNA.",
        examples=[120],
    )
    total_corrections: int = Field(
        ...,
        ge=0,
        description="Total number of engineer correction learning events.",
        examples=[18],
    )
    memory_count: int = Field(
        ...,
        ge=0,
        description="Total number of retrievable operational memory records.",
        examples=[246],
    )
    top_successful_fixes: list[dict[str, Any]] = Field(
        ...,
        description="Fixes ranked by accumulated successful outcomes.",
        examples=[[{"fix_name": "Patch connection leak", "success_count": 7}]],
    )
    top_failed_fixes: list[dict[str, Any]] = Field(
        ...,
        description="Fixes ranked by accumulated failed outcomes.",
        examples=[[{"fix_name": "Restart connection pool", "failure_count": 5}]],
    )
