"""Кольцевой буфер последних событий чата для отладки (живёт в памяти процесса)."""
from collections import deque

_events: deque[dict] = deque(maxlen=100)


def record(event: dict) -> None:
    _events.append(event)


def recent(limit: int = 50) -> list[dict]:
    return list(_events)[-limit:][::-1]  # новые сверху


def clear() -> None:
    _events.clear()
