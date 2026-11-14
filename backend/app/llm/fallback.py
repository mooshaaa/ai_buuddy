import logging

from ..kb import Entry
from ..models import User
from .base import Intent, KbResult, LLMProvider

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

    def answer(self, user: User, question: str, entries: list[Entry]) -> KbResult:
        try:
            return self.primary.answer(user, question, entries)
        except Exception as e:  # noqa: BLE001
            log.warning("LLM недоступна для ответа по базе знаний, используем заглушку: %s", e)
            result = self.backup.answer(user, question, entries)
            result.note = f"{type(e).__name__}: {e}"[:200]
            return result
