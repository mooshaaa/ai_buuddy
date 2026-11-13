import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    # stub | openai_compat
    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_fallback_model: str = os.getenv("LLM_FALLBACK_MODEL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "15"))
    # DEBUG=1: показывать отладку в ответах API и открыть /api/debug/events (только для разработки)
    debug: bool = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")


settings = Settings()
