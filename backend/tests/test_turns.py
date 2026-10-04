import json
from dataclasses import dataclass, field

import pytest
from sqlmodel import Session as DBSession

from app.db import init_db, make_engine
from app.models import Profile
from app.providers.errors import ProviderError
from app.providers.interfaces import CompletionResult, SpeechResult, TranscriptionResult
from app.schemas.api import SessionCreate
from app.services import exclusions, turns
from app.services.errors import ApiError
from app.services.scoring import session_scores

GOOD = {
    "corrections": [{
        "id": "c1", "original": "habe nach Berlin gegangen", "corrected": "bin nach Berlin gegangen",
        "corrected_sentence": "Ich bin nach Berlin gegangen.", "kind": "error",
        "topic": "de_perfekt_auxiliary", "explanation": "gehen uses sein.",
    }],
    "spoken_correction_id": "c1",
    "needs_clarification": False,
    "reply": "Was hast du dort gemacht?",
}


@dataclass
class FakeSTT:
    text: str = "Ich habe nach Berlin gegangen."
    fail: bool = False
    calls: int = 0

    async def transcribe(self, wav_bytes, language):
        self.calls += 1
        if self.fail:
            raise ProviderError("unavailable", "stt", retryable=True)
        return TranscriptionResult(self.text, "fake", "fake-stt", 1.0)


@dataclass
class FakeLLM:
    outputs: list = field(default_factory=lambda: [json.dumps(GOOD)])
    calls: int = 0
    seen: list = field(default_factory=list)

    async def complete(self, messages, *, schema, purpose):
        self.calls += 1
        self.seen.append(messages)
        out = self.outputs[min(self.calls - 1, len(self.outputs) - 1)]
        if isinstance(out, Exception):
            raise out
        return CompletionResult(out, "fake", "fake-llm", 1.0)


@dataclass
class FakeTTS:
    texts: list = field(default_factory=list)

    async def synthesize(self, text, language):
        self.texts.append(text)
        return SpeechResult(b"mp3", "audio/mpeg", "fake", "fake-tts", 1.0)


@dataclass
class Providers:
    stt: FakeSTT = field(default_factory=FakeSTT)
    llm: FakeLLM = field(default_factory=FakeLLM)
    tts: FakeTTS = field(default_factory=FakeTTS)


pytestmark = pytest.mark.asyncio

TIMING = dict(speech_span_ms=18_000, voiced_ms=15_000, pause_ms=3_000)


@pytest.fixture
def db():
    engine = make_engine(":memory:")
    init_db(engine)
    with DBSession(engine) as session:
        yield session


async def new_session(db):
    p = Profile(name="Amir", native_language="en")
    db.add(p)
    db.commit()
    return await turns.start_session(db, SessionCreate(
        profile_id=p.id, target_language="de", explanation_mode="native", level="A2", scenario="cafe"))


async def submit(db, prov, sid, cid="t1", audio=b"wav-1", **timing):
    return await turns.submit_turn(db, prov, None, sid, cid, audio, **{**TIMING, **timing})


async def test_start_session_creates_spoken_opening(db):
    start = await new_session(db)
    assert start.session.explanation_language == "en"
    prov = Providers()
    await turns.synthesize_turn(db, prov, start.opening_turn_id)
    assert prov.tts.texts == [start.opening_text]


async def test_turn_persists_corrections_and_speaks_recast(db):
    start = await new_session(db)
    prov = Providers()
    out = await submit(db, prov, start.session.id)
    assert out.correction_status == "done" and out.transcript == "Ich habe nach Berlin gegangen."
    c = out.corrections[0]
    assert c.original == "habe nach Berlin gegangen" and c.topic_label == "Perfekt: haben vs. sein"
    assert out.spoken_correction_id == c.id
    await turns.synthesize_turn(db, prov, out.turn_id)
    assert prov.tts.texts[-1] == "Du meinst: Ich bin nach Berlin gegangen. Was hast du dort gemacht?"
    history = prov.llm.seen[0]
    assert [m["role"] for m in history] == ["system", "user"]
    assert "Tutor: " + start.opening_text in history[1]["content"]
    assert history[1]["content"].endswith("Learner's LAST message (analyse this one):\nIch habe nach Berlin gegangen.")


