"""Native schema verified at https://deepinfra.com/ResembleAI/chatterbox-multilingual/api.
Input: text/language_id/response_format/optional voice_id; JSON output contains base64 audio.
No synthesis has been claimed verified without a real account request.
"""
import base64
import binascii
from time import perf_counter
import httpx
from app.config import Settings
from .errors import ProviderError, json_object, post, require_language, require_text
from .interfaces import Language, SpeechResult

class DeepInfraTTS:
    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self.settings, self.client = settings, client

    async def synthesize(self, text: str, language: Language) -> SpeechResult:
        require_language(language, "tts")
        require_text(text)
        s = self.settings
        if not s.deepinfra_api_key.get_secret_value():
            raise ProviderError("missing_credentials", "tts")
        started = perf_counter()
        body = {"text": text, "language_id": language, "response_format": "wav"}
        voice = s.deepinfra_voice_de if language == "de" else s.deepinfra_voice_en
        if voice:
            body["voice_id"] = voice
        response = await post(self.client, f"{s.deepinfra_base_url}/{s.tts_model}", stage="tts",
            timeout=s.provider_timeout_s, json=body,
            headers={"Authorization": f"Bearer {s.deepinfra_api_key.get_secret_value()}"})
        if response.headers.get("content-type", "").split(";")[0] in ("audio/wav", "audio/x-wav"):
            audio = response.content
        else:
            data = json_object(response, "tts")
            if data.get("inference_status", {}).get("status", "succeeded") != "succeeded":
                raise ProviderError("synthesis_failed", "tts", retryable=True)
            encoded = data.get("audio")
            if not isinstance(encoded, str):
                raise ProviderError("invalid_response", "tts", retryable=True)
            if encoded.startswith("data:"):
                header, separator, encoded = encoded.partition(",")
                if not separator or header not in ("data:audio/wav;base64", "data:audio/x-wav;base64"):
                    raise ProviderError("invalid_response", "tts", retryable=True)
            try:
                audio = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise ProviderError("invalid_response", "tts", retryable=True) from exc
        if not audio:
            raise ProviderError("empty_audio", "tts", retryable=True)
        if not (audio.startswith(b"RIFF") and audio[8:12] == b"WAVE"):
            raise ProviderError("invalid_audio", "tts", retryable=True)
        return SpeechResult(audio, "audio/wav", "deepinfra", s.tts_model, (perf_counter() - started) * 1000)
