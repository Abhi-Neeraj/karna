"""Pydantic schemas for incident outcome learning."""

from pydantic import BaseModel, ConfigDict, Field


class OutcomeCreateRequest(BaseModel):
    """Validated final-fix outcome submitted by an engineer."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    incident_id: int = Field(
        ...,
        gt=0,
        description="Identifier of the incident whose outcome is being recorded.",
        examples=[42],
    )
    fix_applied: str = Field(
        ...,
        min_length=3,
        max_length=10_000,
        description="The final remediation action actually applied by the engineer.",
        examples=["Patched the connection leak and increased pool capacity."],
    )
    success: bool = Field(
        ...,
        description="Whether the applied fix resolved the incident.",
        examples=[True],
    )
    notes: str | None = Field(
        default=None,
        max_length=10_000,
        description="Optional operational observations about the result.",
        examples=["Error rate returned to baseline within five minutes."],
    )


class OutcomeResponse(BaseModel):
    """Confirmation returned after an outcome updates KARNA learning."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        gt=0,
        description="Persistent identifier of the newly stored outcome.",
        examples=[108],
    )
    incident_id: int = Field(
        ...,
        gt=0,
        description="Identifier of the incident associated with this outcome.",
        examples=[42],
    )
    success: bool = Field(
        ...,
        description="Recorded success or failure state of the applied fix.",
        examples=[True],
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Human-readable confirmation of the learning update.",
        examples=["Outcome stored and fix statistics updated."],
    )
