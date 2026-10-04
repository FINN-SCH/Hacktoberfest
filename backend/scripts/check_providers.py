"""Small real-provider probe. Never prints credentials or upstream response bodies."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys
from time import perf_counter

# Support both python -m scripts.check_providers and python scripts/check_providers.py.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.prompts.turn import build_messages
from app.providers.audio import validate_wav
from app.providers.errors import ProviderError
from app.providers.factory import build_providers
from app.schemas.llm import turn_analysis_json_schema
from app.services.turns import parse_analysis
from app.services.validation import AnalysisValidationError
from app.topics import TOPICS

RETRY_DELAYS = (20, 40, 60)
TRANSCRIPT = "Ich habe nach Berlin gegangen."

class CheckFailure(ValueError):
    pass

def _rate_limited(exc: Exception) -> bool:
    # Edge can wrap aiohttp's 429 inside ProviderError; do not expose its response body.
    cause = exc
    for _ in range(4):
        if getattr(cause, "status_code", None) == 429 or getattr(cause, "status", None) == 429:
            return True
        if isinstance(cause, ProviderError) and cause.code == "rate_limit":
            return True
        cause = cause.__cause__
        if cause is None:
            break
    return False

async def _probe(label, operation, describe, *, sleep=asyncio.sleep, emit=print):
    started = perf_counter()
    for attempt in range(4):
        try:
            result = await operation()
            reason = describe(result)
            emit(f"PASS {label} {(perf_counter() - started) * 1000:.0f}ms {reason}", flush=True)
            return result, False
        except Exception as exc:
            if _rate_limited(exc) and attempt < len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt]
                emit(f"WAIT {label} 429; waiting {delay}s before retry {attempt + 1}/3", flush=True)
                await sleep(delay)
                continue
            if isinstance(exc, ProviderError):
                reason = exc.code
            elif isinstance(exc, CheckFailure):
                reason = str(exc)
            else:
                reason = type(exc).__name__  # no raw exception or body: it could contain a key
            emit(f"FAIL {label} {(perf_counter() - started) * 1000:.0f}ms {reason}", flush=True)
            return None, True

def _describe_llm(result):
    try:
        parsed = parse_analysis(result.content, TRANSCRIPT, "de")
    except (AnalysisValidationError, ValueError, TypeError):
        raise CheckFailure("response did not pass the tutor correction contract") from None
    if parsed.needs_clarification or not any(c.kind == "error" and c.topic == "de_perfekt_auxiliary" for c in parsed.corrections):
        raise CheckFailure("expected de_perfekt_auxiliary correction was missing")
    return "valid turn JSON; de_perfekt_auxiliary correction found"

def _describe_tts(result):
    if not result.audio or not result.media_type.startswith("audio/"):
        raise CheckFailure("expected nonempty audio and an audio media type")
    return f"{len(result.audio)} bytes; {result.media_type}"

def _describe_stt(result):
    if not result.text.strip():
        raise CheckFailure("empty transcript; try a clearly spoken WAV")
    device = result.metadata.get("device")
    suffix = f"; device={device}" if device else ""
    return f"nonempty transcript{suffix}; plumbing only, not error-preservation evidence"

async def run_checks(settings, providers, *, stt_wav: Path | None = None, sleep=asyncio.sleep, emit=print) -> int:
    emit(f"CONFIG LLM=openai-compatible model={settings.llm_model} JSON={settings.llm_json_mode}; "
         f"STT={settings.stt_provider} model={settings.stt_model}; TTS={settings.tts_provider}", flush=True)
    labels = ("LLM/openai-compatible", f"TTS/{settings.tts_provider}", f"STT/{settings.stt_provider}")
    messages = build_messages("de", "A2", "cafe", "en", [], TRANSCRIPT)
    _, llm_failed = await _probe(labels[0], lambda: providers.llm.complete(messages,
        schema=turn_analysis_json_schema(list(TOPICS["de"])), purpose="turn"),
        _describe_llm, sleep=sleep, emit=emit)
    audio, tts_failed = await _probe(labels[1], lambda: providers.tts.synthesize("Hallo!", "de"),
                                   _describe_tts, sleep=sleep, emit=emit)
    wav = None
    if stt_wav is not None:
        try:
            wav = stt_wav.read_bytes()
            validate_wav(wav)
        except (OSError, ProviderError):
            emit(f"FAIL {labels[2]} 0ms --stt-wav must be readable mono PCM16 16000Hz WAV")
            return 1
    elif audio is not None and audio.audio[:4] == b"RIFF" and audio.audio[8:12] == b"WAVE":
        try:
            validate_wav(audio.audio)
            wav = audio.audio
        except ProviderError:
            emit(f"SKIPPED {labels[2]} 0ms TTS WAV is not mono PCM16 16000Hz; supply --stt-wav or speak in the browser")
    else:
        emit(f"SKIPPED {labels[2]} 0ms no compatible TTS WAV (Edge returns MP3); supply --stt-wav or speak in the browser")
    stt_failed = False
    if wav is not None:
        _, stt_failed = await _probe(labels[2], lambda: providers.stt.transcribe(wav, "de"),
                                    _describe_stt, sleep=sleep, emit=emit)
    return int(llm_failed or tts_failed or stt_failed)

async def _main(stt_wav):
    providers = None
    try:
        settings = Settings()
        providers = build_providers(settings)
        return await run_checks(settings, providers, stt_wav=stt_wav)
    except Exception as exc:
        print(f"FAIL configuration 0ms {type(exc).__name__}; check settings without sharing .env")
        return 1
    finally:
        if providers is not None:
            await providers.aclose()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Probe configured providers once each; only 429s are retried.")
    parser.add_argument("--stt-wav", type=Path, help="Optional German speech, mono PCM16 16kHz WAV, instead of TTS output.")
    args = parser.parse_args(argv)
    return asyncio.run(_main(args.stt_wav))

if __name__ == "__main__":
    raise SystemExit(main())
