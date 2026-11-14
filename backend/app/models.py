from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))  # intern | mentor


class Stage(Base):
    """Пункт чек-листа адаптации. role — для кого пункт."""

    __tablename__ = "stages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(50))
    position: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")


class StageProgress(Base):
    __tablename__ = "stage_progress"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"), primary_key=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)


class Action(Base):
    """Действие, которое предложил агент и которое ждёт подтверждения."""

    __tablename__ = "actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(50))
    params: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="needs_confirmation")
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Absence(Base):
    """Таблица мок-сервиса отсутствий."""

    __tablename__ = "absences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    date: Mapped[str] = mapped_column(String(10))
    kind: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Message(Base):
    """История диалога. archived=True после «Новый диалог»: в контекст и интерфейс не попадает, но остаётся для метрик."""

    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # user | assistant
    text: Mapped[str] = mapped_column(Text, default="")  # текстовое представление для модели
    blocks: Mapped[list] = mapped_column(JSON, default=list)  # блоки для показа в интерфейсе
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