async def test_duplicate_submit_is_idempotent_and_conflicts_are_rejected(db):
    sid = (await new_session(db)).session.id
    prov = Providers()
    first = await submit(db, prov, sid)
    again = await submit(db, prov, sid)
    assert again.turn_id == first.turn_id and prov.stt.calls == 1 and prov.llm.calls == 1
    with pytest.raises(ApiError) as exc:
        await submit(db, prov, sid, audio=b"other")
    assert exc.value.status == 409
    with pytest.raises(ApiError) as exc:
        await submit(db, prov, sid, voiced_ms=14_000, pause_ms=4_000)
    assert exc.value.status == 409


async def test_invalid_llm_output_gets_one_repair(db):
    sid = (await new_session(db)).session.id
    prov = Providers(llm=FakeLLM(outputs=["not json", "```json\n" + json.dumps(GOOD) + "\n```"]))
    out = await submit(db, prov, sid)
    assert out.correction_status == "done" and prov.llm.calls == 2
    assert "rejected" in prov.llm.seen[1][-1]["content"]


async def test_rejected_generation_is_retried_once(db):
    sid = (await new_session(db)).session.id
    prov = Providers(llm=FakeLLM(outputs=[ProviderError("invalid_response", "llm", retryable=True), json.dumps(GOOD)]))
    out = await submit(db, prov, sid)
    assert out.correction_status == "done" and prov.llm.calls == 2


async def test_analysis_failure_keeps_transcript_and_retries_without_audio(db):
    start = await new_session(db)
    sid = start.session.id
    bad = json.dumps({**GOOD, "corrections": [{**GOOD["corrections"][0], "original": "invented words"}]})
    prov = Providers(llm=FakeLLM(outputs=[bad, bad]))
    with pytest.raises(ApiError) as exc:
        await submit(db, prov, sid)
    assert exc.value.body.stage == "analysis" and exc.value.body.retryable
    saved = turns.get_turn_by_client(db, sid, "t1")
    assert saved.correction_status == "analysis_failed" and saved.transcript
    s = db.get(turns.Session, sid)
    assert session_scores(db, s).assessed_turns == 0  # failed analysis is never error-free

    prov.llm = FakeLLM()
    out = await submit(db, prov, sid, audio=None)
    assert out.correction_status == "done" and prov.stt.calls == 1


async def test_stt_failure_requires_audio_on_retry(db):
    sid = (await new_session(db)).session.id
    prov = Providers(stt=FakeSTT(fail=True))
    with pytest.raises(ApiError) as exc:
        await submit(db, prov, sid)
    assert exc.value.body.stage == "stt"
    with pytest.raises(ApiError) as exc:
        await submit(db, prov, sid, audio=None)
    assert exc.value.body.code == "audio_required"
    prov.stt.fail = False
    assert (await submit(db, prov, sid)).correction_status == "done"


async def test_empty_transcript_asks_to_repeat_without_llm(db):
    sid = (await new_session(db)).session.id
    prov = Providers(stt=FakeSTT(text="  "))
    out = await submit(db, prov, sid)
    assert out.needs_clarification and out.corrections == [] and prov.llm.calls == 0


async def test_provider_error_in_llm_marks_analysis_failed(db):
    sid = (await new_session(db)).session.id
    prov = Providers(llm=FakeLLM(outputs=[ProviderError("rate_limit", "llm", retryable=True)]))
    with pytest.raises(ApiError) as exc:
        await submit(db, prov, sid)
    assert exc.value.body.code == "rate_limit"


async def test_bad_timing_rejected(db):
    sid = (await new_session(db)).session.id
    with pytest.raises(ApiError) as exc:
        await submit(db, Providers(), sid, voiced_ms=20_000)
    assert exc.value.status == 422


async def test_exclusions_are_idempotent_and_stop_spoken_recast(db):
    sid = (await new_session(db)).session.id
    prov = Providers()
    out = await submit(db, prov, sid)
    c = exclusions.mark_not_a_mistake(db, out.corrections[0].id)
    assert c.status == "excluded"
    assert exclusions.mark_not_a_mistake(db, c.id).status == "excluded"
    await turns.synthesize_turn(db, prov, out.turn_id)
    assert prov.tts.texts[-1] == "Was hast du dort gemacht?"
    assert exclusions.mark_misheard(db, out.turn_id).misheard
    with pytest.raises(ApiError):
        exclusions.mark_misheard(db, out.turn_id - 1)  # opening turn


async def test_ended_session_rejects_turns(db):
    sid = (await new_session(db)).session.id
    s = db.get(turns.Session, sid)
    s.status = "ended"
    db.add(s)
    db.commit()
    with pytest.raises(ApiError) as exc:
        await submit(db, Providers(), sid)
    assert exc.value.body.code == "session_not_active"
