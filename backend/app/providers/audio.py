import io
import wave
from .errors import ProviderError

def validate_wav(data: bytes) -> None:
    if len(data) > 16_000 * 2 * 180 + 4096:
        raise ProviderError("audio_too_large", "stt")
    try:
        with wave.open(io.BytesIO(data), "rb") as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getcomptype()) != (1, 2, 16000, "NONE"):
                raise ValueError("Expected mono PCM16 16kHz")
            count = audio.getnframes()
            if count <= 0 or count > 16000 * 180 or len(audio.readframes(count)) != count * 2:
                raise ValueError("Empty, oversized or truncated audio")
    except (wave.Error, EOFError, ValueError) as exc:
        raise ProviderError("invalid_audio", "stt") from exc
