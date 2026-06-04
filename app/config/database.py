from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import contextmanager

from app.config.settings import (
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_NAME,
    DATABASE_USER,
    DATABASE_PASSWORD,
)

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}"
    f"/{DATABASE_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=15,       # Keeps 15 connections ready
    max_overflow=30,    # Allows up to 30 extra connections during peaks
    pool_timeout=45,    # Waits 45s for a connection before failing
    pool_recycle=3600,  # Refresh connections every hour to avoid Supabase timeouts
    pool_pre_ping=True  # Check if connection is alive before using it
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


@contextmanager
def get_session():
    """Context manager for database sessions to ensure cleanup and performance."""
    session = SessionLocal()
    try:
        yield session
        if session.new or session.dirty or session.deleted:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()