"""SQLAlchemy engine + session factory + declarative Base.

Sync engine, sync sessions. Matches the pattern used by rfq_manager_ms.
SQLite gets check_same_thread=False so FastAPI's thread pool can share
the connection across the request handler call chain.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config.settings import settings


_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_session():
    """FastAPI dependency. Yields a session, always closes after the request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
