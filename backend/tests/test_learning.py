import json
from datetime import timedelta
from types import SimpleNamespace
import pytest
from sqlmodel import Session as DBSession, select
from app.db import init_db, make_engine
from app.models import Profile, Session, Turn, Mistake, ProfileAnalysis, utcnow
from app.providers.interfaces import CompletionResult
from app.services import reports, quizzes, analysis
from app.services.errors import ApiError
from app.schemas.quizzes import QuizAnswers

class FakeLLM:
    def __init__(self, output, callback=None):
        self.output, self.callback, self.calls = output, callback, 0
    async def complete(self, messages, *, schema, purpose):
        self.calls += 1
        if self.callback:
            self.callback()
        value = self.output[purpose] if isinstance(self.output, dict) and purpose in self.output else self.output
        return CompletionResult(value if isinstance(value,str) else json.dumps(value), "fake", "fake", 1)

@pytest.fixture
def db(tmp_path):
    engine=make_engine(str(tmp_path/"test.db")); init_db(engine)
    with DBSession(engine) as db:
        yield db
    engine.dispose()

def evidence(db, *, ended=False, profile=None, language="de", words="Ich habe nach Berlin gegangen."):
    if profile is None:
        profile=Profile(name="Learner",native_language="en");db.add(profile);db.commit();db.refresh(profile)
    session=Session(profile_id=profile.id,target_language=language,explanation_language="en",level="A2",scenario="cafe",
                    status="ended" if ended else "active", ended_at=utcnow() if ended else None)
    db.add(session);db.commit();db.refresh(session)
    for i in range(1,6):
        turn=Turn(session_id=session.id,seq=i,client_turn_id=f"turn-{i}",correction_status="done",
                  transcript=words,voiced_ms=12000,speech_span_ms=15000,pause_ms=3000)
        db.add(turn)
    db.commit()
    turn=db.exec(select(Turn).where(Turn.session_id==session.id)).first()
    mistake=Mistake(profile_id=profile.id,session_id=session.id,turn_id=turn.id,language=language,
        topic="de_perfekt_auxiliary" if language=="de" else "en_other",kind="error",original="habe",corrected="bin",
        corrected_sentence="Ich bin nach Berlin gegangen.",explanation="Use sein",llm_ref="c1")
    db.add(mistake);db.commit();db.refresh(mistake)
    return profile,session,turn,mistake

def report_output(turn):
    return {"vocab_rating":3,"vocab_evidence":[{"turn_id":turn.id,"quote":"Berlin","explanation":"A place name"}],
            "summary":{"weaknesses":["Auxiliary choice"],"next_focus":"Practise sein."}}

@pytest.mark.asyncio
async def test_end_idempotent_and_exclusion_stales(db):
    p,s,t,m=evidence(db)
    llm=FakeLLM(report_output(t)); bundle=SimpleNamespace(llm=llm)
    result=await reports.end_session(db,bundle,s.id)
    assert result.snapshot_status=="ok" and result.scores.sufficient_sample
    await reports.end_session(db,bundle,s.id)
    assert llm.calls==1
    m.status="excluded";m.excluded_at=utcnow()+timedelta(seconds=1);db.add(m);db.commit()
    updated=reports.get_report(db,s.id)
    assert updated.stale_exclusions==1 and updated.scores.grammar.error_count==0

@pytest.mark.asyncio
async def test_end_rejects_processing_and_invalid_generation_repairs_once(db):
    p,s,t,m=evidence(db)
    t.correction_status="processing";db.add(t);db.commit()
    llm=FakeLLM("not json")
    with pytest.raises(ApiError) as e:
        await reports.end_session(db,SimpleNamespace(llm=llm),s.id)
    assert e.value.status==409 and llm.calls==0
    t.correction_status="done";db.add(t);db.commit()
    result=await reports.end_session(db,SimpleNamespace(llm=llm),s.id)
    assert result.snapshot_status=="failed" and result.session.status=="ended" and llm.calls==2

