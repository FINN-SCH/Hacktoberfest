"""Learner-driven exclusions. Idempotent; their timestamps drive staleness labels."""

from __future__ import annotations

from sqlmodel import Session as DBSession

from ..models import Mistake, Turn, utcnow
from ..schemas.api import CorrectionOut, TurnOut
from .errors import ApiError
from .turns import correction_out, turn_out


def mark_misheard(db: DBSession, turn_id: int) -> TurnOut:
    t = db.get(Turn, turn_id)
    if t is None:
        raise ApiError(404, "turn_not_found", "Turn not found.")
    if t.kind != "learner":
        raise ApiError(400, "not_a_learner_turn", "Only learner turns can be marked as misheard.")
    if not t.misheard:
        t.misheard = True
        t.misheard_at = utcnow()
        db.add(t)
        db.commit()
        db.refresh(t)
    return turn_out(db, t)


def mark_not_a_mistake(db: DBSession, mistake_id: int) -> CorrectionOut:
    m = db.get(Mistake, mistake_id)
    if m is None:
        raise ApiError(404, "mistake_not_found", "Correction not found.")
    if m.status != "excluded":
        m.status = "excluded"
        m.excluded_at = utcnow()
        db.add(m)
        db.commit()
        db.refresh(m)
    return correction_out(m)
