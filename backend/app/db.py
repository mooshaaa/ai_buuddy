from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models import Base

_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from .seed import seed

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
