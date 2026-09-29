"""Pydantic schemas for engineer correction learning events."""

from pydantic import BaseModel, ConfigDict, Field


class CorrectionCreateRequest(BaseModel):
    """Validated root-cause correction submitted by an engineer."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    incident_id: int = Field(
        ...,
        gt=0,
        description="Identifier of the incident receiving the correction.",
        examples=[42],
    )
    original_root_cause: str | None = Field(
        default=None,
        max_length=10_000,
        description="The prior root-cause assessment being corrected, when available.",
        examples=["Database overload"],
    )
    corrected_root_cause: str = Field(
        ...,
        min_length=3,
        max_length=10_000,
        description="Engineer-validated root cause that should inform future recall.",
        examples=["Connection leak"],
    )
    reason: str = Field(
        ...,
        min_length=3,
        max_length=10_000,
        description="Evidence or rationale supporting the corrected diagnosis.",
        examples=["Leaked sessions accumulated until the connection pool was exhausted."],
    )


class CorrectionResponse(BaseModel):
    """Confirmation returned after a correction is stored as organizational memory."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        gt=0,
        description="Persistent identifier of the stored correction.",
        examples=[21],
    )
    incident_id: int = Field(
        ...,
        gt=0,
        description="Identifier of the incident associated with this correction.",
        examples=[42],
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Human-readable confirmation of the correction learning update.",
        examples=["Correction stored and added to operational memory."],
    )
