"""Интерфейс провайдера. Модель (или заглушка) только понимает запрос и извлекает параметры.
Вызов инструментов и проверка прав остаются в коде агента."""
from dataclasses import dataclass, field
from typing import Protocol

from ..kb import Entry
from ..models import User


@dataclass
class Intent:
    name: str  # create_absence | show_stages | team_progress | faq | unknown
    params: dict = field(default_factory=dict)
    text: str = ""
    source: str = "stub"  # stub | llm
    model: str = ""
    note: str = ""  # причина отката на заглушку


@dataclass
class KbResult:
    found: bool
    text: str = ""
    source_ids: list[str] = field(default_factory=list)
    source: str = "stub"  # stub | llm
    model: str = ""
    note: str = ""


class LLMProvider(Protocol):
    def parse(self, user: User, message: str) -> Intent: ...

    def answer(self, user: User, question: str, entries: list[Entry]) -> KbResult: ...
