"""
Database initialization and connection setup for the Automated Video Generator.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from .models import Base
from ..config.settings import DATABASE_URL, DATABASE_TYPE

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Set up the database engine based on configuration."""
        try:
            if DATABASE_TYPE == 'sqlite':
                # SQLite configuration using Python 3.13's built-in sqlite3
                # No need for pysqlite3 - using built-in support
                self.engine = create_engine(
                    DATABASE_URL,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False  # Set to True for SQL debugging
                )
            elif DATABASE_TYPE == 'postgresql':
                # PostgreSQL configuration
                self.engine = create_engine(
                    DATABASE_URL,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False
                )
            else:
                raise ValueError(f"Unsupported database type: {DATABASE_TYPE}")
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database engine initialized for {DATABASE_TYPE}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic cleanup."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            with self.get_db_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

def get_db() -> Session:
    """Dependency function to get database session."""
    return db_manager.get_session()

def init_database():
    """Initialize the database (create tables, etc.)."""
    try:
        db_manager.create_tables()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def close_database():
    """Close database connections."""
    db_manager.close()
