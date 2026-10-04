"""Single definition of which turns and mistakes count as evidence (PLAN.md section 6).

Scoring, reports, quizzes and the Analysis tab must all go through these functions.
"""

from __future__ import annotations

import unicodedata
from typing import Optional

from sqlmodel import Session as DBSession
from sqlmodel import select

from ..models import Mistake, Session, Turn

MIN_ELIGIBLE_WORDS = 3


def _strip_punct(token: str) -> str:
    start, end = 0, len(token)
    while start < end and unicodedata.category(token[start]).startswith("P"):
        start += 1
    while end > start and unicodedata.category(token[end - 1]).startswith("P"):
        end -= 1
    return token[start:end]


def count_words(text: Optional[str]) -> int:
    """Whitespace tokens with surrounding punctuation trimmed; internal ' and - are kept."""
    if not text:
        return 0
    return sum(1 for tok in text.split() if _strip_punct(tok))


def is_eligible(turn: Turn) -> bool:
    return (
        turn.kind == "learner"
        and turn.correction_status == "done"
        and not turn.misheard
        and not turn.needs_clarification
        and count_words(turn.transcript) >= MIN_ELIGIBLE_WORDS
    )


def _sessions_query(profile_id: Optional[int], language: Optional[str], ended_only: bool):
    q = select(Session.id)
    if profile_id is not None:
        q = q.where(Session.profile_id == profile_id)
    if language is not None:
        q = q.where(Session.target_language == language)
    if ended_only:
        q = q.where(Session.status == "ended")
    return q


def learner_turns(
    db: DBSession,
    *,
    session_id: Optional[int] = None,
    profile_id: Optional[int] = None,
    language: Optional[str] = None,
    ended_only: bool = False,
) -> list[Turn]:
    q = select(Turn).where(Turn.kind == "learner")
    if session_id is not None:
        q = q.where(Turn.session_id == session_id)
    if profile_id is not None or language is not None or ended_only:
        q = q.where(Turn.session_id.in_(_sessions_query(profile_id, language, ended_only)))
    return list(db.exec(q.order_by(Turn.session_id, Turn.seq)).all())


def eligible_turns(db: DBSession, **filters) -> list[Turn]:
    return [t for t in learner_turns(db, **filters) if is_eligible(t)]


def active_errors(db: DBSession, **filters) -> list[Mistake]:
    """Active kind=error mistakes that belong to eligible turns, oldest first."""
    turns = {t.id: t for t in eligible_turns(db, **filters)}
    if not turns:
        return []
    q = (
        select(Mistake)
        .where(Mistake.turn_id.in_(list(turns)))
        .where(Mistake.status == "active")
        .where(Mistake.kind == "error")
        .order_by(Mistake.created_at, Mistake.id)
    )
    return list(db.exec(q).all())


def is_mistake_eligible(db: DBSession, mistake_id: int, profile_id: int, language: str) -> bool:
    """Used by quizzes right before delivery and again at grading."""
    m = db.get(Mistake, mistake_id)
    if m is None or m.status != "active" or m.kind != "error":
        return False
    if m.profile_id != profile_id or m.language != language:
        return False
    turn = db.get(Turn, m.turn_id)
    return turn is not None and is_eligible(turn)
