"""Environment configuration; loading settings never opens a DB or initializes providers."""
from pathlib import Path
from typing import Any, Literal
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8",
        case_sensitive=False, extra="ignore",
    )
    host: str = "127.0.0.1"
    port: int = Field(default=5050, ge=1, le=65535)
    db_path: Path = BACKEND_DIR / "tutor.db"
    provider_timeout_s: float = Field(default=60, gt=0, le=300)
    llm_base_url: str = "http://localhost:4000/v1"
    llm_model: str = "qwen3.8-fast"
    llm_api_key: SecretStr = SecretStr("dummy")
    llm_json_mode: Literal["prompt", "json_object", "json_schema"] = "prompt"
    # Merge verbatim: reproduces Klabundo's raw httpx body, NOT SDK extra_body flattening.
    llm_extra_json: dict[str, Any] = Field(default_factory=lambda: {
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
    })
    llm_temperature: float = Field(default=0.2, ge=0, le=2)
    llm_turn_max_tokens: int = Field(default=2048, gt=0)
    llm_report_max_tokens: int = Field(default=2048, gt=0)
    llm_quiz_max_tokens: int = Field(default=4096, gt=0)
    llm_analysis_max_tokens: int = Field(default=2048, gt=0)
    stt_provider: Literal["faster_whisper", "groq"] = "faster_whisper"
    stt_model: str = "large-v3-turbo"
    stt_device: Literal["auto", "cuda", "cpu"] = "auto"
    stt_cpu_threads: int = Field(default=6, ge=1)
    groq_api_key: SecretStr = SecretStr("")
    groq_base_url: str = "https://api.groq.com/openai/v1"
    tts_provider: Literal["edge", "deepinfra"] = "edge"
    edge_voice_en: str = "en-US-AndrewNeural"
    edge_voice_de: str = "de-DE-ConradNeural"
    edge_rate: str = "+2%"
    edge_volume: str = "+4%"
    deepinfra_api_key: SecretStr = SecretStr("")
    deepinfra_base_url: str = "https://api.deepinfra.com/v1/inference"
    tts_model: str = "ResembleAI/chatterbox-multilingual"
    deepinfra_voice_en: str | None = None
    deepinfra_voice_de: str | None = None

    @field_validator("llm_extra_json")
    @classmethod
    def protect_contract(cls, value: dict[str, Any]) -> dict[str, Any]:
        reserved = {"model", "messages", "stream", "response_format", "max_tokens", "temperature"}
        if reserved.intersection(value):
            raise ValueError("LLM_EXTRA_JSON may not override model/messages/stream/format/token budget/temperature")
        return value

    @field_validator("db_path")
    @classmethod
    def resolve_db_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else BACKEND_DIR / value

    @field_validator("llm_base_url", "groq_base_url", "deepinfra_base_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        from urllib.parse import urlsplit
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("Provider base URL must be an HTTP(S) URL without query/fragment")
        return value.rstrip("/")
