"""Main entry point for Art Factory application.

This module handles application startup and initialization with the controller layer.
"""

import sys
import logging
from pathlib import Path


def setup_python_path():
    """Set up Python path for local imports."""
    app_dir = Path(__file__).parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))


def setup_logging(debug: bool = False):
    """Set up application logging.

    Args:
        debug: Enable debug logging if True
    """
    level = logging.DEBUG if debug else logging.INFO
    format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout),
            # TODO: Add file handler for production
        ],
    )


def main():
    """Main application entry point."""
    # Set up imports first
    setup_python_path()

    # Check for debug flag
    debug_mode = "--debug" in sys.argv

    # Set up logging
    setup_logging(debug_mode)
    logger = logging.getLogger(__name__)

    logger.info("Starting Art Factory Desktop Application with Controllers")

    try:
        # Import after path setup
        from application_with_controllers import ArtFactoryApplication

        # Create and initialize the application
        app = ArtFactoryApplication()

        if not app.initialize(sys.argv):
            logger.error("Failed to initialize application")
            return 1

        # Run the application
        exit_code = app.run()

        # Shutdown cleanly
        app.shutdown()

        logger.info(f"Application exited with code: {exit_code}")
        return exit_code

    except Exception as e:
        logger.error(f"Fatal application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())