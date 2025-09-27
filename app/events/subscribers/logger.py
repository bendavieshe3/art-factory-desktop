"""
Logging subscriber that converts events to structured log entries.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from ..event_types import Event, EventSeverity


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from event
        if hasattr(record, "event_data"):
            log_data.update(record.event_data)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Enhanced console formatter with color support.
    """

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and os.isatty(1)  # Check if stdout is a terminal

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and structure."""
        # Build basic message
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        level = record.levelname
        logger_name = record.name

        # Add color if enabled
        if self.use_colors:
            level_color = self.COLORS.get(level, '')
            level = f"{level_color}{level:8s}{self.RESET}"

        # Base format
        message = f"[{timestamp}] {level} {logger_name:20s} - {record.getMessage()}"

        # Add event data if present
        if hasattr(record, "event_id"):
            message += f" [event:{record.event_id[:8]}]"

        if hasattr(record, "order_id") and record.order_id:
            message += f" [order:{record.order_id[:8]}]"

        if hasattr(record, "duration") and record.duration:
            message += f" [{record.duration:.3f}s]"

        # Add exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class LoggingSubscriber:
    """
    Event subscriber that converts events to log entries.

    Features:
    - Structured logging (JSON format)
    - File rotation
    - Console output with colors
    - Per-module log levels
    - Event context preservation
    """

    # Map event severity to log levels
    SEVERITY_TO_LEVEL = {
        EventSeverity.DEBUG: logging.DEBUG,
        EventSeverity.INFO: logging.INFO,
        EventSeverity.WARNING: logging.WARNING,
        EventSeverity.ERROR: logging.ERROR,
        EventSeverity.CRITICAL: logging.CRITICAL,
    }

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        console_output: bool = True,
        file_output: bool = True,
        structured_format: bool = False,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        use_colors: bool = True
    ):
        """
        Initialize logging subscriber.

        Args:
            log_dir: Directory for log files (defaults to user logs)
            console_output: Enable console output
            file_output: Enable file output
            structured_format: Use JSON format for files
            max_bytes: Maximum size per log file
            backup_count: Number of backup files to keep
            use_colors: Use colors in console output
        """
        self.console_output = console_output
        self.file_output = file_output
        self.structured_format = structured_format

        # Set up log directory
        if log_dir is None:
            # Default to user's logs directory
            if os.name == 'posix':  # macOS/Linux
                log_dir = Path.home() / "Library" / "Logs" / "ArtFactory"
            else:  # Windows
                log_dir = Path.home() / "AppData" / "Local" / "ArtFactory" / "Logs"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logger
        self.logger = logging.getLogger("art_factory.events")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # Don't propagate to root logger

        # Remove existing handlers
        self.logger.handlers.clear()

        # Set up console handler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(ConsoleFormatter(use_colors=use_colors))
            self.logger.addHandler(console_handler)

        # Set up file handlers
        if file_output:
            # Main log file (all events)
            main_log = self.log_dir / "art_factory.log"
            main_handler = logging.handlers.RotatingFileHandler(
                main_log,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            main_handler.setLevel(logging.DEBUG)

            if structured_format:
                main_handler.setFormatter(StructuredFormatter())
            else:
                main_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            self.logger.addHandler(main_handler)

            # Error log file (errors only)
            error_log = self.log_dir / "art_factory_errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s'
                )
            )
            self.logger.addHandler(error_handler)

    def handle_event(self, event: Event) -> None:
        """
        Handle an event and convert it to a log entry.

        Args:
            event: Event to log
        """
        # Get log level from event severity
        level = self.SEVERITY_TO_LEVEL.get(event.severity, logging.INFO)

        # Build log message
        message = self._format_message(event)

        # Build extra fields for structured logging
        extra = self._build_extra_fields(event)

        # Log the event
        self.logger.log(level, message, extra=extra, exc_info=self._get_exc_info(event))

    def _format_message(self, event: Event) -> str:
        """Format event as log message."""
        message = f"[{event.type}]"

        # Add source if present
        if event.source:
            message += f" ({event.source})"

        # Add main data points
        if event.data:
            # Extract key data points for message
            if "message" in event.data:
                message += f" {event.data['message']}"
            elif "progress" in event.data:
                message += f" Progress: {event.data['progress']}%"
            elif "duration" in event.data:
                message += f" Duration: {event.data['duration']:.3f}s"
            elif "operation" in event.data:
                message += f" Operation: {event.data['operation']}"

        # Add error message if present
        if event.error_message:
            message += f" ERROR: {event.error_message}"

        return message

    def _build_extra_fields(self, event: Event) -> Dict[str, Any]:
        """Build extra fields for structured logging."""
        extra = {
            "event_id": event.id,
            "event_type": event.type,
            "event_data": event.to_dict(),
        }

        # Add correlation IDs
        if event.order_id:
            extra["order_id"] = event.order_id
        if event.order_item_id:
            extra["order_item_id"] = event.order_item_id
        if event.product_id:
            extra["product_id"] = event.product_id
        if event.project_id:
            extra["project_id"] = event.project_id
        if event.session_id:
            extra["session_id"] = event.session_id
        if event.request_id:
            extra["request_id"] = event.request_id

        # Add performance data
        if event.data and "duration" in event.data:
            extra["duration"] = event.data["duration"]

        return extra

    def _get_exc_info(self, event: Event) -> Optional[bool]:
        """Get exception info if event contains error."""
        # Only include exc_info for actual exceptions
        if event.error_type and event.severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]:
            # Return True to capture current exception if in exception handler
            return True
        return None

    def subscribe_to_event_bus(self, event_bus) -> None:
        """
        Subscribe this logger to an event bus.

        Args:
            event_bus: EventBus instance to subscribe to
        """
        event_bus.subscribe(
            handler=self.handle_event,
            event_types=["*"],  # Subscribe to all events
            priority=100  # High priority to log before other handlers
        )
        self.logger.info("Logging subscriber connected to event bus")

    def get_log_files(self) -> Dict[str, Path]:
        """Get paths to current log files."""
        return {
            "main": self.log_dir / "art_factory.log",
            "errors": self.log_dir / "art_factory_errors.log",
        }

    def rotate_logs(self) -> None:
        """Force rotation of log files."""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()

    def set_log_level(self, level: str, logger_name: Optional[str] = None) -> None:
        """
        Set log level for specific logger or all loggers.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            logger_name: Optional specific logger name
        """
        level_value = getattr(logging, level.upper(), logging.INFO)

        if logger_name:
            logging.getLogger(logger_name).setLevel(level_value)
        else:
            self.logger.setLevel(level_value)