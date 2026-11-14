"""Память диалога: хранится на бэкенде, привязана к пользователю."""
from sqlalchemy.orm import Session

from .models import Message

MAX_TURNS = 8        # сколько последних сообщений видит модель
MAX_CHARS = 1500     # обрезка каждого сообщения в контексте
RESTORE_LIMIT = 50   # сколько сообщений показываем после перезагрузки страницы


def render(blocks: list[dict]) -> str:
    """Текст для модели из блоков ответа. Ошибки в контекст не попадают."""
    parts: list[str] = []
    for b in blocks:
        kind = b.get("type")
        if kind == "text":
            parts.append(b["text"])
        elif kind == "action_card":
            parts.append(f"[карточка: {b['title']}, параметры: {b['params']}]")
        elif kind == "source":
            parts.append("[источники: " + ", ".join(i["title"] for i in b["items"]) + "]")
    return "\n".join(parts)


def load(db: Session, user_id: str, limit: int = MAX_TURNS) -> list[dict]:
    """Последние сообщения в хронологическом порядке: [{"role": "user"|"assistant", "text": ...}]."""
    rows = (
        db.query(Message)
        .filter(Message.user_id == user_id, Message.archived.is_(False))
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    return [{"role": r.role, "text": r.text[:MAX_CHARS]} for r in reversed(rows) if r.text]


def save_turn(db: Session, user_id: str, user_text: str, bot_blocks: list[dict]) -> None:
    db.add(Message(user_id=user_id, role="user", text=user_text,
                   blocks=[{"type": "text", "text": user_text}]))
    db.add(Message(user_id=user_id, role="assistant", text=render(bot_blocks), blocks=bot_blocks))
    db.commit()


def restore(db: Session, user_id: str, limit: int = RESTORE_LIMIT) -> list[dict]:
    rows = (
        db.query(Message)
        .filter(Message.user_id == user_id, Message.archived.is_(False))
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {"id": r.id, "role": "user" if r.role == "user" else "bot", "blocks": r.blocks}
        for r in reversed(rows)
    ]


def reset(db: Session, user_id: str) -> int:
    n = (
        db.query(Message)
        .filter(Message.user_id == user_id, Message.archived.is_(False))
        .update({Message.archived: True})
    )
    db.commit()
    return n
