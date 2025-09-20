"""Pytest configuration and fixtures for Art Factory tests."""

import sys
import os
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

# Add app directory to path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session.

    This fixture is required for testing Qt components.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app here - pytest-qt handles it


@pytest.fixture
def qtbot(qapp, qtbot):
    """Ensure qtbot has access to the QApplication instance.

    This extends the pytest-qt qtbot fixture.
    """
    return qtbot


@pytest.fixture(autouse=True)
def reset_signal_bus():
    """Reset the signal bus before each test.

    This ensures tests don't interfere with each other.
    """
    from signals import signal_bus

    yield
    signal_bus.reset()


@pytest.fixture
def debug_mode(monkeypatch):
    """Enable debug mode for a test."""
    monkeypatch.setenv("AF_DEBUG", "1")
    yield
    monkeypatch.delenv("AF_DEBUG", raising=False)