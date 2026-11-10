"""Заглушка без LLM: ключевые слова и разбор даты. Работает всегда, нужна для тестов и запуска без ключа."""
import re
from datetime import date, timedelta

from .. import kb
from ..models import User
from .base import Intent

MONTH_STEMS = ["январ", "феврал", "март", "апрел", "ма", "июн", "июл", "август", "сентябр", "октябр", "ноябр", "декабр"]
MONTH_IDX = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10, 12: 11}


def parse_date(text: str, today: date | None = None) -> date | None:
    today = today or date.today()
    low = text.lower()
    if "послезавтра" in low:
        return today + timedelta(days=2)
    if "завтра" in low:
        return today + timedelta(days=1)
    m = re.search(r"(\d{1,2})\s+([а-я]+)", low)
    if m:
        day, word = int(m.group(1)), m.group(2)
        for month, idx in MONTH_IDX.items():
            if word.startswith(MONTH_STEMS[idx]):
                return _build(today, month, day)
    m = re.search(r"(\d{1,2})\.(\d{1,2})", low)
    if m:
        return _build(today, int(m.group(2)), int(m.group(1)))
    return None


def _build(today: date, month: int, day: int) -> date | None:
    try:
        d = date(today.year, month, day)
    except ValueError:
        return None
    return d if d >= today else date(today.year + 1, month, day)


class StubProvider:
    def parse(self, user: User, message: str) -> Intent:
        low = message.lower()
        if any(w in low for w in ("отгул", "выходн", "отпуск")):
            kind = "vacation" if "отпуск" in low else "day_off"
            d = parse_date(message)
            return Intent("create_absence", {"date": d.isoformat() if d else None, "kind": kind})
        if any(w in low for w in ("прогресс стажёр", "прогресс стажер", "прогресс команд", "как справляется")):
            return Intent("team_progress")
        if any(w in low for w in ("этап", "что делать", "что мне делать", "план", "следующий шаг")):
            return Intent("show_stages")
        answer = kb.lookup(message)
        if answer:
            return Intent("faq", text=answer)
        return Intent("unknown")
