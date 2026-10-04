"""Strict schema for the per-turn tutor LLM output (PLAN.md section 3). The transcript is NOT part of it."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class LLMCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=16)
    original: str = Field(min_length=1)
    corrected: str = Field(min_length=1)
    corrected_sentence: str = Field(min_length=1)
    kind: Literal["error", "improvement"]
    topic: str
    explanation: str = Field(min_length=1)


class TurnAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corrections: list[LLMCorrection]
    spoken_correction_id: Optional[str]
    needs_clarification: bool
    reply: str = Field(min_length=1)


def turn_analysis_json_schema(topics: list[str]) -> dict:
    """JSON schema for strict `json_schema` mode: every property required, no extra properties."""
    correction = {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "original", "corrected", "corrected_sentence", "kind", "topic", "explanation"],
        "properties": {
            "id": {"type": "string"},
            "original": {"type": "string"},
            "corrected": {"type": "string"},
            "corrected_sentence": {"type": "string"},
            "kind": {"type": "string", "enum": ["error", "improvement"]},
            "topic": {"type": "string", "enum": topics},
            "explanation": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["corrections", "spoken_correction_id", "needs_clarification", "reply"],
        "properties": {
            "corrections": {"type": "array", "items": correction},
            "spoken_correction_id": {"type": ["string", "null"]},
            "needs_clarification": {"type": "boolean"},
            "reply": {"type": "string"},
        },
    }
