import asyncio
import base64
import io
import json
import threading
import wave
from types import SimpleNamespace

import httpx
import pytest
from app.config import Settings
from app.providers.errors import ProviderError
from app.providers.llm_openai import OpenAICompatibleLLM
from app.providers.stt_groq import GroqSTT
from app.providers.stt_faster_whisper import FasterWhisperSTT
from app.providers.tts_deepinfra import DeepInfraTTS
from app.providers.tts_edge import EdgeTTS

def settings(**kwargs):
    return Settings(_env_file=None, **kwargs)

def wav():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\0\0" * 1600)
    return buffer.getvalue()

@pytest.mark.asyncio
async def test_litellm_wire_and_raw_content_no_repair():
    seen = []
    async def handle(request):
        seen.append(json.loads(request.content))
        assert request.headers["authorization"] == "Bearer dummy"
        return httpx.Response(200, json={"choices": [{"message": {"content": "not JSON"}, "finish_reason": "stop"}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await OpenAICompatibleLLM(settings(), client).complete(
            [{"role": "user", "content": "Hallo"}], schema={"type": "object"}, purpose="turn")
    assert result.content == "not JSON"  # services validate and repair
    assert len(seen) == 1
    body = seen[0]
    assert body["model"] == "qwen3.8-fast" and body["stream"] is False
    assert body["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert "response_format" not in body
    assert "JSON" in body["messages"][0]["content"]

@pytest.mark.asyncio
async def test_groq_schema_profile_and_purpose_budget():
    async def handle(request):
        body = json.loads(request.content)
        assert body["response_format"]["json_schema"]["strict"] is True
        assert body["max_tokens"] == 4096
        assert "extra_body" not in body
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        await OpenAICompatibleLLM(settings(llm_json_mode="json_schema", llm_extra_json={}), client).complete(
            [], schema={"type": "object", "additionalProperties": False}, purpose="quiz")

@pytest.mark.asyncio
@pytest.mark.parametrize("status,code,retryable", [(401, "authentication", False), (403, "authentication", False),
    (429, "rate_limit", True), (400, "bad_request", False), (503, "unavailable", True)])
async def test_http_errors_are_typed_without_downgrade(status, code, retryable):
    calls = []
    async def handle(request):
        calls.append(request)
        return httpx.Response(status, json={"secret_upstream_detail": "must not leak"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ProviderError) as error:
            await OpenAICompatibleLLM(settings(), client).complete([], schema={}, purpose="turn")
    assert len(calls) == 1
    assert (error.value.code, error.value.retryable, error.value.stage) == (code, retryable, "llm")
    assert "secret_upstream_detail" not in str(error.value)

@pytest.mark.asyncio
async def test_truncation_is_explicit():
    async def handle(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"corrections":'}, "finish_reason": "length"}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ProviderError, match="truncated"):
            await OpenAICompatibleLLM(settings(), client).complete([], schema={}, purpose="turn")

@pytest.mark.asyncio
async def test_groq_stt_multipart_forced_language_no_blacklist():
    async def handle(request):
        assert request.url.path == "/openai/v1/audio/transcriptions"
        body = request.content
        assert b'name="language"\r\n\r\nde' in body
        assert b'name="model"\r\n\r\nwhisper-large-v3' in body
        assert b'RIFF' in body and b'filename="turn.wav"' in body
        return httpx.Response(200, json={"text": "Thank you"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await GroqSTT(settings(groq_api_key="test", stt_model="whisper-large-v3"), client).transcribe(wav(), "de")
    assert result.text == "Thank you"

@pytest.mark.asyncio
async def test_deepinfra_documented_payload_and_data_uri():
    audio = wav()
    async def handle(request):
        assert request.url.path == "/v1/inference/ResembleAI/chatterbox-multilingual"
        body = json.loads(request.content)
        assert body == {"text": "Guten Tag", "language_id": "de", "response_format": "wav"}
        return httpx.Response(200, json={"audio": "data:audio/wav;base64," + base64.b64encode(audio).decode(),
                                         "output_format": "wav"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await DeepInfraTTS(settings(deepinfra_api_key="test"), client).synthesize("Guten Tag", "de")
    assert result.audio == audio and result.media_type == "audio/wav"

@pytest.mark.asyncio
async def test_empty_edge_audio_errors_and_full_stream_collected():
    selected = []
    class Communicate:
        def __init__(self, text, voice, **kwargs):
            selected.append(voice)
        async def stream(self):
            yield {"type": "WordBoundary"}
            yield {"type": "audio", "data": b"first"}
            yield {"type": "audio", "data": b"second"}
    result = await EdgeTTS(settings(), communicate_factory=Communicate).synthesize("Hallo", "de")
    assert result.audio == b"firstsecond" and selected == ["de-DE-ConradNeural"]
    class Empty(Communicate):
        async def stream(self):
            yield {"type": "WordBoundary"}
    with pytest.raises(ProviderError) as error:
        await EdgeTTS(settings(), communicate_factory=Empty).synthesize("Hallo", "de")
    assert error.value.code == "empty_audio"

@pytest.mark.asyncio
async def test_faster_whisper_lazy_gpu_iteration_failure_falls_back_once_off_loop():
    calls, threads = [], []
    main_thread = threading.get_ident()
    def model_factory(model, **kwargs):
        calls.append(kwargs)
        device = kwargs["device"]
        class Model:
            def transcribe(self, audio, **options):
                assert options["language"] == "de"
                assert options["condition_on_previous_text"] is False
                def segments():
                    threads.append(threading.get_ident())
                    if device == "cuda":
                        raise RuntimeError("CUDA out of memory")
                    yield SimpleNamespace(text=" Ich habe nach Berlin gegangen.")
                return segments(), SimpleNamespace(language="de")
        return Model()
    adapter = FasterWhisperSTT(settings(), model_factory=model_factory)
    assert calls == []
    result = await adapter.transcribe(wav(), "de")
    await adapter.transcribe(wav(), "de")
    assert [c["device"] for c in calls] == ["cuda", "cpu"]
    assert all(t != main_thread for t in threads)
    assert result.metadata["device"] == "cpu"
    assert result.text == "Ich habe nach Berlin gegangen."

def test_settings_reject_reserved_extra_json():
    with pytest.raises(ValueError):
        settings(llm_extra_json={"stream": True})

@pytest.mark.asyncio
async def test_invalid_wav_rejected_before_network():
    async def handle(request):
        pytest.fail("invalid audio reached provider")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ProviderError):
            await GroqSTT(settings(groq_api_key="test"), client).transcribe(b"webm", "en")
