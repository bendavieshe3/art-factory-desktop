"""Main entry point for Art Factory application.

This module handles application startup and initialization.
"""

import sys
from pathlib import Path


def setup_python_path():
    """Set up Python path for local imports."""
    app_dir = Path(__file__).parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))


def main():
    """Main application entry point."""
    # Set up imports first
    setup_python_path()

    # Import after path setup
    from application import ArtFactoryApplication
    from views.main_window import MainWindow

    # Create application instance
    art_factory = ArtFactoryApplication()
    art_factory.create_app()

    # Create and show main window
    main_window = MainWindow()
    main_window.show()

    if art_factory.is_debug_mode():
        print("Art Factory started in debug mode")
        print(f"Python version: {sys.version}")
        print(f"App directory: {Path(__file__).parent}")

    # Start event loop
    return art_factory.run()


if __name__ == "__main__":
    sys.exit(main())