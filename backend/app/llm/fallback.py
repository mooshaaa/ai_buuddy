import logging

from ..models import User
from .base import Intent, LLMProvider

log = logging.getLogger("ai_buddy.llm")


class FallbackProvider:
    """Основной провайдер, а при любом сбое запасной (заглушка), чтобы интерфейс всегда отвечал."""

    def __init__(self, primary: LLMProvider, backup: LLMProvider):
        self.primary = primary
        self.backup = backup

    def parse(self, user: User, message: str) -> Intent:
        try:
            return self.primary.parse(user, message)
        except Exception as e:  # noqa: BLE001
            log.warning("LLM недоступна, используем заглушку: %s", e)
            intent = self.backup.parse(user, message)
            intent.note = f"{type(e).__name__}: {e}"[:200]
            return intent
