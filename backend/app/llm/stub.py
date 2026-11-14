"""Заглушка без LLM: ключевые слова и разбор даты. Работает всегда, нужна для тестов и запуска без ключа."""
import re
from datetime import date, timedelta

from .. import kb
from ..models import User
from ..kb import Entry
from .base import Intent, KbResult

MONTH_STEMS = ["январ", "феврал", "март", "апрел", "ма", "июн", "июл", "август", "сентябр", "октябр", "ноябр", "декабр"]
WEEKDAY_STEMS = ["понедельник", "вторник", "сред", "четверг", "пятниц", "суббот", "воскресень"]
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
    m = re.search(r"\b(?:в|во|на)\s+(?:эту\s+|следующ\w+\s+)?(понедельник|вторник|сред\w|четверг|пятниц\w|суббот\w|воскресень\w)", low)
    if m:
        target = next(i for i, stem in enumerate(WEEKDAY_STEMS) if m.group(1).startswith(stem))
        return today + timedelta(days=(target - today.weekday() - 1) % 7 + 1)
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
        if kb.search(message, kb.ENTRIES):
            return Intent("faq")
        return Intent("unknown")

    def answer(self, user: User, question: str, entries: list[Entry]) -> KbResult:
        hit = kb.search(question, entries)
        if not hit:
            return KbResult(found=False)
        return KbResult(found=True, text=hit.text, source_ids=[hit.id])
