"""
Database Connection Module

Provides SQLAlchemy engine, session factory, and declarative base.
Uses connection pooling for optimal performance.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

from app.config import settings

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for models
Base = declarative_base()


# Event listener to set MySQL charset to utf8mb4
@event.listens_for(Engine, "connect")
def set_mysql_charset(dbapi_conn, connection_record):
    """Set MySQL connection charset to utf8mb4 for full Unicode support."""
    # Only apply to MySQL connections (skip for SQLite in tests)
    if hasattr(dbapi_conn, 'cursor'):
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
        except Exception:
            # Ignore errors for non-MySQL databases (e.g., SQLite)
            pass


def get_db():
    """
    Dependency function to get database session.

    Yields a database session and ensures it's closed after use.
    Use this as a FastAPI dependency in route functions.

    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