def quiz_output(m,answer="Stra\u00dfe"):
    return {"questions":[{"id":"q1","source_mistake_id":m.id,"kind":"fill_in",
      "question":"Die ___ ist lang.","options":[],"correct_option_id":None,
      "accepted_answers":[answer],"explanation":"Keep the correct spelling.","ambiguous":False}]}

@pytest.mark.asyncio
async def test_quiz_keeps_keys_private_and_rechecks_at_grade(db):
    p,s,t,m=evidence(db)
    q=await quizzes.create_quiz(db,SimpleNamespace(llm=FakeLLM(quiz_output(m))),p.id,"de")
    assert "accepted_answers" not in q.model_dump_json() and "correct_option_id" not in q.model_dump_json()
    good=quizzes.grade(db,q.id,QuizAnswers(answers={"q1":"  Stra\u00dfe  "}))
    assert (good.correct,good.total)==(1,1)
    wrong=quizzes.grade(db,q.id,QuizAnswers(answers={"q1":"Strasse"}))
    assert wrong.correct==0
    m.status="excluded";m.excluded_at=utcnow();db.add(m);db.commit()
    result=quizzes.grade(db,q.id,QuizAnswers(answers={"q1":"Stra\u00dfe"}))
    assert result.total==0 and result.results[0].status=="skipped_source_excluded"

@pytest.mark.asyncio
async def test_quiz_unicode_and_profile_isolation(db):
    p,s,t,m=evidence(db)
    q=await quizzes.create_quiz(db,SimpleNamespace(llm=FakeLLM(quiz_output(m,"H\u00e4user"))),p.id,"de")
    assert quizzes.grade(db,q.id,QuizAnswers(answers={"q1":"Ha\u0308user"})).correct==1
    assert quizzes.grade(db,q.id,QuizAnswers(answers={"q1":"h\u00e4user"})).correct==0
    with pytest.raises(ApiError):
        await quizzes.create_quiz(db,SimpleNamespace(llm=FakeLLM({})),p.id,"en")

@pytest.mark.asyncio
async def test_analysis_unlock_and_one_repair(db):
    p,s,t,m=evidence(db,ended=True)
    llm=FakeLLM("invalid")
    await analysis.generate_analysis(db,SimpleNamespace(llm=llm),p.id,"de")
    assert llm.calls==0 and analysis.get_analysis(db,p.id,"de").session_count==1
    evidence(db,ended=True,profile=p)
    await analysis.generate_analysis(db,SimpleNamespace(llm=llm),p.id,"de")
    out=analysis.get_analysis(db,p.id,"de")
    assert out.latest_attempt_failed and out.written is None and llm.calls==2
    assert len(out.recurring)==1 and out.recurring[0].sessions==2

@pytest.mark.asyncio
async def test_report_quotes_reject_invented_evidence_and_insufficient_vocab(db):
    p,s,t,m=evidence(db)
    output=report_output(t);output["vocab_evidence"][0]["quote"]="I never said this"
    llm=FakeLLM(output)
    result=await reports.end_session(db,SimpleNamespace(llm=llm),s.id)
    assert result.snapshot_status=="failed" and llm.calls==2
    t.misheard=True;t.misheard_at=utcnow();db.add(t);db.commit()
    small={"vocab_rating":None,"vocab_evidence":[],"summary":{"weaknesses":[],"next_focus":"Speak more next time."}}
    result=await reports.regenerate(db,SimpleNamespace(llm=FakeLLM(small)),s.id)
    assert result.snapshot_status=="ok" and result.vocab_rating is None and not result.scores.sufficient_sample

@pytest.mark.asyncio
async def test_quiz_exclusion_during_generation_is_not_delivered(db):
    p,s,t,m=evidence(db)
    def exclude():
        m.status="excluded";m.excluded_at=utcnow();db.add(m);db.commit()
    with pytest.raises(ApiError) as caught:
        await quizzes.create_quiz(db,SimpleNamespace(llm=FakeLLM(quiz_output(m),exclude)),p.id,"de")
    assert caught.value.status==409

