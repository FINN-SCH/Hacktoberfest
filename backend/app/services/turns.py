"""Session start and the per-turn pipeline: STT -> tutor LLM -> validated, persisted corrections.

Turns are idempotent per (session_id, client_turn_id); a failed stage is retried by re-POSTing the
same id. Speech is synthesised separately from saved evidence, so a TTS failure never loses text.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from time import perf_counter
from typing import Optional

from pydantic import ValidationError
from sqlmodel import Session as DBSession
from sqlmodel import func, select

from ..languages import OPENINGS, resolve_explanation_language, spoken_text
from ..models import Mistake, Profile, Session, Turn, utcnow
from ..prompts import turn as turn_prompt
from ..providers.errors import ProviderError
from ..providers.interfaces import SpeechResult
from ..schemas.api import CorrectionOut, SessionCreate, SessionOut, SessionStartOut, TurnOut
from ..schemas.llm import TurnAnalysis, turn_analysis_json_schema
from ..topics import TOPICS, topic_label
from .errors import ApiError
from .validation import AnalysisValidationError, ValidatedAnalysis, nfc, validate_analysis

CLARIFY = {
    "de": "Entschuldigung, das habe ich nicht verstanden. Kannst du das bitte wiederholen?",
    "en": "Sorry, I didn't catch that. Could you say it again?",
}

_locks: dict[int, asyncio.Lock] = {}


def _lock(session_id: int) -> asyncio.Lock:
    return _locks.setdefault(session_id, asyncio.Lock())


def session_out(s: Session) -> SessionOut:
    return SessionOut.model_validate(s, from_attributes=True)


def _get_session(db: DBSession, session_id: int) -> Session:
    s = db.get(Session, session_id)
    if s is None:
        raise ApiError(404, "session_not_found", "Session not found.")
    return s


def correction_out(m: Mistake) -> CorrectionOut:
    return CorrectionOut(
        id=m.id, original=m.original, corrected=m.corrected, corrected_sentence=m.corrected_sentence,
        kind=m.kind, topic=m.topic, topic_label=topic_label(m.topic), explanation=m.explanation,
        highlight_start=m.highlight_start, highlight_end=m.highlight_end, status=m.status,
    )


def turn_out(db: DBSession, t: Turn) -> TurnOut:
    mistakes = db.exec(select(Mistake).where(Mistake.turn_id == t.id).order_by(Mistake.id)).all()
    return TurnOut(
        turn_id=t.id, session_id=t.session_id, seq=t.seq, kind=t.kind, client_turn_id=t.client_turn_id,
        correction_status=t.correction_status, failure_code=t.failure_code, transcript=t.transcript,
        needs_clarification=t.needs_clarification, misheard=t.misheard,
        corrections=[correction_out(m) for m in mistakes],
        spoken_correction_id=t.spoken_correction_mistake_id, reply=t.tutor_reply,
    )


async def start_session(db: DBSession, data: SessionCreate) -> SessionStartOut:
    profile = db.get(Profile, data.profile_id)
    if profile is None:
        raise ApiError(404, "profile_not_found", "Profile not found.")
    s = Session(
        profile_id=profile.id,
        target_language=data.target_language,
        explanation_language=resolve_explanation_language(
            data.explanation_mode, profile.native_language, data.target_language),
        level=data.level,
        scenario=data.scenario,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    opening_text = OPENINGS[s.target_language][s.scenario]
    opening = Turn(session_id=s.id, seq=0, kind="opening", correction_status="done", tutor_reply=opening_text)
    db.add(opening)
    db.commit()
    db.refresh(opening)
    return SessionStartOut(session=session_out(s), opening_turn_id=opening.id, opening_text=opening_text)


def _turn_by_client(db: DBSession, session_id: int, client_turn_id: str) -> Optional[Turn]:
    return db.exec(
        select(Turn).where(Turn.session_id == session_id, Turn.client_turn_id == client_turn_id)
    ).first()


def get_turn_by_client(db: DBSession, session_id: int, client_turn_id: str) -> TurnOut:
    _get_session(db, session_id)
    t = _turn_by_client(db, session_id, client_turn_id)
    if t is None:
        raise ApiError(404, "turn_not_found", "Turn not found.")
    return turn_out(db, t)


def list_turns(db: DBSession, session_id: int) -> list[TurnOut]:
    _get_session(db, session_id)
    turns = db.exec(select(Turn).where(Turn.session_id == session_id).order_by(Turn.seq)).all()
    return [turn_out(db, t) for t in turns]


def session_has_processing_turn(db: DBSession, session_id: int) -> bool:
    return db.exec(
        select(Turn.id).where(Turn.session_id == session_id, Turn.correction_status == "processing")
    ).first() is not None


def _check_timing(speech_span_ms: int, voiced_ms: int, pause_ms: int) -> None:
    ok = 0 < voiced_ms <= speech_span_ms and pause_ms >= 0 and abs(voiced_ms + pause_ms - speech_span_ms) <= 2
    if not ok:
        raise ApiError(422, "invalid_timing", "Timing must satisfy 0 < voiced <= span and voiced + pause = span.")


async def submit_turn(
    db: DBSession,
    providers,
    settings,
    session_id: int,
    client_turn_id: str,
    audio: Optional[bytes],
    speech_span_ms: int,
    voiced_ms: int,
    pause_ms: int,
) -> TurnOut:
    _check_timing(speech_span_ms, voiced_ms, pause_ms)
    audio_hash = hashlib.sha256(audio).hexdigest() if audio else None

    async with _lock(session_id):
        s = _get_session(db, session_id)
        if s.status != "active":
            raise ApiError(409, "session_not_active", "This session has ended.")

        t = _turn_by_client(db, session_id, client_turn_id)
        if t is not None:
            if (t.speech_span_ms, t.voiced_ms, t.pause_ms) != (speech_span_ms, voiced_ms, pause_ms):
                raise ApiError(409, "turn_conflict", "Same turn id with different timing.", turn_id=t.id)
            if audio_hash is not None and audio_hash != t.audio_sha256:
                raise ApiError(409, "turn_conflict", "Same turn id with different audio.", turn_id=t.id)
            if t.correction_status in ("done", "processing"):
                return turn_out(db, t)
            if t.correction_status == "stt_failed" and audio is None:
                raise ApiError(422, "audio_required", "Re-send the audio to retry transcription.",
                               stage="stt", retryable=True, turn_id=t.id)
        else:
            if audio is None:
                raise ApiError(422, "audio_required", "Audio is required for a new turn.")
            next_seq = (db.exec(select(func.max(Turn.seq)).where(Turn.session_id == session_id)).one() or 0) + 1
            t = Turn(
                session_id=session_id, seq=next_seq, client_turn_id=client_turn_id, audio_sha256=audio_hash,
                speech_span_ms=speech_span_ms, voiced_ms=voiced_ms, pause_ms=pause_ms,
            )

        t.correction_status = "processing"
        t.failure_code = None
        t.updated_at = utcnow()
        db.add(t)
        db.commit()
        db.refresh(t)

        if t.transcript is None:
            await _run_stt(db, providers, s, t, audio)
        if t.transcript == "":
            _save_clarification(db, s, t)
        else:
            await _run_analysis(db, providers, settings, s, t)
        return turn_out(db, t)


def _fail(db: DBSession, t: Turn, status: str, code: str, stage: str, retryable: bool) -> ApiError:
    t.correction_status = status
    t.failure_code = code
    t.updated_at = utcnow()
    db.add(t)
    db.commit()
    return ApiError(502, code, f"The {stage} step failed ({code}).", stage=stage, retryable=retryable, turn_id=t.id)


async def _run_stt(db: DBSession, providers, s: Session, t: Turn, audio: bytes) -> None:
    started = perf_counter()
    try:
        result = await providers.stt.transcribe(audio, s.target_language)
    except ProviderError as e:
        raise _fail(db, t, "stt_failed", e.code, "stt", e.retryable)
    t.transcript = nfc(result.text).strip()
    t.stt_ms = int((perf_counter() - started) * 1000)
    db.add(t)
    db.commit()  # the transcript survives an analysis failure


def _save_clarification(db: DBSession, s: Session, t: Turn) -> None:
    t.needs_clarification = True
    t.tutor_reply = CLARIFY[s.target_language]
    t.correction_status = "done"
    t.updated_at = utcnow()
    db.add(t)
    db.commit()


def _history(db: DBSession, s: Session, before_seq: int) -> list[tuple[str, str]]:
    turns = db.exec(
        select(Turn).where(Turn.session_id == s.id, Turn.seq < before_seq).order_by(Turn.seq)
    ).all()
    out: list[tuple[str, str]] = []
    for prev in turns:
        if prev.kind == "learner" and prev.transcript and not prev.misheard:
            out.append(("user", prev.transcript))
        if prev.tutor_reply:
            out.append(("assistant", prev.tutor_reply))
    return out


_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
_THINK = re.compile(r"^\s*<think>.*?</think>\s*", re.DOTALL)


def parse_analysis(content: str, transcript: str, language: str) -> ValidatedAnalysis:
    text = _THINK.sub("", content.strip(), count=1).strip()
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise AnalysisValidationError([f"not a single valid JSON object: {e.msg}"])
    if not isinstance(data, dict):
        raise AnalysisValidationError(["top level must be a JSON object"])
    try:
        analysis = TurnAnalysis.model_validate(data)
    except ValidationError as e:
        raise AnalysisValidationError([f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()])
    return validate_analysis(analysis, transcript, language)


async def _run_analysis(db: DBSession, providers, settings, s: Session, t: Turn) -> None:
    messages = turn_prompt.build_messages(
        s.target_language, s.level, s.scenario, s.explanation_language, _history(db, s, t.seq), t.transcript)
    schema = turn_analysis_json_schema(list(TOPICS[s.target_language]))
    started = perf_counter()
    validated: Optional[ValidatedAnalysis] = None
    model_name = None
    try:
        for attempt in range(2):  # one repair attempt, owned here
            result = await providers.llm.complete(messages, schema=schema, purpose="turn")
            model_name = result.model
            try:
                validated = parse_analysis(result.content, t.transcript, s.target_language)
                break
            except AnalysisValidationError as e:
                if attempt == 0:
                    messages = turn_prompt.repair_messages(messages, result.content, e.errors)
    except ProviderError as e:
        raise _fail(db, t, "analysis_failed", e.code, "analysis", e.retryable)
    if validated is None:
        raise _fail(db, t, "analysis_failed", "invalid_llm_output", "analysis", True)

    by_ref: dict[str, Mistake] = {}
    if not validated.needs_clarification:
        for c in validated.corrections:
            m = Mistake(
                profile_id=s.profile_id, session_id=s.id, turn_id=t.id, language=s.target_language,
                topic=c.topic, kind=c.kind, original=c.original, corrected=c.corrected,
                corrected_sentence=c.corrected_sentence, explanation=c.explanation,
                highlight_start=c.highlight_start, highlight_end=c.highlight_end, llm_ref=c.llm_ref,
            )
            db.add(m)
            by_ref[c.llm_ref] = m
        db.flush()
    spoken = by_ref.get(validated.spoken_ref) if validated.spoken_ref else None
    t.spoken_correction_mistake_id = spoken.id if spoken else None
    t.needs_clarification = validated.needs_clarification
    t.tutor_reply = validated.reply
    t.correction_status = "done"
    t.llm_ms = int((perf_counter() - started) * 1000)
    t.llm_model = model_name
    t.prompt_version = turn_prompt.PROMPT_VERSION
    t.updated_at = utcnow()
    db.add(t)
    db.commit()  # mistakes + reply land atomically
    db.refresh(t)


async def synthesize_turn(db: DBSession, providers, turn_id: int) -> SpeechResult:
    t = db.get(Turn, turn_id)
    if t is None:
        raise ApiError(404, "turn_not_found", "Turn not found.")
    if t.correction_status != "done" or not t.tutor_reply:
        raise ApiError(409, "turn_not_ready", "This turn has no tutor response yet.", turn_id=t.id)
    s = db.get(Session, t.session_id)
    recast = None
    if t.spoken_correction_mistake_id is not None:
        m = db.get(Mistake, t.spoken_correction_mistake_id)
        if m is not None and m.status == "active" and not t.misheard:
            recast = m.corrected_sentence
    text = spoken_text(s.target_language, recast, t.tutor_reply)
    try:
        return await providers.tts.synthesize(text, s.target_language)
    except ProviderError as e:
        raise ApiError(502, e.code, f"The speech step failed ({e.code}).", stage="tts",
                       retryable=e.retryable, turn_id=t.id)
