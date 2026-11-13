import logging
from functools import lru_cache

from ..config import settings
from .base import LLMProvider
from .fallback import FallbackProvider
from .openai_compat import OpenAICompatProvider
from .stub import StubProvider

log = logging.getLogger("ai_buddy.llm")


@lru_cache(maxsize=1)
def get_provider() -> LLMProvider:
    """stub: без модели. openai_compat: любая OpenAI-совместимая модель, при сбое откат на заглушку."""
    if settings.llm_provider == "stub":
        return StubProvider()
    if settings.llm_provider == "openai_compat":
        if not (settings.llm_base_url and settings.llm_model and settings.llm_api_key):
            log.warning("LLM_BASE_URL, LLM_MODEL или LLM_API_KEY не заданы, работает заглушка")
            return StubProvider()
        return FallbackProvider(
            OpenAICompatProvider(
                settings.llm_base_url,
                settings.llm_api_key,
                settings.llm_model,
                settings.llm_fallback_model,
                settings.llm_timeout,
            ),
            StubProvider(),
        )
    raise RuntimeError(f"Неизвестный LLM_PROVIDER: {settings.llm_provider}")


def describe_provider() -> str:
    """Короткое описание режима для /health: помогает понять, работает модель или заглушка."""
    provider = get_provider()
    if isinstance(provider, StubProvider):
        return "stub"
    return f"openai_compat:{settings.llm_model}"
