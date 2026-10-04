from datetime import datetime, timezone

import pytest
from sqlmodel import Session as DBSession

from app.db import init_db, make_engine
from app.models import Mistake, Profile, Session, Turn
from app.services.eligibility import active_errors, count_words, eligible_turns, is_mistake_eligible
from app.services.scoring import compute_scores, fluency_rating, grammar_rating, session_scores


def turn(i, text="ich gehe heute nach Hause", status="done", voiced=15_000, span=18_000, **kw):
    return Turn(
        id=i, session_id=1, seq=i, kind="learner", client_turn_id=f"c{i}", correction_status=status,
        transcript=text, voiced_ms=voiced, speech_span_ms=span, pause_ms=span - voiced, **kw,
    )


def test_count_words_trims_punctuation_keeps_internal():
    assert count_words("Hello, I'm well-known ... ok!") == 4
    assert count_words("") == 0 and count_words(None) == 0


@pytest.mark.parametrize("pct,band", [(100, 5), (90, 5), (89.9, 4), (75, 4), (55, 3), (35, 2), (34.9, 1), (0, 1)])
def test_grammar_bands(pct, band):
    assert grammar_rating(pct) == band


def test_fluency_speed_not_rewarded_and_pauses_cap():
    assert fluency_rating(80, 0.2, "A2") == 5
    assert fluency_rating(200, 0.2, "A2") == 1  # far too fast is not better
    assert fluency_rating(120, 0.2, "A2") == 3  # 10 over
    assert fluency_rating(80, 0.85, "A2") == 1  # severe pauses cap the rating
    assert fluency_rating(80, 0.55, "A2") == 3


def test_insufficient_sample_has_no_ratings_but_keeps_evidence():
    turns = [turn(i) for i in range(1, 5)]
    s = compute_scores(turns, {}, "A2")
    assert not s.sufficient_sample and s.grammar.rating is None and s.fluency.rating is None
    assert s.grammar.error_free_turn_pct == 100.0 and s.insufficient_reason


def test_failed_and_excluded_turns_never_count_as_error_free():
    turns = [turn(i) for i in range(1, 6)] + [
        turn(6, status="analysis_failed"),
        turn(7, misheard=True),
        turn(8, needs_clarification=True),
        turn(9, text="ja bitte"),  # < 3 words
    ]
    s = compute_scores(turns, {1: 2, 2: 1}, "A2")
    assert s.eligible_turns == 5 and s.learner_turns == 9 and s.assessed_turns == 8
    assert s.grammar.error_free_turn_pct == 60.0 and s.grammar.rating == 3
    assert s.grammar.error_count == 3
    assert s.grammar.errors_per_100_words == round(100 * 3 / 25, 1)
    assert s.sufficient_sample  # 5 turns x 15 s = 75 s


def test_session_wpm_and_pause_from_sums():
    turns = [turn(i, voiced=12_000, span=16_000) for i in range(1, 6)]
    s = compute_scores(turns, {}, "B1")
    assert s.fluency.wpm == round(25 / (60_000 / 60_000), 1)
    assert s.fluency.pause_ratio == 0.25


@pytest.fixture
def db():
    engine = make_engine(":memory:")
    init_db(engine)
    with DBSession(engine) as session:
        yield session


def test_exclusions_propagate_through_eligibility(db):
    p = Profile(name="A", native_language="en")
    db.add(p)
    db.commit()
    s = Session(profile_id=p.id, target_language="de", explanation_language="en", level="A2", scenario="cafe")
    db.add(s)
    db.commit()
    turns = []
    for i in range(1, 6):
        t = Turn(session_id=s.id, seq=i, client_turn_id=f"c{i}", correction_status="done",
                 transcript="ich habe nach Berlin gegangen", voiced_ms=15_000, speech_span_ms=18_000, pause_ms=3_000)
        db.add(t)
        turns.append(t)
    db.commit()
    mistakes = []
    for t in turns[:2]:
        m = Mistake(profile_id=p.id, session_id=s.id, turn_id=t.id, language="de", topic="de_perfekt_auxiliary",
                    kind="error", original="habe", corrected="bin", corrected_sentence="ich bin", explanation="x",
                    llm_ref="c1")
        db.add(m)
        mistakes.append(m)
    db.commit()

    assert session_scores(db, s).grammar.error_free_turn_pct == 60.0
    assert len(active_errors(db, profile_id=p.id, language="de")) == 2

    mistakes[0].status = "excluded"
    mistakes[0].excluded_at = datetime.now(timezone.utc)
    turns[1].misheard = True
    db.add_all([mistakes[0], turns[1]])
    db.commit()

    assert len(eligible_turns(db, session_id=s.id)) == 4
    assert active_errors(db, session_id=s.id) == []
    assert session_scores(db, s).grammar.error_free_turn_pct == 100.0
    assert not is_mistake_eligible(db, mistakes[0].id, p.id, "de")
    assert not is_mistake_eligible(db, mistakes[1].id, p.id, "de")  # its turn is misheard
