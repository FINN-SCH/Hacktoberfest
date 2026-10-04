import io
import json
import wave
from types import SimpleNamespace
import pytest
from app.config import Settings
from app.providers.errors import ProviderError
from app.providers.interfaces import CompletionResult, SpeechResult, TranscriptionResult
from scripts.check_providers import run_checks
from test_turns import GOOD

def wav():
    data = io.BytesIO()
    with wave.open(data, "wb") as audio:
        audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(16000)
        audio.writeframes(b"\0\0" * 1600)
    return data.getvalue()

class Fake:
    def __init__(self, *, limit=0, audio=None, text="Hallo"):
        self.llm = self; self.tts = self; self.stt = self
        self.limit = limit; self.calls = 0; self.stt_calls = 0
        self.audio = audio; self.text = text
    async def complete(self, messages, *, schema, purpose):
        self.calls += 1
        if self.calls <= self.limit:
            raise ProviderError("rate_limit", "llm", status_code=429)
        return CompletionResult(json.dumps(GOOD), "fake", "fake", 1)
    async def synthesize(self, text, language):
        return SpeechResult(self.audio or b"mp3", "audio/wav" if self.audio else "audio/mpeg", "fake", "fake", 1)
    async def transcribe(self, audio, language):
        self.stt_calls += 1
        return TranscriptionResult(self.text, "fake", "fake", 1)

@pytest.mark.asyncio
async def test_probe_retries_only_429_with_bounded_delays_and_skips_mp3():
    delays, lines = [], []
    async def sleep(seconds): delays.append(seconds)
    fake = Fake(limit=3)
    result = await run_checks(Settings(_env_file=None, llm_api_key="never-print-me"), fake,
                              sleep=sleep, emit=lambda line, **kw: lines.append(line))
    assert result == 0 and fake.calls == 4 and fake.stt_calls == 0
    assert delays == [20, 40, 60]
    assert any(line.startswith("SKIPPED STT/") for line in lines)
    assert "never-print-me" not in "\n".join(lines)

@pytest.mark.asyncio
async def test_probe_stops_after_three_retries_and_continues_other_checks():
    delays, lines = [], []
    async def sleep(seconds): delays.append(seconds)
    fake = Fake(limit=99, audio=wav())
    assert await run_checks(Settings(_env_file=None), fake, sleep=sleep, emit=lambda line, **kw: lines.append(line)) == 1
    assert fake.calls == 4 and fake.stt_calls == 1 and delays == [20, 40, 60]
    assert any(line.startswith("PASS TTS/") for line in lines)

@pytest.mark.asyncio
async def test_probe_real_audio_contract_and_empty_transcript(tmp_path):
    path = tmp_path / "input.wav"; path.write_bytes(wav())
    fake = Fake(text="")
    assert await run_checks(Settings(_env_file=None), fake, stt_wav=path, emit=lambda *a, **k: None) == 1
    assert fake.stt_calls == 1

@pytest.mark.asyncio
async def test_probe_does_not_retry_auth_or_expose_exception_text():
    class Broken(Fake):
        async def complete(self, *args, **kwargs):
            self.calls += 1
            raise ProviderError("authentication", "llm", status_code=401)
        async def synthesize(self, *args, **kwargs):
            raise RuntimeError("secret-key-that-must-not-print")
    fake = Broken()
    lines = []
    assert await run_checks(Settings(_env_file=None), fake, emit=lambda line, **kw: lines.append(line)) == 1
    assert fake.calls == 1 and "secret-key-that-must-not-print" not in "\n".join(lines)
