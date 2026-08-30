"""
Database engine and session management.

One engine per process, one session per request. FastAPI's dependency
injection (get_db) hands each request its own session and always closes
it afterward, even if the request raises — this avoids connection leaks
under load, which a plain global session would cause.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
