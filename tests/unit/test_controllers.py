"""
Unit tests for controller layer components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from PyQt6.QtTest import QTest

from app.controllers.main_controller import MainController
from app.controllers.generation_controller import GenerationController
from app.controllers.gallery_controller import GalleryController
from app.controllers.project_controller import ProjectController
from app.controllers.controller_manager import ControllerManager
from app.signals.signal_bus import SignalBus


class TestMainController:
    """Test cases for MainController."""

    def test_main_controller_singleton(self, qtbot):
        """Test that MainController implements singleton pattern."""
        signal_bus = SignalBus()

        controller1 = MainController(signal_bus)
        controller2 = MainController(signal_bus)

        assert controller1 is controller2
        assert MainController._instance is controller1

    def test_main_controller_initialization(self, qtbot):
        """Test MainController initialization."""
        signal_bus = SignalBus()
        controller = MainController(signal_bus)

        assert controller.signal_bus is signal_bus
        assert controller.current_project_id is None
        assert isinstance(controller.application_state, dict)
        assert isinstance(controller.controllers, dict)

    def test_register_controller(self, qtbot):
        """Test registering child controllers."""
        signal_bus = SignalBus()
        main_controller = MainController(signal_bus)

        # Create mock child controller
        child_controller = Mock()
        child_controller.initialize = Mock()

        # Register controller
        main_controller.register_controller("test", child_controller)

        assert "test" in main_controller.controllers
        assert main_controller.controllers["test"] is child_controller
        child_controller.initialize.assert_called_once()

    def test_set_current_project(self, qtbot):
        """Test setting current project."""
        signal_bus = SignalBus()
        controller = MainController(signal_bus)

        # Track signal emissions
        project_changed_signals = []
        signal_bus.domain.project_changed.connect(lambda pid: project_changed_signals.append(pid))

        # Set project
        controller.set_current_project("test-project-123")

        assert controller.current_project_id == "test-project-123"
        assert "test-project-123" in project_changed_signals

    def test_application_state_management(self, qtbot):
        """Test application state get/set operations."""
        signal_bus = SignalBus()
        controller = MainController(signal_bus)

        # Test setting and getting state
        controller.set_application_state("test_key", "test_value")
        assert controller.get_application_state("test_key") == "test_value"

        # Test default value
        assert controller.get_application_state("nonexistent", "default") == "default"


class TestGenerationController:
    """Test cases for GenerationController."""

    def test_generation_controller_initialization(self, qtbot):
        """Test GenerationController initialization."""
        signal_bus = SignalBus()
        controller = GenerationController(signal_bus)

        assert controller.signal_bus is signal_bus
        assert isinstance(controller.active_orders, dict)
        assert isinstance(controller.generation_queue, list)

    def test_parameter_validation(self, qtbot):
        """Test generation parameter validation."""
        signal_bus = SignalBus()
        controller = GenerationController(signal_bus)

        # Valid parameters
        valid_params = {"prompt": "A cat in a hat"}
        assert controller._validate_parameters(valid_params) is True

        # Invalid parameters - missing prompt
        invalid_params = {"steps": 20}
        assert controller._validate_parameters(invalid_params) is False

        # Invalid parameters - empty prompt
        empty_prompt_params = {"prompt": ""}
        assert controller._validate_parameters(empty_prompt_params) is False

    @patch("app.controllers.generation_controller.OrderService")
    def test_generation_request_handling(self, mock_order_service, qtbot):
        """Test handling generation requests."""
        signal_bus = SignalBus()
        controller = GenerationController(signal_bus)

        # Mock main controller with project
        mock_main = Mock()
        mock_main.current_project_id = "test-project"
        controller.setParent(mock_main)

        # Mock order service
        mock_order = Mock()
        mock_order.id = "test-order-123"
        mock_order.items = []
        mock_order_service.return_value.create_order.return_value = mock_order

        # Track signal emissions
        order_created_signals = []
        signal_bus.domain.order_created.connect(lambda oid: order_created_signals.append(oid))

        # Test generation request
        parameters = {"prompt": "A beautiful landscape"}
        controller._on_generation_requested(parameters)

        # Verify order creation
        assert "test-order-123" in controller.active_orders
        assert "test-order-123" in order_created_signals

    def test_generation_queue_management(self, qtbot):
        """Test generation queue operations."""
        signal_bus = SignalBus()
        controller = GenerationController(signal_bus)

        # Mock order data
        controller.active_orders["order-1"] = {"order": Mock(), "status": "created"}

        # Test queueing
        controller._queue_generation("order-1")

        assert "order-1" in controller.generation_queue
        assert controller.active_orders["order-1"]["status"] == "processing"

    def test_generation_status_tracking(self, qtbot):
        """Test generation status tracking."""
        signal_bus = SignalBus()
        controller = GenerationController(signal_bus)

        # Get initial status
        status = controller.get_generation_queue_status()
        assert status["queue_length"] == 0
        assert status["active_orders"] == 0

        # Add active order
        controller.active_orders["test-order"] = {"status": "processing"}
        controller.generation_queue.append("test-order")

        status = controller.get_generation_queue_status()
        assert status["queue_length"] == 1
        assert status["active_orders"] == 1


class TestGalleryController:
    """Test cases for GalleryController."""

    def test_gallery_controller_initialization(self, qtbot):
        """Test GalleryController initialization."""
        signal_bus = SignalBus()
        controller = GalleryController(signal_bus)

        assert controller.signal_bus is signal_bus
        assert isinstance(controller.products, list)
        assert isinstance(controller.selected_products, list)
        assert isinstance(controller.current_filter, dict)

    def test_mock_product_creation(self, qtbot):
        """Test mock product data creation."""
        signal_bus = SignalBus()
        controller = GalleryController(signal_bus)

        products = controller._create_mock_products("test-project")

        assert len(products) == 12  # Should create 12 mock products
        assert all("id" in p for p in products)
        assert all("name" in p for p in products)
        assert all(p["project_id"] == "test-project" for p in products)

    def test_filter_and_search_application(self, qtbot):
        """Test applying filters and search to products."""
        signal_bus = SignalBus()
        controller = GalleryController(signal_bus)

        # Create test products
        products = [
            {
                "id": "1",
                "name": "Cat Image",
                "project_id": "proj1",
                "parameters": {"prompt": "cat"},
            },
            {
                "id": "2",
                "name": "Dog Image",
                "project_id": "proj2",
                "parameters": {"prompt": "dog"},
            },
            {
                "id": "3",
                "name": "Bird Image",
                "project_id": "proj1",
                "parameters": {"prompt": "bird"},
            },
        ]

        # Test search
        controller.search_query = "cat"
        filtered = controller._apply_filters_and_search(products)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "1"

        # Test project filter
        controller.search_query = ""
        controller.current_filter = {"project_id": "proj1"}
        filtered = controller._apply_filters_and_search(products)
        assert len(filtered) == 2
        assert all(p["project_id"] == "proj1" for p in filtered)

    def test_selection_handling(self, qtbot):
        """Test product selection handling."""
        signal_bus = SignalBus()
        controller = GalleryController(signal_bus)

        # Create mock products
        controller.products = [
            {"id": "product-1", "name": "Test 1"},
            {"id": "product-2", "name": "Test 2"},
        ]

        # Test selection change
        controller._on_selection_changed(["product-1", "product-2"])

        assert controller.selected_products == ["product-1", "product-2"]

    def test_file_import_validation(self, qtbot):
        """Test file import validation."""
        signal_bus = SignalBus()
        controller = GalleryController(signal_bus)

        # Test valid image file
        with patch("pathlib.Path.exists", return_value=True):
            result = controller._import_file("/test/image.png", "test-project")
            assert result is True

        # Test non-existent file
        with patch("pathlib.Path.exists", return_value=False):
            result = controller._import_file("/test/missing.png", "test-project")
            assert result is False

    def test_gallery_statistics(self, qtbot):
        """Test gallery statistics calculation."""
        signal_bus = SignalBus()
        controller = GalleryController(signal_bus)

        # Set up test data
        controller.products = [{"id": f"p{i}"} for i in range(5)]
        controller.selected_products = ["p1", "p2"]
        controller.search_query = "test"
        controller.current_filter = {"project_id": "test"}

        stats = controller.get_gallery_stats()

        assert stats["total_products"] == 5
        assert stats["selected_products"] == 2
        assert stats["search_query"] == "test"
        assert stats["current_filter"] == {"project_id": "test"}


class TestProjectController:
    """Test cases for ProjectController."""

    def test_project_controller_initialization(self, qtbot):
        """Test ProjectController initialization."""
        signal_bus = SignalBus()
        controller = ProjectController(signal_bus)

        assert controller.signal_bus is signal_bus
        assert isinstance(controller.projects, list)
        assert controller.current_project is None

    def test_mock_project_creation(self, qtbot):
        """Test mock project data creation."""
        signal_bus = SignalBus()
        controller = ProjectController(signal_bus)

        projects = controller._create_mock_projects()

        assert len(projects) >= 3  # Should create at least 3 mock projects
        assert all("id" in p for p in projects)
        assert all("name" in p for p in projects)
        assert all("status" in p for p in projects)

    def test_project_creation(self, qtbot):
        """Test project creation."""
        signal_bus = SignalBus()
        controller = ProjectController(signal_bus)

        # Track signal emissions
        project_created_signals = []
        signal_bus.domain.project_created.connect(lambda pid: project_created_signals.append(pid))

        # Create project
        project_id = controller.create_project("Test Project", "Test description")

        assert project_id is not None
        assert project_id in project_created_signals
        assert any(p["name"] == "Test Project" for p in controller.projects)

    def test_project_creation_validation(self, qtbot):
        """Test project creation validation."""
        signal_bus = SignalBus()
        controller = ProjectController(signal_bus)

        # Test empty name
        result = controller.create_project("")
        assert result is None

        # Test duplicate name
        controller.create_project("Duplicate")
        result = controller.create_project("Duplicate")
        assert result is None

    def test_project_switching(self, qtbot):
        """Test project switching."""
        signal_bus = SignalBus()
        controller = ProjectController(signal_bus)

        # Create mock project
        mock_project = {"id": "test-project", "name": "Test"}
        controller.projects = [mock_project]

        # Mock main controller
        mock_main = Mock()
        mock_main.set_current_project = Mock()
        controller.setParent(mock_main)

        # Switch to project
        controller.switch_to_project("test-project")

        assert controller.current_project == mock_project
        mock_main.set_current_project.assert_called_with("test-project")

    def test_project_operations(self, qtbot):
        """Test project update, delete, and archive operations."""
        signal_bus = SignalBus()
        controller = ProjectController(signal_bus)

        # Create test project
        project_id = controller.create_project("Test Project")
        assert project_id is not None

        # Test update
        result = controller.update_project(project_id, {"name": "Updated Project"})
        assert result is True

        project = controller._get_project_by_id(project_id)
        assert project["name"] == "Updated Project"

        # Test archive
        result = controller.archive_project(project_id)
        assert result is True

        project = controller._get_project_by_id(project_id)
        assert project["status"] == "archived"

        # Test delete
        result = controller.delete_project(project_id)
        assert result is True

        project = controller._get_project_by_id(project_id)
        assert project is None

    def test_project_statistics(self, qtbot):
        """Test project statistics calculation."""
        signal_bus = SignalBus()
        controller = ProjectController(signal_bus)

        # Create test project
        project_id = controller.create_project("Test Project")
        stats = controller.get_project_statistics(project_id)

        assert stats is not None
        assert "total_products" in stats
        assert "total_orders" in stats
        assert "creation_date" in stats


class TestControllerManager:
    """Test cases for ControllerManager."""

    def test_controller_manager_initialization(self, qtbot):
        """Test ControllerManager initialization."""
        signal_bus = SignalBus()
        manager = ControllerManager(signal_bus)

        assert manager.signal_bus is signal_bus
        assert manager.main_controller is None
        assert not manager._initialized

    def test_controller_initialization_success(self, qtbot):
        """Test successful controller initialization."""
        signal_bus = SignalBus()
        manager = ControllerManager(signal_bus)

        result = manager.initialize_controllers()

        assert result is True
        assert manager._initialized is True
        assert manager.main_controller is not None
        assert manager.generation_controller is not None
        assert manager.gallery_controller is not None
        assert manager.project_controller is not None

    def test_controller_retrieval(self, qtbot):
        """Test getting controllers by name."""
        signal_bus = SignalBus()
        manager = ControllerManager(signal_bus)
        manager.initialize_controllers()

        # Test getting specific controllers
        generation_controller = manager.get_controller("generation")
        assert generation_controller is manager.generation_controller

        gallery_controller = manager.get_controller("gallery")
        assert gallery_controller is manager.gallery_controller

        project_controller = manager.get_controller("project")
        assert project_controller is manager.project_controller

        # Test getting non-existent controller
        nonexistent = manager.get_controller("nonexistent")
        assert nonexistent is None

    def test_controller_status(self, qtbot):
        """Test getting controller status information."""
        signal_bus = SignalBus()
        manager = ControllerManager(signal_bus)

        # Before initialization
        status = manager.get_controller_status()
        assert status["initialized"] is False

        # After initialization
        manager.initialize_controllers()
        status = manager.get_controller_status()
        assert status["initialized"] is True
        assert "main_controller" in status
        assert "generation_controller" in status
        assert "gallery_controller" in status
        assert "project_controller" in status

    def test_controller_shutdown(self, qtbot):
        """Test controller shutdown."""
        signal_bus = SignalBus()
        manager = ControllerManager(signal_bus)
        manager.initialize_controllers()

        assert manager._initialized is True

        manager.shutdown_controllers()

        assert manager._initialized is False


def test_controller_integration(qtbot):
    """Test integration between controllers."""
    signal_bus = SignalBus()
    manager = ControllerManager(signal_bus)
    manager.initialize_controllers()

    main_controller = manager.get_main_controller()
    project_controller = manager.get_project_controller()
    gallery_controller = manager.get_gallery_controller()

    # Test project creation and switching integration
    project_id = project_controller.create_project("Integration Test")
    assert project_id is not None

    # Switch to the project
    project_controller.switch_to_project(project_id)

    # Verify main controller was updated
    assert main_controller.current_project_id == project_id

    # Test that gallery controller receives project change
    assert (
        gallery_controller.current_filter.get("project_id") != project_id
    )  # Filter not auto-applied


if __name__ == "__main__":
    # Run tests if executed directly
    app = QApplication([])
    pytest.main([__file__])
