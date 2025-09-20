"""Main entry point for Art Factory application.

This module handles application startup and initialization.
"""

import sys
from pathlib import Path

# Add app directory to Python path for imports
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from application import ArtFactoryApplication  # noqa: E402
from views.main_window import MainWindow  # noqa: E402


def main():
    """Main application entry point."""
    # Create application instance
    art_factory = ArtFactoryApplication()
    art_factory.create_app()

    # Create and show main window
    main_window = MainWindow()
    main_window.show()

    if art_factory.is_debug_mode():
        print("Art Factory started in debug mode")
        print(f"Python version: {sys.version}")
        print(f"App directory: {app_dir}")

    # Start event loop
    return art_factory.run()


if __name__ == "__main__":
    sys.exit(main())
