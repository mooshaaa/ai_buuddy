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

    def parse(self, user: User, message: str, history: list[dict] | None = None) -> Intent:
        try:
            return self.primary.parse(user, message, history)
        except Exception as e:  # noqa: BLE001
            log.warning("LLM недоступна, используем заглушку: %s", e)
            intent = self.backup.parse(user, message, history)
            intent.note = f"{type(e).__name__}: {e}"[:200]
            return intent

    def answer(
        self, user: User, question: str, entries: list[Entry], history: list[dict] | None = None
    ) -> KbResult:
        try:
            return self.primary.answer(user, question, entries, history)
        except Exception as e:  # noqa: BLE001
            log.warning("LLM недоступна для ответа по базе знаний, используем заглушку: %s", e)
            result = self.backup.answer(user, question, entries, history)
            result.note = f"{type(e).__name__}: {e}"[:200]
            return result
