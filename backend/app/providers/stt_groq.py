from time import perf_counter
import httpx
from app.config import Settings
from .audio import validate_wav
from .errors import ProviderError, json_object, post, require_language
from .interfaces import Language, TranscriptionResult

# Deliberately preserve the prototype's learner-error instruction; no phrase blacklist.
INITIAL_PROMPTS = {
    "en": "Verbatim phonetic transcript of an ESL language learner. Transcribe every mistake, grammatical error, slip of the tongue, and exact word spoken without auto-correcting grammar or translating: mein name are Jonathan, he have, yesterday I go, she don't knows.",
    "de": "Wortgetreue Transkription eines Deutschlernenden. Jedes gesprochene Wort, jeden Grammatikfehler und Versprecher unveraendert transkribieren. Nicht korrigieren oder uebersetzen: Ich habe nach Berlin gegangen. Er gehen zur Arbeit. Ich sehe der Mann.",
}

class GroqSTT:
    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self.settings, self.client = settings, client

    async def transcribe(self, wav_bytes: bytes, language: Language) -> TranscriptionResult:
        require_language(language, "stt")
        validate_wav(wav_bytes)
        s = self.settings
        if not s.groq_api_key.get_secret_value():
            raise ProviderError("missing_credentials", "stt")
        started = perf_counter()
        response = await post(self.client, f"{s.groq_base_url}/audio/transcriptions", stage="stt",
            timeout=s.provider_timeout_s,
            headers={"Authorization": f"Bearer {s.groq_api_key.get_secret_value()}"},
            files={"file": ("turn.wav", wav_bytes, "audio/wav")},
            data={"model": s.stt_model, "language": language, "temperature": "0",
                  "response_format": "json", "prompt": INITIAL_PROMPTS[language]})
        text = json_object(response, "stt").get("text")
        if not isinstance(text, str):
            raise ProviderError("invalid_response", "stt", retryable=True)
        return TranscriptionResult(text.strip(), "groq", s.stt_model,
                                   (perf_counter() - started) * 1000)
