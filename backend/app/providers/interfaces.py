"""Frozen Step A contracts. Services own JSON validation, repair and persistence."""
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Protocol, Sequence

Language = Literal["de", "en"]
Purpose = Literal["turn", "report", "quiz", "analysis"]

@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    provider: str
    model: str
    elapsed_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CompletionResult:
    content: str
    provider: str
    model: str
    elapsed_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class SpeechResult:
    audio: bytes
    media_type: str
    provider: str
    model: str
    elapsed_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

class STTProvider(Protocol):
    async def transcribe(self, wav_bytes: bytes, language: Language) -> TranscriptionResult: ...

class LLMProvider(Protocol):
    async def complete(
        self, messages: Sequence[Mapping[str, str]], *,
        schema: dict[str, Any], purpose: Purpose,
    ) -> CompletionResult: ...

class TTSProvider(Protocol):
    async def synthesize(self, text: str, language: Language) -> SpeechResult: ...
