"""
Database Connection Manager
===========================

SQLAlchemy database connection and session management.
"""

import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base

logger = logging.getLogger(__name__)

# Global database instance
_db_instance: Optional["Database"] = None


class Database:
    """Database connection manager."""
    
    def __init__(
        self,
        database_url: str = "sqlite:///./data/otto.db",
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10
    ):
        self.database_url = database_url
        
        # For SQLite, we need special handling
        if database_url.startswith("sqlite"):
            # Ensure data directory exists
            if ":///" in database_url:
                db_path = database_url.split(":///")[1]
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # SQLite with check_same_thread=False for async compatibility
            self.engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool  # Single connection for SQLite
            )
            
            # Enable foreign keys for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")  # Better concurrency
                cursor.close()
        else:
            # PostgreSQL or other databases
            self.engine = create_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True  # Verify connections before use
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database initialized: {database_url.split('://')[0]}")
    
    def create_tables(self):
        """Create all tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created/verified")
    
    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[Session, None]:
        """Async context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def session_scope(self):
        """Synchronous context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_db() -> Database:
    """Get or create the global database instance."""
    global _db_instance
    
    if _db_instance is None:
        # Get database URL from environment or use default
        import os
        database_url = os.getenv("DATABASE_URL", "sqlite:///./data/otto.db")
        _db_instance = Database(database_url=database_url)
        _db_instance.create_tables()
    
    return _db_instance


def init_db(database_url: Optional[str] = None) -> Database:
    """Initialize the database with optional custom URL."""
    global _db_instance
    
    if database_url:
        _db_instance = Database(database_url=database_url)
    else:
        _db_instance = get_db()
    
    _db_instance.create_tables()
    return _db_instance


def get_session() -> Session:
    """Convenience function to get a database session."""
    return get_db().get_session()
