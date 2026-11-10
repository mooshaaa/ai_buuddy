import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")


settings = Settings()
