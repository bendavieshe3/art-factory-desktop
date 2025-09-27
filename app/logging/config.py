"""
Configuration system for logging and event framework.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml


@dataclass
class LoggingConfig:
    """Configuration for logging system."""

    # General settings
    enabled: bool = True
    debug_mode: bool = False

    # Log levels per module
    log_levels: Dict[str, str] = field(default_factory=lambda: {
        "app": "INFO",
        "app.factories": "INFO",
        "app.services": "INFO",
        "app.controllers": "INFO",
        "app.events": "DEBUG",
        "app.signals": "WARNING",
    })

    # File logging
    file_output: bool = True
    log_dir: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    structured_format: bool = False

    # Console logging
    console_output: bool = True
    console_level: str = "INFO"
    use_colors: bool = True

    # Event bus settings
    event_bus_enabled: bool = True
    event_history_size: int = 1000
    event_bus_workers: int = 4

    # Middleware settings
    sanitization_enabled: bool = True
    sanitize_emails: bool = False
    enrichment_enabled: bool = True
    throttling_enabled: bool = True
    throttle_interval: float = 0.1  # seconds

    # Performance tracking
    performance_tracking: bool = True
    performance_log_threshold: float = 1.0  # seconds

    @classmethod
    def from_file(cls, config_path: Path) -> "LoggingConfig":
        """Load configuration from file (JSON or YAML)."""
        if not config_path.exists():
            return cls()  # Return defaults

        with open(config_path, 'r') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        return cls(**data.get('logging', {}))

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Load configuration from environment variables."""
        config = cls()

        # Override with environment variables
        if os.environ.get("AF_DEBUG") == "1":
            config.debug_mode = True
            config.console_level = "DEBUG"

        if os.environ.get("AF_LOG_DIR"):
            config.log_dir = os.environ["AF_LOG_DIR"]

        if os.environ.get("AF_LOG_LEVEL"):
            level = os.environ["AF_LOG_LEVEL"]
            config.console_level = level
            # Update all module levels
            config.log_levels = {k: level for k in config.log_levels}

        if os.environ.get("AF_NO_COLORS") == "1":
            config.use_colors = False

        if os.environ.get("AF_STRUCTURED_LOGS") == "1":
            config.structured_format = True

        return config

    def to_file(self, config_path: Path) -> None:
        """Save configuration to file."""
        data = {"logging": asdict(self)}

        with open(config_path, 'w') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)


@dataclass
class EventConfig:
    """Configuration for event system."""

    # Subscriber configuration
    subscribers: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "logger": {
            "enabled": True,
            "priority": 100,
        },
        "ui_bridge": {
            "enabled": False,  # Will be enabled by TASK-115
            "priority": 50,
        },
        "metrics": {
            "enabled": False,  # Future enhancement
            "priority": 75,
        },
        "history": {
            "enabled": False,  # Future enhancement
            "priority": 60,
        },
    })

    # Event filtering
    event_filters: Dict[str, List[str]] = field(default_factory=lambda: {
        "exclude_types": [],
        "include_sources": [],
        "exclude_sources": [],
    })


def setup_logging(
    config: Optional[LoggingConfig] = None,
    config_file: Optional[Path] = None
) -> LoggingConfig:
    """
    Set up the logging system with the given configuration.

    Args:
        config: LoggingConfig object (if None, loads from env/file)
        config_file: Path to configuration file

    Returns:
        LoggingConfig object used
    """
    # Load configuration
    if config is None:
        if config_file and config_file.exists():
            config = LoggingConfig.from_file(config_file)
        else:
            config = LoggingConfig.from_env()

    # Apply debug mode
    if config.debug_mode:
        # Enable debug logging for all modules
        for module in config.log_levels:
            config.log_levels[module] = "DEBUG"

    # Set up Python logging
    for module, level in config.log_levels.items():
        logger = logging.getLogger(module)
        logger.setLevel(getattr(logging, level))

    # Set up event bus and logging subscriber
    if config.event_bus_enabled:
        from ..events import event_bus
        from ..events.middleware import (
            SanitizationMiddleware,
            EnrichmentMiddleware,
            ThrottlingMiddleware
        )
        from ..events.subscribers import LoggingSubscriber

        # Add middleware
        if config.sanitization_enabled:
            event_bus.add_middleware(
                SanitizationMiddleware(sanitize_emails=config.sanitize_emails)
            )

        if config.enrichment_enabled:
            event_bus.add_middleware(EnrichmentMiddleware())

        if config.throttling_enabled:
            event_bus.add_middleware(
                ThrottlingMiddleware(throttle_interval=config.throttle_interval)
            )

        # Set up logging subscriber
        log_dir = Path(config.log_dir) if config.log_dir else None
        logging_subscriber = LoggingSubscriber(
            log_dir=log_dir,
            console_output=config.console_output,
            file_output=config.file_output,
            structured_format=config.structured_format,
            max_bytes=config.max_file_size,
            backup_count=config.backup_count,
            use_colors=config.use_colors
        )

        # Subscribe to event bus
        logging_subscriber.subscribe_to_event_bus(event_bus)

        # Log startup
        from ..events import Event, EventTypes
        event_bus.publish(Event(
            type=EventTypes.SYSTEM_STARTUP,
            source="logging",
            data={"config": asdict(config)}
        ))

    return config


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    if os.name == 'posix':  # macOS/Linux
        config_dir = Path.home() / ".config" / "art-factory"
    else:  # Windows
        config_dir = Path.home() / "AppData" / "Local" / "ArtFactory"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "logging.yaml"


def load_or_create_config() -> LoggingConfig:
    """Load configuration or create default."""
    config_path = get_default_config_path()

    if config_path.exists():
        return LoggingConfig.from_file(config_path)
    else:
        # Create default configuration
        config = LoggingConfig()
        config.to_file(config_path)
        return config