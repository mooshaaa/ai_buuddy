"""Оркестратор: провайдер понимает запрос, агент проверяет права и вызывает инструменты."""
import time

from sqlalchemy.orm import Session

from . import tools
from .llm.base import LLMProvider
from .models import Action, Stage, StageProgress, User
from .policy import PermissionDenied, is_allowed
from .schemas import ActionCardBlock, Block, ErrorBlock, TextBlock

ACTION_TITLES = {"create_absence": "Заявка на отгул"}

HELP = (
    "Я помогаю с адаптацией. Могу оформить отгул, показать твои этапы и ответить на вопросы "
    "про доступы, 1:1, экватор и защиту данных. Например: «Хочу отгул 20 ноября»."
)


def to_card(action: Action) -> ActionCardBlock:
    return ActionCardBlock(
        action_id=action.id,
        action=action.name,
        title=ACTION_TITLES.get(action.name, action.name),
        params=action.params,
        status=action.status,
        result=action.result,
    )


def stage_summary(db: Session, user: User) -> str:
    rows = (
        db.query(Stage, StageProgress.done)
        .join(StageProgress, StageProgress.stage_id == Stage.id)
        .filter(StageProgress.user_id == user.id, Stage.role == user.role)
        .order_by(Stage.id)
        .all()
    )
    total = len(rows)
    done = sum(1 for _, d in rows if d)
    nxt = next((s for s, d in rows if not d), None)
    if nxt is None:
        return f"Все {total} шагов выполнены."
    return f"Выполнено {done} из {total}. Следующий шаг: «{nxt.title}» ({nxt.period}). {nxt.description}"


def handle_message(
    db: Session, user: User, message: str, provider: LLMProvider, trace: dict | None = None
) -> list[Block]:
    start = time.perf_counter()
    try:
        intent = provider.parse(user, message)
    except Exception as e:
        if trace is not None:
            trace.update(intent="error", source="error", model="", note=str(e)[:200],
                         latency_ms=round((time.perf_counter() - start) * 1000))
        return [ErrorBlock(text="Не получилось обработать запрос. Попробуй ещё раз или переформулируй.")]
    if trace is not None:
        trace.update(intent=intent.name, source=intent.source, model=intent.model, note=intent.note,
                     latency_ms=round((time.perf_counter() - start) * 1000))

    if intent.name == "create_absence":
        if not is_allowed(user.role, "create_absence"):
            return [ErrorBlock(text="У тебя нет прав на оформление отсутствий.")]
        if not intent.params.get("date"):
            return [TextBlock(text="На какую дату оформить отгул? Напиши, например: «20 ноября» или «завтра».")]
        action = Action(user_id=user.id, name="create_absence", params=intent.params)
        db.add(action)
        db.commit()
        return [
            TextBlock(text=f"Подготовил заявку на {intent.params['date']}. Проверь данные и подтверди."),
            to_card(action),
        ]

    if intent.name == "show_stages":
        return [TextBlock(text=stage_summary(db, user))]

    if intent.name == "team_progress":
        try:
            result = tools.execute(db, user, "view_team_progress", {})
        except PermissionDenied:
            return [ErrorBlock(text="Прогресс стажёров доступен только наставникам. Спроси об этом у своего наставника.")]
        lines = [f"{m['name']}: {m['done']} из {m['total']}" for m in result["members"]]
        return [TextBlock(text="Прогресс стажёров:\n" + "\n".join(lines))]

    if intent.name == "faq":
        return [TextBlock(text=intent.text)]

    return [TextBlock(text=HELP)]
