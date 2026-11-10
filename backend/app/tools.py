"""Мок корпоративных сервисов. Позже каждый инструмент заменяется MCP-сервером,
а реестр TOOLS и функция execute остаются точкой подключения."""
from datetime import date

from sqlalchemy.orm import Session

from .models import Absence, Stage, StageProgress, User
from .policy import assert_allowed

KINDS = {"day_off": "отгул", "vacation": "отпуск"}


def create_absence(db: Session, user: User, params: dict) -> dict:
    try:
        day = date.fromisoformat(params["date"])
    except (KeyError, ValueError):
        raise ValueError("Некорректная дата, нужен формат ГГГГ-ММ-ДД")
    kind = params.get("kind", "day_off")
    if kind not in KINDS:
        raise ValueError("Неизвестный тип отсутствия")
    absence = Absence(user_id=user.id, date=day.isoformat(), kind=kind)
    db.add(absence)
    db.flush()
    return {"request_id": f"ABS-{absence.id:04d}", "status": "submitted", "date": absence.date}


def view_team_progress(db: Session, user: User, params: dict) -> dict:
    members = []
    for member in db.query(User).filter(User.role == "intern").all():
        base = db.query(StageProgress).join(Stage, Stage.id == StageProgress.stage_id).filter(
            StageProgress.user_id == member.id, Stage.role == "intern")
        members.append({
            "name": member.name,
            "done": base.filter(StageProgress.done.is_(True)).count(),
            "total": base.count(),
        })
    return {"members": members}


TOOLS = {"create_absence": create_absence, "view_team_progress": view_team_progress}


def execute(db: Session, user: User, name: str, params: dict) -> dict:
    assert_allowed(user.role, name)
    return TOOLS[name](db, user, params)
