from dataclasses import dataclass, field
import httpx
from app.config import Settings
from .interfaces import LLMProvider, STTProvider, TTSProvider
from .llm_openai import OpenAICompatibleLLM
from .stt_groq import GroqSTT
from .stt_faster_whisper import FasterWhisperSTT
from .tts_edge import EdgeTTS
from .tts_deepinfra import DeepInfraTTS

@dataclass
class Providers:
    llm: LLMProvider
    stt: STTProvider
    tts: TTSProvider
    _owned_client: httpx.AsyncClient | None = field(default=None, repr=False)

    async def aclose(self) -> None:
        if self._owned_client is not None:
            await self._owned_client.aclose()

def build_providers(settings: Settings, *, http_client: httpx.AsyncClient | None = None) -> Providers:
    # Construct in application lifespan (Step C), never during OpenAPI export/import.
    client = http_client or httpx.AsyncClient(timeout=settings.provider_timeout_s)
    return Providers(
        llm=OpenAICompatibleLLM(settings, client),
        stt=GroqSTT(settings, client) if settings.stt_provider == "groq" else FasterWhisperSTT(settings),
        tts=EdgeTTS(settings) if settings.tts_provider == "edge" else DeepInfraTTS(settings, client),
        _owned_client=None if http_client is not None else client,
    )
