"""Deterministic grammar + fluency ratings, computed on read (PLAN.md section 6). Never stored."""

from __future__ import annotations

from collections import Counter
from typing import Optional

from sqlmodel import Session as DBSession

from ..models import Session, Turn
from ..schemas.api import FluencyScore, GrammarScore, SessionScores
from .eligibility import active_errors, count_words, is_eligible, learner_turns

SCORING_VERSION = "v1"
FLUENCY_HEURISTIC_VERSION = "fluency-v1"

MIN_ELIGIBLE_TURNS = 5
MIN_VOICED_MS = 60_000

IDEAL_WPM: dict[str, tuple[float, float]] = {
    "A1": (50, 110),
    "A2": (50, 110),
    "B1": (70, 140),
    "B2": (70, 140),
}


def grammar_rating(error_free_pct: float) -> int:
    if error_free_pct >= 90:
        return 5
    if error_free_pct >= 75:
        return 4
    if error_free_pct >= 55:
        return 3
    if error_free_pct >= 35:
        return 2
    return 1


def fluency_rating(wpm: float, pause_ratio: float, level: str) -> int:
    """Heuristic: speed outside the level's ideal band is penalised in both directions, and long
    pauses cap the rating. Not a validated proficiency measure."""
    low, high = IDEAL_WPM[level]
    d = max(low - wpm, wpm - high, 0)
    if d == 0:
        rate_score = 5
    elif d <= 20:
        rate_score = 3
    elif d <= 40:
        rate_score = 2
    else:
        rate_score = 1

    if pause_ratio < 0.35:
        pause_cap = 5
    elif pause_ratio < 0.50:
        pause_cap = 4
    elif pause_ratio < 0.65:
        pause_cap = 3
    elif pause_ratio < 0.80:
        pause_cap = 2
    else:
        pause_cap = 1
    return min(rate_score, pause_cap)


def compute_scores(turns: list[Turn], errors_per_turn: dict[int, int], level: str) -> SessionScores:
    """Pure core. `turns` = all learner turns of the session; `errors_per_turn` = active error
    counts keyed by turn id (only eligible turns are consulted)."""
    learner = [t for t in turns if t.kind == "learner"]
    assessed = [t for t in learner if t.correction_status == "done"]
    eligible = [t for t in learner if is_eligible(t)]

    words = sum(count_words(t.transcript) for t in eligible)
    voiced_ms = sum(t.voiced_ms or 0 for t in eligible)
    span_ms = sum(t.speech_span_ms or 0 for t in eligible)
    pause_ms = sum(t.pause_ms or 0 for t in eligible)
    error_count = sum(errors_per_turn.get(t.id, 0) for t in eligible)
    error_free = sum(1 for t in eligible if errors_per_turn.get(t.id, 0) == 0)

    sufficient = len(eligible) >= MIN_ELIGIBLE_TURNS and voiced_ms >= MIN_VOICED_MS
    reason: Optional[str] = None
    if not sufficient:
        reason = (
            f"Not enough speech yet: {len(eligible)}/{MIN_ELIGIBLE_TURNS} assessed turns and "
            f"{voiced_ms // 1000}/{MIN_VOICED_MS // 1000} s of speech."
        )

    error_free_pct = round(100 * error_free / len(eligible), 1) if eligible else None
    errors_per_100 = round(100 * error_count / words, 1) if words else None
    wpm = round(words / (voiced_ms / 60_000), 1) if voiced_ms else None
    pause_ratio = round(pause_ms / span_ms, 3) if span_ms else None

    grammar = GrammarScore(
        rating=grammar_rating(error_free_pct) if sufficient and error_free_pct is not None else None,
        error_free_turn_pct=error_free_pct,
        errors_per_100_words=errors_per_100,
        error_count=error_count,
        eligible_turns=len(eligible),
    )
    fluency = FluencyScore(
        rating=fluency_rating(wpm, pause_ratio, level)
        if sufficient and wpm is not None and pause_ratio is not None
        else None,
        wpm=wpm,
        pause_ratio=pause_ratio,
        heuristic_version=FLUENCY_HEURISTIC_VERSION,
    )
    return SessionScores(
        sufficient_sample=sufficient,
        insufficient_reason=reason,
        eligible_turns=len(eligible),
        assessed_turns=len(assessed),
        learner_turns=len(learner),
        eligible_words=words,
        eligible_voiced_ms=voiced_ms,
        grammar=grammar,
        fluency=fluency,
        scoring_version=SCORING_VERSION,
    )


def session_scores(db: DBSession, session: Session) -> SessionScores:
    turns = learner_turns(db, session_id=session.id)
    errors = Counter(m.turn_id for m in active_errors(db, session_id=session.id))
    return compute_scores(turns, dict(errors), session.level)
