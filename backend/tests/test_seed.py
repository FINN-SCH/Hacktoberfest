from datetime import timedelta
import pytest
from sqlmodel import SQLModel, Session as DBSession, select
from app.db import make_engine
from app.models import Profile, Session, Turn, Mistake, Quiz, QuizAttempt, ProfileAnalysis, utcnow
from app.seed import seed_demo, SeedError
from app.services.analysis import get_analysis
from app.services.reports import get_report
from app.services.validation import find_spans

@pytest.fixture
def db(tmp_path):
    engine = make_engine(str(tmp_path / "seed.db"))
    SQLModel.metadata.create_all(engine)
    with DBSession(engine) as db:
        yield db
    engine.dispose()

def test_seed_reports_analysis_and_refusal(db):
    profile = seed_demo(db)
    sessions = list(db.exec(select(Session)).all())
    assert len(sessions) == 4
    assert sorted(s.target_language for s in sessions) == ["de", "de", "de", "en"]
    assert all(s.is_demo_data and s.status == "ended" for s in sessions)
    for session in sessions:
        report = get_report(db, session.id)
        assert report.scores.sufficient_sample and report.vocab_rating is not None
        assert report.snapshot_status == "ok" and report.stale_exclusions == 0
        assert len(report.transcript) >= 6
    for m in db.exec(select(Mistake)).all():
        turn = db.get(Turn, m.turn_id)
        assert m.original in turn.transcript
        assert (m.highlight_start, m.highlight_end) in find_spans(turn.transcript, m.original)
    analysis = get_analysis(db, profile.id, "de")
    assert {x.topic for x in analysis.recurring} >= {"de_verb_second", "de_accusative"}
    assert "de_dative" in {x.topic for x in analysis.improving}
    assert analysis.written is not None and analysis.based_on_sessions == 3
    with pytest.raises(SeedError, match="already exists"):
        seed_demo(db)
    assert len(db.exec(select(Session)).all()) == 4

def test_reset_preserves_real_data_and_removes_demo_dependents(db):
    demo = seed_demo(db)
    normal = Profile(name="Real learner", native_language="en")
    db.add(normal); db.commit(); db.refresh(normal)
    real = Session(profile_id=normal.id, target_language="de", explanation_language="en", level="A2", scenario="cafe")
    db.add(real); db.commit(); db.refresh(real)
    processing = Turn(session_id=real.id, seq=1, client_turn_id="real", correction_status="processing")
    quiz = Quiz(profile_id=demo.id, language="de", questions_json="[]")
    db.add(processing); db.add(quiz); db.commit(); db.refresh(quiz)
    db.add(QuizAttempt(quiz_id=quiz.id, answers_json="{}", results_json="[]", correct=0, total=0)); db.commit()
    seed_demo(db, reset_demo=True)
    assert len(db.exec(select(Session).where(Session.is_demo_data == True)).all()) == 4
    assert db.get(Session, real.id).status == "active"
    assert db.get(Turn, processing.id).correction_status == "processing"
    assert db.exec(select(Quiz)).first() is None
    assert db.exec(select(QuizAttempt)).first() is None
    assert len(db.exec(select(ProfileAnalysis)).all()) == 1

def test_reset_refuses_real_sessions_under_demo_profile(db):
    demo = seed_demo(db)
    real = Session(profile_id=demo.id, target_language="en", explanation_language="en", level="B1", scenario="free_talk")
    db.add(real); db.commit()
    with pytest.raises(SeedError, match="non-demo sessions"):
        seed_demo(db, reset_demo=True)
    assert len(db.exec(select(Session)).all()) == 5

def test_seed_refuses_name_collision_without_deleting_profile(db):
    profile = Profile(name="Demo learner", native_language="de")
    db.add(profile); db.commit()
    with pytest.raises(SeedError, match="reserved"):
        seed_demo(db, reset_demo=True)
    assert db.get(Profile, profile.id).native_language == "de"
