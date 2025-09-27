"""
Controller manager for initializing and coordinating all application controllers.
"""

import logging
from typing import Dict, Any

from signals.signal_bus import SignalBus
from .main_controller import MainController
from .generation_controller import GenerationController
from .gallery_controller import GalleryController
from .project_controller import ProjectController


class ControllerManager:
    """Manager for initializing and coordinating all application controllers.

    This class provides a centralized way to initialize all controllers,
    ensure proper signal connections, and manage controller lifecycle.
    """

    def __init__(self, signal_bus: SignalBus):
        """Initialize the controller manager.

        Args:
            signal_bus: The application signal bus
        """
        self.signal_bus = signal_bus
        self.logger = logging.getLogger(__name__)

        # Controllers
        self.main_controller: MainController = None
        self.generation_controller: GenerationController = None
        self.gallery_controller: GalleryController = None
        self.project_controller: ProjectController = None

        self._initialized = False

    def initialize_controllers(self) -> bool:
        """Initialize all application controllers.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing application controllers")

            # Create main controller first (singleton)
            self.main_controller = MainController(self.signal_bus)

            # Create other controllers
            self.generation_controller = GenerationController(self.signal_bus)
            self.gallery_controller = GalleryController(self.signal_bus)
            self.project_controller = ProjectController(self.signal_bus)

            # Register controllers with main controller
            self.main_controller.register_controller(
                "generation", self.generation_controller
            )
            self.main_controller.register_controller("gallery", self.gallery_controller)
            self.main_controller.register_controller("project", self.project_controller)

            # Set up controller relationships
            self._setup_controller_relationships()

            # Initialize the main controller (which initializes others)
            self.main_controller.initialize_application()

            self._initialized = True
            self.logger.info("All controllers initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize controllers: {e}")
            return False

    def _setup_controller_relationships(self):
        """Set up relationships between controllers."""
        # Set parent relationships for cross-controller communication
        self.generation_controller.setParent(self.main_controller)
        self.gallery_controller.setParent(self.main_controller)
        self.project_controller.setParent(self.main_controller)

        # Connect additional cross-controller signals if needed
        # This allows controllers to communicate through the signal bus
        self._connect_cross_controller_signals()

    def _connect_cross_controller_signals(self):
        """Connect signals that span multiple controllers."""
        # Example: When a project changes, notify gallery to reload
        self.signal_bus.domain.project_changed.connect(
            self.gallery_controller._on_project_changed
        )

        # When products are created, update project statistics
        self.signal_bus.domain.product_created.connect(
            self._on_product_created_for_stats
        )

    def _on_product_created_for_stats(self, product_id: str):
        """Handle product creation for statistics updates.

        Args:
            product_id: ID of the created product
        """
        # This is an example of cross-controller coordination
        # In a real implementation, this might update project statistics
        self.logger.debug(f"Product created for stats update: {product_id}")

    def get_controller(self, name: str):
        """Get a controller by name.

        Args:
            name: Name of the controller to retrieve

        Returns:
            The controller instance, or None if not found
        """
        if not self._initialized:
            return None

        return self.main_controller.get_controller(name)

    def get_main_controller(self) -> MainController:
        """Get the main controller.

        Returns:
            The main controller instance
        """
        return self.main_controller

    def get_generation_controller(self) -> GenerationController:
        """Get the generation controller.

        Returns:
            The generation controller instance
        """
        return self.generation_controller

    def get_gallery_controller(self) -> GalleryController:
        """Get the gallery controller.

        Returns:
            The gallery controller instance
        """
        return self.gallery_controller

    def get_project_controller(self) -> ProjectController:
        """Get the project controller.

        Returns:
            The project controller instance
        """
        return self.project_controller

    def shutdown_controllers(self):
        """Shutdown all controllers and clean up resources."""
        if not self._initialized:
            return

        self.logger.info("Shutting down application controllers")

        try:
            # Shutdown main controller (which handles others)
            if self.main_controller:
                self.main_controller.shutdown()

            self._initialized = False
            self.logger.info("All controllers shut down successfully")

        except Exception as e:
            self.logger.error(f"Error during controller shutdown: {e}")

    def get_controller_status(self) -> Dict[str, Any]:
        """Get status information about all controllers.

        Returns:
            Dictionary with controller status information
        """
        if not self._initialized:
            return {"initialized": False}

        status = {
            "initialized": True,
            "main_controller": {
                "current_project": getattr(
                    self.main_controller, "current_project_id", None
                ),
                "registered_controllers": len(self.main_controller.controllers),
            },
        }

        # Add generation controller status
        if self.generation_controller:
            status["generation_controller"] = (
                self.generation_controller.get_generation_queue_status()
            )

        # Add gallery controller status
        if self.gallery_controller:
            status["gallery_controller"] = self.gallery_controller.get_gallery_stats()

        # Add project controller status
        if self.project_controller:
            status["project_controller"] = {
                "total_projects": len(self.project_controller.get_all_projects()),
                "active_projects": len(self.project_controller.get_active_projects()),
                "current_project": (
                    self.project_controller.current_project["id"]
                    if self.project_controller.current_project
                    else None
                ),
            }

        return status

    def handle_application_error(self, error_message: str, context: str = ""):
        """Handle application-wide errors.

        Args:
            error_message: The error message
            context: Optional context about where the error occurred
        """
        full_message = f"{context}: {error_message}" if context else error_message
        self.logger.error(f"Application error: {full_message}")

        # Emit error signal through main controller
        if self.main_controller:
            self.main_controller.handle_error(error_message, context)
