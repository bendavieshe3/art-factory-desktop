"""
Main controller for application coordination and cross-cutting concerns.
"""

from PyQt6.QtCore import QSettings, pyqtSlot
from typing import Optional, Dict, Any
import logging

from .base_controller import BaseController
from signals.signal_bus import SignalBus


class MainController(BaseController):
    """Main application controller handling coordination and cross-cutting concerns.

    Responsibilities:
    - Initialize and coordinate other controllers
    - Manage application-wide state (current project, preferences)
    - Handle cross-cutting concerns (error handling, loading states)
    - Coordinate application lifecycle events
    """

    _instance: Optional["MainController"] = None

    def __new__(cls, signal_bus: SignalBus):
        """Ensure MainController is a singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._main_initialized = False
        return cls._instance

    def __init__(self, signal_bus: SignalBus):
        """Initialize the main controller."""
        if self._main_initialized:
            return

        super().__init__(signal_bus)
        self.settings = QSettings("Art Factory", "Desktop")
        self.logger = logging.getLogger(__name__)

        # Application state
        self.current_project_id: Optional[str] = None
        self.application_state: Dict[str, Any] = {}

        # Child controllers
        self.controllers: Dict[str, BaseController] = {}

        self._main_initialized = True

    def _connect_signals(self):
        """Connect main controller signals."""
        # UI state signals
        self.signal_bus.ui.view_changed.connect(self._on_view_changed)
        self.signal_bus.ui.loading_started.connect(self._on_loading_started)
        self.signal_bus.ui.loading_finished.connect(self._on_loading_finished)
        self.signal_bus.ui.error_occurred.connect(self._on_error_occurred)

        # Domain events for application state
        self.signal_bus.domain.project_changed.connect(self._on_project_changed)

    def register_controller(self, name: str, controller: BaseController):
        """Register a child controller.

        Args:
            name: Unique name for the controller
            controller: The controller instance to register
        """
        self.controllers[name] = controller
        controller.initialize()
        self.logger.info(f"Registered controller: {name}")

    def get_controller(self, name: str) -> Optional[BaseController]:
        """Get a registered controller by name.

        Args:
            name: Name of the controller to retrieve

        Returns:
            The controller instance, or None if not found
        """
        return self.controllers.get(name)

    def initialize_application(self):
        """Initialize the application and all controllers."""
        self.logger.info("Initializing Art Factory application")

        # Load application settings
        self._load_application_state()

        # Initialize this controller
        self.initialize()

        # Initialize child controllers
        for name, controller in self.controllers.items():
            try:
                controller.initialize()
                self.logger.info(f"Initialized controller: {name}")
            except Exception as e:
                self.handle_error(f"Failed to initialize {name} controller: {e}")

    def _load_application_state(self):
        """Load application state from settings."""
        # Load current project
        self.current_project_id = self.settings.value("current_project", None)

        # Load other application preferences
        self.application_state = {
            "theme": self.settings.value("theme", "light"),
            "last_view": self.settings.value("last_view", "projects"),
            "window_geometry": self.settings.value("geometry"),
            "window_state": self.settings.value("windowState"),
        }

        self.logger.info(f"Loaded application state: project={self.current_project_id}")

    def _save_application_state(self):
        """Save application state to settings."""
        if self.current_project_id:
            self.settings.setValue("current_project", self.current_project_id)

        for key, value in self.application_state.items():
            if value is not None:
                self.settings.setValue(key, value)

    def set_current_project(self, project_id: Optional[str]):
        """Set the current active project.

        Args:
            project_id: ID of the project to set as current, or None for no project
        """
        if self.current_project_id != project_id:
            old_project = self.current_project_id
            self.current_project_id = project_id

            # Save to settings
            if project_id:
                self.settings.setValue("current_project", project_id)
            else:
                self.settings.remove("current_project")

            # Emit project changed signal
            if project_id:
                self.signal_bus.domain.project_changed.emit(project_id)

            self.logger.info(f"Project changed: {old_project} → {project_id}")

    def get_application_state(self, key: str, default: Any = None) -> Any:
        """Get an application state value.

        Args:
            key: State key to retrieve
            default: Default value if key not found

        Returns:
            The state value or default
        """
        return self.application_state.get(key, default)

    def set_application_state(self, key: str, value: Any):
        """Set an application state value.

        Args:
            key: State key to set
            value: Value to set
        """
        self.application_state[key] = value

    @pyqtSlot(str)
    def _on_view_changed(self, view_name: str):
        """Handle view change events."""
        self.set_application_state("last_view", view_name)
        self.logger.debug(f"View changed to: {view_name}")

    @pyqtSlot(str)
    def _on_loading_started(self, task_name: str):
        """Handle loading started events."""
        self.logger.debug(f"Loading started: {task_name}")

    @pyqtSlot()
    def _on_loading_finished(self):
        """Handle loading finished events."""
        self.logger.debug("Loading finished")

    @pyqtSlot(str)
    def _on_error_occurred(self, error_message: str):
        """Handle error events."""
        self.logger.error(f"Application error: {error_message}")

    @pyqtSlot(str)
    def _on_project_changed(self, project_id: str):
        """Handle project change events."""
        self.logger.info(f"Project changed event received: {project_id}")

    def shutdown(self):
        """Shutdown the application and clean up resources."""
        self.logger.info("Shutting down Art Factory application")

        # Save application state
        self._save_application_state()

        # Clean up child controllers
        for name, controller in self.controllers.items():
            try:
                controller.cleanup()
                self.logger.info(f"Cleaned up controller: {name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up {name} controller: {e}")

        # Clean up this controller
        self.cleanup()

    def cleanup(self):
        """Clean up main controller resources."""
        self.controllers.clear()
        self.application_state.clear()
