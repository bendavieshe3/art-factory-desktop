"""Signal bus for centralized signal management in Art Factory.

The SignalBus provides a singleton pattern for accessing all application
signals from a single location, with optional debug logging.
"""

import os
import sys
from typing import Optional
from functools import wraps
from PyQt6.QtCore import QObject, pyqtBoundSignal

from .domain_signals import DomainSignals
from .ui_signals import UISignals


def log_signal_emission(signal_name: str):
    """Decorator to log signal emissions in debug mode.

    Args:
        signal_name: Name of the signal for logging
    """

    def decorator(emit_method):
        @wraps(emit_method)
        def wrapper(*args, **kwargs):
            if os.environ.get("AF_DEBUG", "0") == "1":
                # Format arguments for logging
                arg_str = ""
                if args:
                    # Skip 'self' argument
                    signal_args = args[1:] if len(args) > 1 else []
                    if signal_args:
                        arg_str = f" with args: {signal_args}"
                print(f"[SIGNAL] {signal_name} emitted{arg_str}", file=sys.stderr)
            return emit_method(*args, **kwargs)

        return wrapper

    return decorator


class LoggedSignalWrapper:
    """Wrapper class to add logging to Qt signals."""

    def __init__(self, signal: pyqtBoundSignal, signal_name: str):
        """Initialize the logged signal wrapper.

        Args:
            signal: The Qt signal to wrap
            signal_name: Name for logging purposes
        """
        self._signal = signal
        self._signal_name = signal_name

    def connect(self, slot):
        """Connect a slot to the signal.

        Args:
            slot: The slot function to connect
        """
        if os.environ.get("AF_DEBUG", "0") == "1":
            print(
                f"[SIGNAL] Connected slot to {self._signal_name}",
                file=sys.stderr,
            )
        return self._signal.connect(slot)

    def disconnect(self, slot=None):
        """Disconnect a slot from the signal.

        Args:
            slot: The slot to disconnect, or None to disconnect all
        """
        if os.environ.get("AF_DEBUG", "0") == "1":
            print(
                f"[SIGNAL] Disconnected from {self._signal_name}",
                file=sys.stderr,
            )
        if slot is None:
            return self._signal.disconnect()
        return self._signal.disconnect(slot)

    @log_signal_emission("signal")
    def emit(self, *args):
        """Emit the signal with optional logging.

        Args:
            *args: Arguments to pass to the signal
        """
        # Update the decorator to use the actual signal name
        if os.environ.get("AF_DEBUG", "0") == "1":
            arg_str = f" with args: {args}" if args else ""
            print(f"[SIGNAL] {self._signal_name} emitted{arg_str}", file=sys.stderr)
        return self._signal.emit(*args)


class LoggedSignals:
    """Base class for signals with automatic logging."""

    def __init__(self, signals_instance: QObject, prefix: str):
        """Initialize logged signals wrapper.

        Args:
            signals_instance: The signals instance to wrap
            prefix: Prefix for signal names in logs
        """
        self._signals = signals_instance
        self._prefix = prefix
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging wrappers for all signals."""
        for attr_name in dir(self._signals):
            attr = getattr(self._signals, attr_name)
            if isinstance(attr, pyqtBoundSignal):
                signal_name = f"{self._prefix}.{attr_name}"
                wrapped_signal = LoggedSignalWrapper(attr, signal_name)
                setattr(self, attr_name, wrapped_signal)


class SignalBus:
    """Centralized signal bus for the application.

    This class provides a singleton pattern for accessing all application
    signals. It includes both domain signals (business events) and UI
    signals (user interface events).

    Attributes:
        domain: Domain signals for business events
        ui: UI signals for user interface events

    Example:
        from app.signals import signal_bus

        # Connect to a domain signal
        signal_bus.domain.order_created.connect(handle_order)

        # Emit a UI signal
        signal_bus.ui.loading_started.emit("Loading products...")
    """

    _instance: Optional["SignalBus"] = None

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the signal bus."""
        # Only initialize once
        if not hasattr(self, "_initialized"):
            self._domain_signals = DomainSignals()
            self._ui_signals = UISignals()

            # Wrap signals with logging in debug mode
            if os.environ.get("AF_DEBUG", "0") == "1":
                print(
                    "[SIGNAL] Signal bus initialized with debug logging",
                    file=sys.stderr,
                )
                self.domain = LoggedSignals(self._domain_signals, "domain")
                self.ui = LoggedSignals(self._ui_signals, "ui")
            else:
                # Direct access without logging
                self.domain = self._domain_signals
                self.ui = self._ui_signals

            self._initialized = True

    def reset(self):
        """Reset all signal connections (useful for testing)."""
        # Disconnect all signals
        for signals in [self._domain_signals, self._ui_signals]:
            for attr_name in dir(signals):
                attr = getattr(signals, attr_name)
                if isinstance(attr, pyqtBoundSignal):
                    try:
                        attr.disconnect()
                    except TypeError:
                        # No connections to disconnect
                        pass

        if os.environ.get("AF_DEBUG", "0") == "1":
            print(
                "[SIGNAL] Signal bus reset - all connections cleared", file=sys.stderr
            )


# Create the global signal bus instance
signal_bus = SignalBus()
