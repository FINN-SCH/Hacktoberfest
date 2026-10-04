"""Safe, typed upstream failures. Never expose provider bodies, keys or transcripts."""
from typing import Any
import httpx

class ProviderError(Exception):
    def __init__(self, code: str, stage: str, *, retryable: bool = False, status_code: int | None = None):
        self.code = code
        self.stage = stage
        self.retryable = retryable
        self.status_code = status_code
        super().__init__(f"{stage} provider: {code}")

async def post(client: httpx.AsyncClient, url: str, *, stage: str, timeout: float, **kwargs: Any) -> httpx.Response:
    try:
        response = await client.post(url, timeout=timeout, **kwargs)
    except httpx.TimeoutException as exc:
        raise ProviderError("timeout", stage, retryable=True) from exc
    except httpx.RequestError as exc:
        raise ProviderError("unavailable", stage, retryable=True) from exc
    if not response.is_success:
        status = response.status_code
        if status in (401, 403):
            code, retryable = "authentication", False
        elif status == 429:
            code, retryable = "rate_limit", True
        elif status >= 500:
            code, retryable = "unavailable", True
        else:
            code, retryable = "bad_request", False
        raise ProviderError(code, stage, retryable=retryable, status_code=status)
    return response

def json_object(response: httpx.Response, stage: str) -> dict[str, Any]:
    try:
        data = response.json()
    except (ValueError, UnicodeError) as exc:
        raise ProviderError("invalid_response", stage, retryable=True) from exc
    if not isinstance(data, dict):
        raise ProviderError("invalid_response", stage, retryable=True)
    return data

def require_language(language: str, stage: str) -> None:
    if language not in ("de", "en"):
        raise ProviderError("unsupported_language", stage)

def require_text(text: str) -> None:
    if not text.strip():
        raise ProviderError("empty_text", "tts")
