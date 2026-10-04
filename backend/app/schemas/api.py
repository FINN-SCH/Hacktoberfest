"""Public API schemas owned by Claude: profiles, sessions, turns, corrections, scores, errors.

Report / quiz / analysis response schemas live in their own modules next to these.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

TargetLanguage = Literal["de", "en"]
Level = Literal["A1", "A2", "B1", "B2"]
Scenario = Literal["cafe", "job_interview", "doctor", "free_talk"]
ExplanationMode = Literal["native", "target"]
CorrectionStatus = Literal["processing", "stt_failed", "analysis_failed", "done"]


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    native_language: str = Field(min_length=2, max_length=8)
    default_explanation_mode: ExplanationMode = "native"


class ProfileOut(BaseModel):
    id: int
    name: str
    native_language: str
    default_explanation_mode: ExplanationMode
    created_at: datetime


class SessionCreate(BaseModel):
    profile_id: int
    target_language: TargetLanguage
    explanation_mode: ExplanationMode
    level: Level
    scenario: Scenario


class SessionOut(BaseModel):
    id: int
    profile_id: int
    target_language: TargetLanguage
    explanation_language: str
    level: Level
    scenario: Scenario
    status: Literal["active", "finalizing", "ended"]
    started_at: datetime
    ended_at: Optional[datetime]
    is_demo_data: bool


class SessionStartOut(BaseModel):
    session: SessionOut
    opening_turn_id: int  # speak it via POST /api/turns/{id}/speech
    opening_text: str


class CorrectionOut(BaseModel):
    id: int
    original: str
    corrected: str
    corrected_sentence: str
    kind: Literal["error", "improvement"]
    topic: str
    topic_label: str
    explanation: str
    highlight_start: Optional[int]
    highlight_end: Optional[int]
    status: Literal["active", "excluded"]


class TurnOut(BaseModel):
    turn_id: int
    session_id: int
    seq: int
    kind: Literal["opening", "learner"]
    client_turn_id: Optional[str]
    correction_status: CorrectionStatus
    failure_code: Optional[str]
    transcript: Optional[str]
    needs_clarification: bool
    misheard: bool
    corrections: list[CorrectionOut]
    spoken_correction_id: Optional[int]  # a CorrectionOut.id
    reply: Optional[str]


class ErrorBody(BaseModel):
    code: str
    message: str
    stage: Optional[Literal["stt", "analysis", "tts", "request"]] = None
    retryable: bool = False
    turn_id: Optional[int] = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class GrammarScore(BaseModel):
    rating: Optional[int]  # None when the sample is insufficient
    error_free_turn_pct: Optional[float]
    errors_per_100_words: Optional[float]
    error_count: int
    eligible_turns: int


class FluencyScore(BaseModel):
    rating: Optional[int]
    wpm: Optional[float]
    pause_ratio: Optional[float]
    heuristic_version: str


class SessionScores(BaseModel):
    sufficient_sample: bool
    insufficient_reason: Optional[str]
    eligible_turns: int
    assessed_turns: int  # learner turns whose analysis completed
    learner_turns: int  # all learner turns (coverage = assessed / learner)
    eligible_words: int
    eligible_voiced_ms: int
    grammar: GrammarScore
    fluency: FluencyScore
    scoring_version: str
