import asyncio
import io
import logging
from time import perf_counter
from typing import Any, Callable
from app.config import Settings
from .audio import validate_wav
from .errors import ProviderError, require_language
from .interfaces import Language, TranscriptionResult
from .stt_groq import INITIAL_PROMPTS

logger = logging.getLogger(__name__)

class FasterWhisperSTT:
    def __init__(self, settings: Settings, *, model_factory: Callable[..., Any] | None = None):
        self.settings = settings
        self._factory = model_factory
        self._model: Any = None
        self._device = "cpu" if settings.stt_device == "cpu" else "cuda"
        self._fallback_used = False
        self._semaphore = asyncio.Semaphore(1)

    def _load(self) -> Any:
        if self._factory is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise ProviderError("local_stt_not_installed", "stt") from exc
            self._factory = WhisperModel
        if self._model is None:
            self._model = self._factory(self.settings.stt_model, device=self._device,
                compute_type="int8" if self._device == "cpu" else "int8_float16",
                cpu_threads=self.settings.stt_cpu_threads)
        return self._model

    def _run(self, data: bytes, language: Language) -> str:
        segments, _ = self._load().transcribe(
            io.BytesIO(data), language=language, initial_prompt=INITIAL_PROMPTS[language],
            beam_size=1, best_of=1, temperature=0.0, condition_on_previous_text=False,
            vad_filter=True, vad_parameters={"min_silence_duration_ms": 250, "threshold": 0.4},
        )
        # Generator iteration performs inference: it MUST stay inside the worker thread.
        return " ".join(segment.text for segment in segments).strip()

    def _transcribe_sync(self, data: bytes, language: Language) -> str:
        try:
            return self._run(data, language)
        except ProviderError:
            raise
        except Exception as exc:
            if self._device == "cuda" and not self._fallback_used:
                self._fallback_used = True
                self._model = None
                self._device = "cpu"
                logger.warning("Local STT CUDA failed; using CPU int8 for this process (%s)", type(exc).__name__)
                try:
                    return self._run(data, language)
                except Exception as cpu_exc:
                    raise ProviderError("local_inference_failed", "stt", retryable=True) from cpu_exc
            raise ProviderError("local_inference_failed", "stt", retryable=True) from exc

    async def transcribe(self, wav_bytes: bytes, language: Language) -> TranscriptionResult:
        require_language(language, "stt")
        validate_wav(wav_bytes)
        started = perf_counter()
        async with self._semaphore:
            job = asyncio.create_task(asyncio.to_thread(self._transcribe_sync, wav_bytes, language))
            try:
                text = await asyncio.shield(job)
            except asyncio.CancelledError:
                # Do not release the semaphore while uncancellable native inference is still running.
                try:
                    await job
                except Exception:
                    pass
                raise
            return TranscriptionResult(text, "faster_whisper", self.settings.stt_model,
                (perf_counter() - started) * 1000,
                {"device": self._device, "cpu_fallback": self._fallback_used})
