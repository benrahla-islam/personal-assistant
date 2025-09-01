"""
Database connection and initialization module.
Handles database setup and provides connection utilities.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .models import Base, create_database_engine, create_tables
from config import get_logger

logger = get_logger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///personal_assistant.db")

# Global variables for database connection
engine = None
SessionFactory = None


def initialize_database():
    """Initialize the database connection and create tables if needed."""
    global engine, SessionFactory
    
    if engine is None:
        logger.info(f"Initializing database: {DATABASE_URL}")
        engine = create_database_engine(DATABASE_URL)
        create_tables(engine)
        SessionFactory = sessionmaker(bind=engine)
        logger.info("Database initialized successfully")
    
    return engine, SessionFactory


def get_database_engine():
    """Get the database engine, initializing if needed."""
    if engine is None:
        initialize_database()
    return engine


def get_session_factory():
    """Get the session factory, initializing if needed.""" 
    if SessionFactory is None:
        initialize_database()
    return SessionFactory


@contextmanager
def get_db_session():
    """Get a database session with automatic cleanup."""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_database_connection_string():
    """Get the database connection string for LangChain tools."""
    return DATABASE_URL


# Initialize on import
initialize_database()
