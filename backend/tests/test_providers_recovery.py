import asyncio
import io
import threading
import wave
from types import SimpleNamespace
import httpx
import pytest
from app.config import Settings
from app.providers.errors import ProviderError
from app.providers.llm_openai import OpenAICompatibleLLM
from app.providers.stt_faster_whisper import FasterWhisperSTT
from app.providers.tts_deepinfra import DeepInfraTTS

def wav():
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(b"\0\0" * 800)
    return out.getvalue()

@pytest.mark.asyncio
async def test_cancellation_keeps_native_stt_serialized():
    entered = threading.Event()
    release = threading.Event()
    calls = []
    def factory(*args, **kwargs):
        class Model:
            def transcribe(self, *args, **kwargs):
                def segments():
                    calls.append(1)
                    entered.set()
                    release.wait(timeout=3)
                    yield SimpleNamespace(text="hello")
                return segments(), None
        return Model()
    adapter = FasterWhisperSTT(Settings(_env_file=None, stt_device="cpu"), model_factory=factory)
    first = asyncio.create_task(adapter.transcribe(wav(), "en"))
    assert await asyncio.to_thread(entered.wait, 2)
    first.cancel()
    second = asyncio.create_task(adapter.transcribe(wav(), "en"))
    try:
        await asyncio.sleep(0.02)
        assert len(calls) == 1
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await first
    assert (await second).text == "hello"
    assert len(calls) == 2

@pytest.mark.asyncio
async def test_timeout_does_not_retry():
    calls = []
    async def handle(request):
        calls.append(1)
        raise httpx.ReadTimeout("upstream", request=request)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ProviderError) as error:
            await OpenAICompatibleLLM(Settings(_env_file=None), client).complete([], schema={}, purpose="turn")
    assert error.value.code == "timeout" and error.value.retryable
    assert len(calls) == 1

@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{"audio": ""}, {"audio": "broken base64"}, {"audio": "aGVsbG8="},
    {"audio": "http://unexpected.example/audio.wav"}, {"unexpected": True}])
async def test_deepinfra_rejects_unusable_audio(payload):
    async def handle(request):
        return httpx.Response(200, json=payload)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ProviderError):
            await DeepInfraTTS(Settings(_env_file=None, deepinfra_api_key="test"), client).synthesize("Hallo", "de")
