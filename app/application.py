"""Application setup and configuration for Art Factory.

This module handles QApplication initialization, metadata setup,
and global configuration.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication


class ArtFactoryApplication:
    """Main application class that manages QApplication setup and
    global state."""

    def __init__(self):
        self.app = None
        self._setup_application_metadata()

    def _setup_application_metadata(self):
        """Configure application metadata."""
        QCoreApplication.setApplicationName("Art Factory")
        QCoreApplication.setApplicationVersion("0.1.0-dev")
        QCoreApplication.setOrganizationName("Art Factory Project")
        QCoreApplication.setOrganizationDomain("com.artfactory.desktop")

    def create_app(self, argv=None):
        """Create and configure QApplication instance.

        Args:
            argv: Command line arguments (defaults to sys.argv)

        Returns:
            QApplication: Configured application instance
        """
        if argv is None:
            argv = sys.argv

        self.app = QApplication(argv)

        # Enable debug mode if requested
        if "--debug" in argv:
            os.environ["AF_DEBUG"] = "1"
            print("Debug mode enabled")

        # Set application icon (using system default for now)
        # TODO: Add custom application icon in later task

        return self.app

    def is_debug_mode(self):
        """Check if application is running in debug mode."""
        return os.environ.get("AF_DEBUG", "0") == "1"

    def run(self):
        """Start the application event loop.

        Returns:
            int: Application exit code
        """
        if self.app is None:
            raise RuntimeError(
                "Application not created. Call create_app() first."
            )

        return self.app.exec()
