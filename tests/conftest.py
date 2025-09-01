"""
Shared test fixtures and configuration for the personal assistant test suite.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.models import Base, create_database_engine, create_tables, get_session_factory
from agent.tools.planner_tools.database_tools import get_database_tools


@pytest.fixture(scope="session")
def test_database_engine():
    """Create a test database engine for the session."""
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db_path = tmp.name
    
    # Create engine and tables
    engine = create_database_engine(f'sqlite:///{test_db_path}')
    create_tables(engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@pytest.fixture
def test_session(test_database_engine):
    """Create a fresh database session for each test."""
    SessionFactory = get_session_factory(test_database_engine)
    session = SessionFactory()
    
    yield session
    
    # Cleanup after test - rollback and close
    session.rollback()
    session.close()
    
    # Clear all data between tests for complete isolation
    with test_database_engine.connect() as conn:
        trans = conn.begin()
        try:
            # Delete all data from all tables (in reverse dependency order)
            conn.execute(text("DELETE FROM habit_schedule_items"))
            conn.execute(text("DELETE FROM task_schedule_items"))
            conn.execute(text("DELETE FROM habit_completions"))
            conn.execute(text("DELETE FROM task_completions"))
            conn.execute(text("DELETE FROM habit_tags"))
            conn.execute(text("DELETE FROM task_tags"))
            conn.execute(text("DELETE FROM habit_reminders"))
            conn.execute(text("DELETE FROM task_reminders"))
            conn.execute(text("DELETE FROM time_blocks"))
            conn.execute(text("DELETE FROM daily_schedules"))
            conn.execute(text("DELETE FROM habits"))
            conn.execute(text("DELETE FROM tasks"))
            conn.execute(text("DELETE FROM tags"))
            trans.commit()
        except Exception:
            trans.rollback()
            raise


@pytest.fixture
def database_tools():
    """Get the database tools for testing."""
    return get_database_tools()


@pytest.fixture
def mock_telegram_client():
    """Mock Telegram client for testing."""
    with patch('telegram_scraper.collector.TelegramCollector') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_telegram_bot_token():
    """Mock Telegram bot token environment variable."""
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
        yield 'test_token_123'


@pytest.fixture
def mock_todoist_token():
    """Mock Todoist API token environment variable.""" 
    with patch.dict(os.environ, {'TODOIST_TOKEN': 'test_todoist_token_123'}):
        yield 'test_todoist_token_123'


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all tests."""
    # Ensure we're in test mode
    with patch.dict(os.environ, {'TESTING': 'true'}):
        yield


@pytest.fixture
def sample_habit_data():
    """Sample habit data for testing."""
    return {
        "name": "Morning Exercise",
        "frequency_type": "daily",
        "estimated_duration": 30,
        "priority_level": 8,
        "is_active": True
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "title": "Complete project report",
        "description": "Write the quarterly progress report",
        "due_date": "2025-09-15",
        "priority_level": 7,
        "status": "pending"
    }