@pytest.mark.asyncio
async def test_quiz_rejects_ambiguous_duplicate_options_and_foreign_source(db):
    p,s,t,m=evidence(db)
    bad=quiz_output(m)["questions"][0]
    bad.update(kind="mc",options=[{"id":"a","text":"same"},{"id":"b","text":"same"}],
               correct_option_id="a",accepted_answers=[])
    llm=FakeLLM({"questions":[bad]})
    with pytest.raises(ApiError):
        await quizzes.create_quiz(db,SimpleNamespace(llm=llm),p.id,"de")
    assert llm.calls==2
    p2,s2,t2,m2=evidence(db)
    foreign=FakeLLM(quiz_output(m2))
    with pytest.raises(ApiError):
        await quizzes.create_quiz(db,SimpleNamespace(llm=foreign),p.id,"de")
    assert foreign.calls==2

@pytest.mark.asyncio
async def test_analysis_valid_snapshot_survives_failed_attempt_and_gets_stale(db):
    p,s,t,m=evidence(db,ended=True)
    p,s2,t2,m2=evidence(db,ended=True,profile=p)
    good={"summary":"Auxiliary choice recurs.","strengths":[{"text":"Consistent practice","evidence":"Two sessions"}],
          "focus_areas":[{"topic":m.topic,"why":"It recurs","tip":"Practise sein",
                         "example_mistake_ids":[m.id,m2.id]}]}
    await analysis.generate_analysis(db,SimpleNamespace(llm=FakeLLM(good)),p.id,"de")
    out=analysis.get_analysis(db,p.id,"de")
    assert out.written is not None and out.based_on_sessions==2 and not out.latest_attempt_failed
    m.status="excluded";m.excluded_at=utcnow();db.add(m);db.commit()
    bad={**good,"focus_areas":[{**good["focus_areas"][0],"example_mistake_ids":[m.id]}]}
    llm=FakeLLM(bad)
    await analysis.generate_analysis(db,SimpleNamespace(llm=llm),p.id,"de")
    out=analysis.get_analysis(db,p.id,"de")
    assert out.latest_attempt_failed and out.written is not None and out.stale_exclusions==1 and llm.calls==2

@pytest.mark.asyncio
async def test_analysis_improvement_needs_two_adequate_sessions(db):
    p,s,t,m=evidence(db,ended=True)
    for _ in range(2):
        _,s2,t2,m2=evidence(db,ended=True,profile=p)
        m2.status="excluded";m2.excluded_at=utcnow();db.add(m2);db.commit()
    assert [x.topic for x in analysis.get_analysis(db,p.id,"de").improving]==[m.topic]
    t2.misheard=True;db.add(t2);db.commit()
    assert analysis.get_analysis(db,p.id,"de").improving==[]

def test_json_parser_rejects_extra_objects_duplicates_and_nonfinite():
    for text in ['{} {}','{"x":1,"x":2}','{"x":NaN}','[]','<think>a</think><think>b</think>{}']:
        with pytest.raises(ValueError):
            reports.parse_object(text)
    assert reports.parse_object("```json\n{}\n```")=={}
    assert reports.parse_object('<think>reasoning</think>\n{"x":1}')=={"x":1}

@pytest.mark.asyncio
async def test_overlapping_regenerations_keep_their_own_evidence_cutoff(db):
    import asyncio
    p,s,t,m=evidence(db,ended=True)
    sid,mid=s.id,m.id
    entered,release=asyncio.Event(),asyncio.Event()
    class SlowLLM(FakeLLM):
        async def complete(self,*args,**kwargs):
            entered.set()
            await release.wait()
            return await super().complete(*args,**kwargs)
    slow=asyncio.create_task(reports.regenerate(db,SimpleNamespace(llm=SlowLLM(report_output(t))),sid))
    await entered.wait()
    with DBSession(db.get_bind()) as other:
        excluded=other.get(Mistake,mid)
        excluded.status="excluded";excluded.excluded_at=utcnow();other.add(excluded);other.commit()
        await reports.regenerate(other,SimpleNamespace(llm=FakeLLM(report_output(t))),sid)
    release.set()
    result=await slow
    assert result.stale_exclusions==1
    db.expire_all()
    assert reports.get_report(db,sid).stale_exclusions==1
