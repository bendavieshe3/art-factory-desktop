"""
Base controller class providing common functionality for all controllers.
"""

from PyQt6.QtCore import QObject
from typing import Optional
from signals.signal_bus import SignalBus


class BaseController(QObject):
    """Base class for all application controllers.

    Provides common functionality like signal bus access, error handling,
    and lifecycle management.
    """

    def __init__(self, signal_bus: SignalBus, parent: Optional[QObject] = None):
        """Initialize the base controller.

        Args:
            signal_bus: The application signal bus for communication
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self.signal_bus = signal_bus
        self._initialized = False

    def initialize(self):
        """Initialize the controller and connect signals.

        This method should be overridden by subclasses to set up
        signal connections and any required initialization.
        """
        if self._initialized:
            return

        self._connect_signals()
        self._initialized = True

    def _connect_signals(self):
        """Connect signals for this controller.

        Override in subclasses to set up signal connections.
        """
        pass

    def cleanup(self):
        """Clean up resources when the controller is destroyed.

        Override in subclasses to clean up any resources.
        """
        pass

    def handle_error(self, error_message: str, context: str = ""):
        """Handle an error by emitting the appropriate signal.

        Args:
            error_message: The error message to display
            context: Optional context about where the error occurred
        """
        full_message = f"{context}: {error_message}" if context else error_message
        self.signal_bus.ui.error_occurred.emit(full_message)

    def start_loading(self, task_name: str):
        """Start a loading operation.

        Args:
            task_name: Description of what is being loaded
        """
        self.signal_bus.ui.loading_started.emit(task_name)

    def finish_loading(self):
        """Finish a loading operation."""
        self.signal_bus.ui.loading_finished.emit()
