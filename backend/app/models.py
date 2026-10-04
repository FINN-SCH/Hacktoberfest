from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    native_language: str  # language code, e.g. "en", "de", "ar"
    default_explanation_mode: str = "native"  # "native" | "target"
    created_at: datetime = Field(default_factory=utcnow)


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id", index=True)
    # Settings are snapshots taken at session start; later profile edits never change them.
    target_language: str  # "de" | "en"
    explanation_language: str  # concrete language code resolved at start
    level: str  # "A1" | "A2" | "B1" | "B2"
    scenario: str  # see languages.SCENARIOS
    status: str = "active"  # "active" | "finalizing" | "ended"
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: Optional[datetime] = None

    # LLM snapshot generated at /end (vocabulary rating + summary). Deterministic scores are never stored.
    snapshot_status: str = "none"  # "none" | "ok" | "failed"
    snapshot_evidence_cutoff_at: Optional[datetime] = None  # captured BEFORE generation starts
    snapshot_generated_at: Optional[datetime] = None
    vocab_rating: Optional[int] = None
    vocab_evidence_json: Optional[str] = None
    summary_json: Optional[str] = None

    scoring_version: str = "v1"
    is_demo_data: bool = False


class Turn(SQLModel, table=True):
    __tablename__ = "turns"
    __table_args__ = (
        UniqueConstraint("session_id", "seq"),
        UniqueConstraint("session_id", "client_turn_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    seq: int  # 0 = tutor opening line
    kind: str = "learner"  # "opening" | "learner"
    client_turn_id: Optional[str] = None  # NULL for the opening turn

    # "processing" | "stt_failed" | "analysis_failed" | "done"
    correction_status: str = "processing"
    failure_code: Optional[str] = None

    audio_sha256: Optional[str] = None
    speech_span_ms: Optional[int] = None
    voiced_ms: Optional[int] = None
    pause_ms: Optional[int] = None

    transcript: Optional[str] = None  # owned by the backend (STT output), never rewritten by the LLM
    tutor_reply: Optional[str] = None
    spoken_correction_mistake_id: Optional[int] = None
    needs_clarification: bool = False

    misheard: bool = False
    misheard_at: Optional[datetime] = None

    stt_ms: Optional[int] = None
    llm_ms: Optional[int] = None
    llm_model: Optional[str] = None
    prompt_version: Optional[str] = None

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Mistake(SQLModel, table=True):
    __tablename__ = "mistakes"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id", index=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    turn_id: int = Field(foreign_key="turns.id", index=True)
    language: str
    topic: str
    kind: str  # "error" | "improvement"
    original: str  # the transcript's actual span, not the LLM's spelling
    corrected: str
    corrected_sentence: str
    explanation: str
    highlight_start: Optional[int] = None  # set only when `original` occurs exactly once
    highlight_end: Optional[int] = None
    llm_ref: str  # the correction id the LLM used, e.g. "c1"
    status: str = "active"  # "active" | "excluded"
    excluded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)


class Quiz(SQLModel, table=True):
    __tablename__ = "quizzes"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id", index=True)
    language: str
    questions_json: str  # immutable; includes answer keys and source mistake ids
    created_at: datetime = Field(default_factory=utcnow)


class QuizAttempt(SQLModel, table=True):
    __tablename__ = "quiz_attempts"

    id: Optional[int] = Field(default=None, primary_key=True)
    quiz_id: int = Field(foreign_key="quizzes.id", index=True)
    answers_json: str
    results_json: str  # per item: "correct" | "wrong" | "skipped_source_excluded"
    correct: int
    total: int  # excludes skipped items
    created_at: datetime = Field(default_factory=utcnow)


class ProfileAnalysis(SQLModel, table=True):
    __tablename__ = "profile_analyses"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id", index=True)
    language: str
    status: str  # "ok" | "failed"
    evidence_cutoff_at: datetime
    generated_at: datetime = Field(default_factory=utcnow)
    session_count: int
    content_json: Optional[str] = None
    error: Optional[str] = None
