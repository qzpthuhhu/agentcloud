"""Database setup."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings

# Connect args for SQLite
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Session:
    """FastAPI dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Used at startup for SQLite dev mode."""
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)