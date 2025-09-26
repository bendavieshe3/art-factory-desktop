"""
Fixtures for model tests.
"""

import pytest

from app.models.database import DatabaseManager


@pytest.fixture(scope="function")
def db_manager():
    """Create a test database manager with in-memory SQLite."""
    manager = DatabaseManager("sqlite:///:memory:", echo=False)
    manager.init()
    manager.create_all()
    yield manager
    manager.close()


@pytest.fixture(scope="function")
def session(db_manager):
    """Create a database session for testing."""
    with db_manager.session_scope() as session:
        yield session
