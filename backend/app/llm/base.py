"""Интерфейс провайдера. Модель (или заглушка) только понимает запрос и извлекает параметры.
Вызов инструментов и проверка прав остаются в коде агента."""
from dataclasses import dataclass, field
from typing import Protocol

from ..models import User


@dataclass
class Intent:
    name: str  # create_absence | show_stages | team_progress | faq | unknown
    params: dict = field(default_factory=dict)
    text: str = ""


class LLMProvider(Protocol):
    def parse(self, user: User, message: str) -> Intent: ...
