"""Database connection management with proper session lifecycle."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from config.settings import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )
except Exception as e:
    logger.warning(f"Database engine creation failed: {e}")
    engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None


def init_db():
    """Create all database tables."""
    if engine is None:
        logger.warning("Database not available — skipping table creation")
        return
    from database.schema import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


@contextmanager
def get_db():
    """Context manager for database sessions. Properly closes on exit."""
    if SessionLocal is None:
        raise RuntimeError("Database not available")
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()