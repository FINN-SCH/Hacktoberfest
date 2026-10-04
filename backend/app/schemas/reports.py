from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .api import SessionOut, SessionScores, TurnOut

class EvidenceQuote(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    turn_id: int
    quote: str = Field(min_length=1)
    explanation: str = Field(min_length=1)

class ReportSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    weaknesses: list[str]
    next_focus: str = Field(min_length=1)

class ReportGeneration(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    vocab_rating: int | None = Field(ge=1, le=5)
    vocab_evidence: list[EvidenceQuote]
    summary: ReportSummary

class ReportOut(BaseModel):
    session: SessionOut
    transcript: list[TurnOut]
    scores: SessionScores
    snapshot_status: str
    vocab_rating: int | None
    vocab_evidence: list[EvidenceQuote]
    summary: ReportSummary | None
    snapshot_generated_at: datetime | None
    stale_exclusions: int

class SessionHistoryOut(SessionOut):
    scores: SessionScores
    vocab_rating: int | None
    stale_exclusions: int
