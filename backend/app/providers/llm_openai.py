import json
from time import perf_counter
from typing import Any, Mapping, Sequence
import httpx
from app.config import Settings
from .errors import ProviderError, json_object, post
from .interfaces import CompletionResult, Purpose

class OpenAICompatibleLLM:
    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self.settings, self.client = settings, client

    async def complete(self, messages: Sequence[Mapping[str, str]], *,
                       schema: dict[str, Any], purpose: Purpose) -> CompletionResult:
        started = perf_counter()
        s = self.settings
        if purpose not in ("turn", "report", "quiz", "analysis"):
            raise ProviderError("invalid_purpose", "llm")
        if not s.llm_api_key.get_secret_value():
            raise ProviderError("missing_credentials", "llm")
        instructions = ("Return exactly one JSON object matching this JSON schema. "
                        "No markdown, reasoning or surrounding prose. Schema: " +
                        json.dumps(schema, ensure_ascii=False, separators=(",", ":")))
        body: dict[str, Any] = {
            **s.llm_extra_json,
            "model": s.llm_model,
            "messages": [{"role": "system", "content": instructions}, *[dict(m) for m in messages]],
            "temperature": s.llm_temperature,
            "max_tokens": getattr(s, f"llm_{purpose}_max_tokens"),
            "stream": False,
        }
        if s.llm_json_mode == "json_object":
            body["response_format"] = {"type": "json_object"}
        elif s.llm_json_mode == "json_schema":
            body["response_format"] = {"type": "json_schema", "json_schema": {
                "name": f"tutor_{purpose}", "strict": True, "schema": schema}}
        response = await post(self.client, f"{s.llm_base_url}/chat/completions", stage="llm",
                              timeout=s.provider_timeout_s, json=body,
                              headers={"Authorization": f"Bearer {s.llm_api_key.get_secret_value()}"})
        data = json_object(response, "llm")
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("invalid_response", "llm", retryable=True) from exc
        if finish == "length":
            raise ProviderError("truncated", "llm", retryable=True)
        if finish in ("content_filter", "tool_calls") or not isinstance(content, str) or not content.strip():
            raise ProviderError("invalid_response", "llm", retryable=True)
        return CompletionResult(content, "openai_compatible", s.llm_model,
                                (perf_counter() - started) * 1000,
                                {"finish_reason": finish, "usage": data.get("usage", {})})
