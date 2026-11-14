"""Контракт между бэкендом и фронтендом: ответ агента — список типизированных блоков."""
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ErrorBlock(BaseModel):
    type: Literal["error"] = "error"
    text: str


class ActionCardBlock(BaseModel):
    type: Literal["action_card"] = "action_card"
    action_id: int
    action: str
    title: str
    params: dict
    status: Literal["needs_confirmation", "done", "rejected"]
    result: Optional[dict] = None


class SourceItem(BaseModel):
    id: str
    title: str
    source: str
    synthetic: bool = False


class SourceBlock(BaseModel):
    type: Literal["source"] = "source"
    items: list[SourceItem]


Block = Annotated[Union[TextBlock, ErrorBlock, ActionCardBlock, SourceBlock], Field(discriminator="type")]


class ChatRequest(BaseModel):
    user_id: str
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    blocks: list[Block]
    debug: Optional[dict] = None  # заполняется только при DEBUG=1


class HistoryMessage(BaseModel):
    id: int
    role: Literal["user", "bot"]
    blocks: list[Block]


class HistoryResponse(BaseModel):
    messages: list[HistoryMessage]


class UserOut(BaseModel):
    id: str
    name: str
    role: str


class StageOut(BaseModel):
    id: int
    period: str
    title: str
    description: str
    done: bool


class StagesResponse(BaseModel):
    stages: list[StageOut]
    done: int
    total: int


class UserBody(BaseModel):
    user_id: str
