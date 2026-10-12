import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Some hosts (Heroku, older Render/Neon links) give "postgres://", which SQLAlchemy 2 rejects.
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = "postgresql://" + settings.DATABASE_URL[len("postgres://"):]

# Configure connect_args for SQLite if applicable
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a SQLAlchemy database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> dict:
    """Executes a simple connectivity query against the database engine."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        dialect_name = engine.dialect.name
        return {
            "connected": True,
            "dialect": dialect_name,
            "url": settings.DATABASE_URL.split("@")[-1]  # Hide credentials if any
        }
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return {
            "connected": False,
            "error": str(e)
        }
