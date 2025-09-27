"""
Application class that integrates controllers with the main window.
"""

import logging
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

from signals import signal_bus
from controllers.controller_manager import ControllerManager
from views.main_window import MainWindow
from logging.config import setup_logging
from events import event_bus, Event, EventTypes


class ArtFactoryApplication:
    """Main application class that coordinates controllers and UI.

    This class initializes the controller layer and connects it with
    the main window UI, providing a clean separation between business
    logic and presentation.
    """

    def __init__(self):
        """Initialize the Art Factory application."""
        self.logger = logging.getLogger(__name__)

        # Core components
        self.qt_app: QApplication = None
        self.main_window: MainWindow = None
        self.controller_manager: ControllerManager = None

        # Application state
        self.is_initialized = False

    def initialize(self, argv: list = None) -> bool:
        """Initialize the application.

        Args:
            argv: Command line arguments

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing Art Factory application")

            # Create Qt application
            self.qt_app = QApplication(argv or sys.argv)
            self.qt_app.setApplicationName("Art Factory")
            self.qt_app.setApplicationVersion("1.0.0")
            self.qt_app.setOrganizationName("Art Factory")
            self.qt_app.setOrganizationDomain("artfactory.local")

            # Initialize event system
            self._setup_event_system()

            # Initialize controller manager
            self.controller_manager = ControllerManager(signal_bus)
            if not self.controller_manager.initialize_controllers():
                self.logger.error("Failed to initialize controllers")
                return False

            # Create main window
            self.main_window = MainWindow()

            # Connect controllers to main window
            self._connect_controllers_to_ui()

            # Load initial data
            self._load_initial_data()

            self.is_initialized = True
            self.logger.info("Art Factory application initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    def _setup_event_system(self):
        """Set up the event system with logging and configuration."""
        try:
            self.logger.info("Setting up event system")

            # Set up logging configuration with event bus integration
            # Check for debug mode from command line
            debug_mode = "--debug" in sys.argv
            config = setup_logging()

            self.logger.info("Event system initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to set up event system: {e}")
            # Don't fail application startup if event system fails
            # Fall back to basic logging

    def _connect_controllers_to_ui(self):
        """Connect controllers to UI components."""
        try:
            # Get controllers
            main_controller = self.controller_manager.get_main_controller()
            generation_controller = self.controller_manager.get_generation_controller()
            gallery_controller = self.controller_manager.get_gallery_controller()
            project_controller = self.controller_manager.get_project_controller()

            # Connect parameter panel to generation controller
            if hasattr(self.main_window, 'parameter_panel'):
                self.main_window.parameter_panel.generation_requested.connect(
                    generation_controller._on_generation_requested
                )

            # Connect gallery widget to gallery controller
            if hasattr(self.main_window, 'gallery_widget'):
                # Gallery widget signals to controller
                self.main_window.gallery_widget.selection_changed.connect(
                    gallery_controller._on_selection_changed
                )
                self.main_window.gallery_widget.files_dropped.connect(
                    gallery_controller._on_files_imported
                )
                self.main_window.gallery_widget.products_deleted.connect(
                    self._on_gallery_delete_requested
                )

                # Gallery controller provides data to widget
                self._setup_gallery_data_binding(gallery_controller)

            # Connect projects overview to project controller
            if hasattr(self.main_window, 'projects_overview'):
                self.main_window.projects_overview.project_selected.connect(
                    project_controller.switch_to_project
                )
                self.main_window.projects_overview.project_create_requested.connect(
                    self._on_project_create_requested
                )

                # Project controller provides data to widget
                self._setup_projects_data_binding(project_controller)

            # Connect main window events to main controller
            self.main_window.signal_bus = signal_bus  # Ensure signal bus is available

            self.logger.info("Controllers connected to UI successfully")

        except Exception as e:
            self.logger.error(f"Failed to connect controllers to UI: {e}")

    def _setup_gallery_data_binding(self, gallery_controller):
        """Set up data binding between gallery controller and widget.

        Args:
            gallery_controller: The gallery controller instance
        """
        # Override gallery controller's _update_gallery_display method
        # to actually update the gallery widget
        original_update = gallery_controller._update_gallery_display

        def update_gallery_display(products):
            """Update gallery widget with products."""
            try:
                self.main_window.gallery_widget.set_products(products)
                self.logger.debug(f"Updated gallery with {len(products)} products")
            except Exception as e:
                self.logger.error(f"Failed to update gallery display: {e}")

        gallery_controller._update_gallery_display = update_gallery_display

    def _setup_projects_data_binding(self, project_controller):
        """Set up data binding between project controller and widget.

        Args:
            project_controller: The project controller instance
        """
        # Override project controller's _update_projects_display method
        # to actually update the projects overview widget
        original_update = project_controller._update_projects_display

        def update_projects_display(projects):
            """Update projects overview widget with projects."""
            try:
                # TODO: Update projects overview widget when it has set_projects method
                # self.main_window.projects_overview.set_projects(projects)
                self.logger.debug(f"Would update projects overview with {len(projects)} projects")
            except Exception as e:
                self.logger.error(f"Failed to update projects display: {e}")

        project_controller._update_projects_display = update_projects_display

    def _load_initial_data(self):
        """Load initial application data."""
        try:
            # Load projects
            project_controller = self.controller_manager.get_project_controller()
            project_controller.load_projects()

            # Load last used project if available
            main_controller = self.controller_manager.get_main_controller()
            if main_controller.current_project_id:
                project_controller.switch_to_project(main_controller.current_project_id)

                # Load products for current project
                gallery_controller = self.controller_manager.get_gallery_controller()
                gallery_controller.load_products(main_controller.current_project_id)

            self.logger.info("Initial data loaded")

        except Exception as e:
            self.logger.error(f"Failed to load initial data: {e}")

    def _on_gallery_delete_requested(self, product_ids):
        """Handle product deletion requests from gallery.

        Args:
            product_ids: List of product IDs to delete
        """
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Confirm Deletion",
            f"Delete {len(product_ids)} product{'s' if len(product_ids) > 1 else ''}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Emit deletion signals through signal bus
            for product_id in product_ids:
                signal_bus.domain.product_deleted.emit(product_id)

    def _on_project_create_requested(self, project_data):
        """Handle project creation requests.

        Args:
            project_data: Dictionary with project creation data
        """
        project_controller = self.controller_manager.get_project_controller()
        project_id = project_controller.create_project(
            project_data.get("name", "New Project"),
            project_data.get("description", ""),
            project_data.get("settings")
        )

        if project_id:
            # Switch to the new project
            project_controller.switch_to_project(project_id)

    def run(self) -> int:
        """Run the application.

        Returns:
            Application exit code
        """
        if not self.is_initialized:
            self.logger.error("Application not initialized")
            return 1

        try:
            # Show main window
            self.main_window.show()

            # Set up periodic status updates
            self._setup_status_updates()

            # Run Qt event loop
            return self.qt_app.exec()

        except Exception as e:
            self.logger.error(f"Application runtime error: {e}")
            return 1

    def _setup_status_updates(self):
        """Set up periodic status updates for debugging."""
        def log_controller_status():
            """Log controller status periodically."""
            if self.controller_manager:
                status = self.controller_manager.get_controller_status()
                self.logger.debug(f"Controller status: {status}")

        # Create timer for periodic status updates (every 60 seconds)
        status_timer = QTimer()
        status_timer.timeout.connect(log_controller_status)
        status_timer.start(60000)  # 60 seconds

    def shutdown(self):
        """Shutdown the application and clean up resources."""
        try:
            self.logger.info("Shutting down Art Factory application")

            # Emit shutdown event
            event_bus.publish(Event(
                type=EventTypes.SYSTEM_SHUTDOWN,
                source="application",
                data={"clean_shutdown": True}
            ))

            # Shutdown controller manager
            if self.controller_manager:
                self.controller_manager.shutdown_controllers()

            # Close main window
            if self.main_window:
                self.main_window.close()

            # Shutdown event bus
            event_bus.shutdown()

            self.logger.info("Application shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")

    def get_controller_manager(self) -> ControllerManager:
        """Get the controller manager.

        Returns:
            The controller manager instance
        """
        return self.controller_manager

    def get_main_window(self) -> MainWindow:
        """Get the main window.

        Returns:
            The main window instance
        """
        return self.main_window