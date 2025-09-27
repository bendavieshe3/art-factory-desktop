"""Pytest configuration and fixtures for Art Factory tests."""

import sys
import os
import tempfile
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


# Database test fixtures
@pytest.fixture
def db_session():
    """Create test database session."""
    from models.database import init_database, TEST_DATABASE_URL

    db_manager = init_database(TEST_DATABASE_URL, echo=False)
    with db_manager.session_scope() as session:
        yield session


@pytest.fixture
def sample_project(db_session):
    """Create a sample project for testing."""
    from models import Project

    project = Project(
        name="Test Project", description="Test project for service tests", status="active"
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def sample_product(db_session, sample_project):
    """Create a sample product for testing."""
    from models import Product

    # Create a temporary file for the product
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file.write(b"fake image data")
        file_path = temp_file.name

    product = Product(
        project_id=sample_project.id,
        type="image",
        file_path=file_path,
        file_size=len(b"fake image data"),
        width=1024,
        height=1024,
    )

    # Calculate hash
    product.calculate_file_hash()

    db_session.add(product)
    db_session.commit()

    yield product

    # Clean up temp file
    if os.path.exists(file_path):
        os.unlink(file_path)


@pytest.fixture
def sample_order_item(db_session, sample_project):
    """Create a sample order item for testing."""
    from models import Order, OrderItem

    order = Order(
        project_id=sample_project.id,
        provider="replicate",
        model="stability-ai/sdxl",
        model_family="stable-diffusion",
        model_modality="text-to-image",
        base_parameter_set={
            "prompt": "A test image",
            "steps": 20,
            "guidance_scale": 7.5,
        },
    )
    db_session.add(order)
    db_session.flush()

    order_item = OrderItem(
        order_id=order.id,
        sequence_number=1,
        generation_parameter_set={
            "prompt": "A test image",
            "steps": 20,
            "guidance_scale": 7.5,
        },
    )
    db_session.add(order_item)
    db_session.commit()
    return order_item


@pytest.fixture
def sample_order_with_items(db_session, sample_project):
    """Create a sample order with multiple items for testing."""
    from models import Order, OrderItem

    order = Order(
        project_id=sample_project.id,
        provider="replicate",
        model="stability-ai/sdxl",
        model_family="stable-diffusion",
        model_modality="text-to-image",
        base_parameter_set={
            "prompt": "A [red,blue,green] dog",
            "steps": 20,
            "guidance_scale": 7.5,
        },
    )
    db_session.add(order)
    db_session.flush()

    # Create multiple order items
    for i, color in enumerate(["red", "blue", "green"]):
        order_item = OrderItem(
            order_id=order.id,
            sequence_number=i + 1,
            generation_parameter_set={
                "prompt": f"A {color} dog",
                "steps": 20,
                "guidance_scale": 7.5,
            },
        )
        db_session.add(order_item)

    db_session.commit()
    return order
