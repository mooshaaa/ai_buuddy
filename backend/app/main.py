from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import agent, tools
from .db import get_db, init_db
from .llm import describe_provider, get_provider
from .models import Action, Stage, StageProgress, User
from .policy import PermissionDenied
from .schemas import (ActionCardBlock, ChatRequest, ChatResponse, StageOut,
                      StagesResponse, UserBody, UserOut)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI-buddy", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    return user


@app.get("/health")
def health():
    return {"status": "ok", "llm": describe_provider()}


@app.get("/api/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_db)):
    user = _user(db, body.user_id)
    return ChatResponse(blocks=agent.handle_message(db, user, body.message, get_provider()))


@app.get("/api/stages", response_model=StagesResponse)
def stages(user_id: str, db: Session = Depends(get_db)):
    user = _user(db, user_id)
    rows = (
        db.query(Stage, StageProgress.done)
        .join(StageProgress, StageProgress.stage_id == Stage.id)
        .filter(StageProgress.user_id == user.id, Stage.role == user.role)
        .order_by(Stage.id)
        .all()
    )
    items = [StageOut(id=s.id, period=s.period, title=s.title, description=s.description, done=d) for s, d in rows]
    return StagesResponse(stages=items, done=sum(i.done for i in items), total=len(items))


@app.post("/api/stages/{stage_id}/toggle", response_model=StagesResponse)
def toggle_stage(stage_id: int, body: UserBody, db: Session = Depends(get_db)):
    progress = db.get(StageProgress, (body.user_id, stage_id))
    if not progress:
        raise HTTPException(404, "Этап не найден")
    progress.done = not progress.done
    db.commit()
    return stages(body.user_id, db)


def _owned_action(db: Session, action_id: int, user_id: str) -> Action:
    action = db.get(Action, action_id)
    if not action:
        raise HTTPException(404, "Действие не найдено")
    if action.user_id != user_id:
        raise HTTPException(403, "Это действие принадлежит другому пользователю")
    return action


@app.post("/api/actions/{action_id}/confirm", response_model=ActionCardBlock)
def confirm_action(action_id: int, body: UserBody, db: Session = Depends(get_db)):
    action = _owned_action(db, action_id, body.user_id)
    if action.status != "needs_confirmation":
        return agent.to_card(action)
    user = _user(db, body.user_id)
    try:
        action.result = tools.execute(db, user, action.name, action.params)
    except PermissionDenied as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    action.status = "done"
    db.commit()
    return agent.to_card(action)


@app.post("/api/actions/{action_id}/cancel", response_model=ActionCardBlock)
def cancel_action(action_id: int, body: UserBody, db: Session = Depends(get_db)):
    action = _owned_action(db, action_id, body.user_id)
    if action.status == "needs_confirmation":
        action.status = "rejected"
        db.commit()
    return agent.to_card(action)
