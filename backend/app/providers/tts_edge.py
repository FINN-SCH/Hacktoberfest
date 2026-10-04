import asyncio
from time import perf_counter
from typing import Any, Callable
from app.config import Settings
from .errors import ProviderError, require_language, require_text
from .interfaces import Language, SpeechResult

class EdgeTTS:
    def __init__(self, settings: Settings, *, communicate_factory: Callable[..., Any] | None = None):
        self.settings = settings
        self._factory = communicate_factory

    async def synthesize(self, text: str, language: Language) -> SpeechResult:
        require_language(language, "tts")
        require_text(text)
        if self._factory is None:
            from edge_tts import Communicate
            self._factory = Communicate
        voice = self.settings.edge_voice_de if language == "de" else self.settings.edge_voice_en
        started = perf_counter()
        async def collect() -> bytes:
            data = bytearray()
            communicator = self._factory(text, voice, rate=self.settings.edge_rate, volume=self.settings.edge_volume)
            async for chunk in communicator.stream():
                if chunk.get("type") == "audio":
                    data.extend(chunk["data"])
            return bytes(data)
        try:
            audio = await asyncio.wait_for(collect(), self.settings.provider_timeout_s)
        except asyncio.TimeoutError as exc:
            raise ProviderError("timeout", "tts", retryable=True) from exc
        except Exception as exc:
            raise ProviderError("synthesis_failed", "tts", retryable=True) from exc
        if not audio:
            raise ProviderError("empty_audio", "tts", retryable=True)
        return SpeechResult(audio, "audio/mpeg", "edge", voice, (perf_counter() - started) * 1000)
