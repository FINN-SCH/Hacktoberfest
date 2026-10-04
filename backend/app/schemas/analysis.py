from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .reports import SessionHistoryOut

class Strength(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1)
    evidence: str = Field(min_length=1)

class FocusArea(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    topic: str
    why: str = Field(min_length=1)
    tip: str = Field(min_length=1)
    example_mistake_ids: list[int] = Field(min_length=1)

class WrittenAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    summary: str = Field(min_length=1)
    strengths: list[Strength]
    focus_areas: list[FocusArea] = Field(max_length=3)

class TopicFrequency(BaseModel):
    topic: str
    label: str
    errors: int
    share: float
    sessions: int
    last_seen: datetime

class RecurringExample(BaseModel):
    original: str
    corrected: str
    count: int

class RecurringTopic(BaseModel):
    topic: str
    label: str
    sessions: int
    errors: int
    examples: list[RecurringExample]

class ImprovingTopic(BaseModel):
    topic: str
    label: str

class AnalysisOut(BaseModel):
    profile_id: int
    language: str
    session_count: int
    topic_frequency: list[TopicFrequency]
    progress: list[SessionHistoryOut]
    recurring: list[RecurringTopic]
    improving: list[ImprovingTopic]
    written: WrittenAnalysis | None
    based_on_sessions: int | None
    generated_at: datetime | None
    stale_exclusions: int
    latest_attempt_failed: bool
