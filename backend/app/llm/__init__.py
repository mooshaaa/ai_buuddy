from ..config import settings
from .base import LLMProvider
from .stub import StubProvider


def get_provider() -> LLMProvider:
    """Сюда добавляется реальная модель: новая ветка и класс с методом parse()."""
    if settings.llm_provider == "stub":
        return StubProvider()
    raise RuntimeError(f"Неизвестный LLM_PROVIDER: {settings.llm_provider}")
