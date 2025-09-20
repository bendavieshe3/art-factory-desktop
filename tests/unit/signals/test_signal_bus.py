"""Tests for signal bus singleton and logging."""

# Signal bus testing
import os
from io import StringIO
from contextlib import redirect_stderr

from signals import SignalBus, signal_bus


class TestSignalBus:
    """Test suite for SignalBus singleton."""

    def test_signal_bus_singleton(self):
        """Test that SignalBus follows singleton pattern."""
        bus1 = SignalBus()
        bus2 = SignalBus()

        assert bus1 is bus2
        assert bus1 is signal_bus
        assert bus2 is signal_bus

    def test_signal_bus_has_domain_signals(self):
        """Test that signal bus has domain signals."""
        assert hasattr(signal_bus, "domain")

        # Check for specific domain signals
        domain = signal_bus.domain
        if not os.environ.get("AF_DEBUG"):
            # In non-debug mode, check direct attributes
            assert hasattr(domain, "order_created")
            assert hasattr(domain, "generation_progress")
            assert hasattr(domain, "product_created")

    def test_signal_bus_has_ui_signals(self):
        """Test that signal bus has UI signals."""
        assert hasattr(signal_bus, "ui")

        # Check for specific UI signals
        ui = signal_bus.ui
        if not os.environ.get("AF_DEBUG"):
            # In non-debug mode, check direct attributes
            assert hasattr(ui, "request_generation")
            assert hasattr(ui, "view_changed")
            assert hasattr(ui, "error_occurred")

    def test_signal_bus_reset(self, qtbot):
        """Test that signal bus can be reset."""
        # Track signal reception
        received = []

        def handler(value):
            received.append(value)

        # Connect a handler
        if hasattr(signal_bus.domain, "_signals"):
            # Debug mode
            signal_bus.domain._signals.order_created.connect(handler)
        else:
            # Non-debug mode
            signal_bus.domain.order_created.connect(handler)

        # Reset the bus
        signal_bus.reset()

        # Try to emit - handler should not receive it after reset
        try:
            if hasattr(signal_bus.domain, "_signals"):
                signal_bus.domain._signals.order_created.emit("test_order")
            else:
                signal_bus.domain.order_created.emit("test_order")
        except Exception:
            pass  # May raise if truly disconnected

        # Should not have received the signal
        assert len(received) == 0

    def test_signal_emission_through_bus(self, qtbot):
        """Test that signals can be emitted through the bus."""
        received = []

        def handler(*args):
            received.append(args)

        # Get the actual signal based on debug mode
        if hasattr(signal_bus.domain, "_signals"):
            # Debug mode - access the underlying signal
            signal = signal_bus.domain._signals.order_created
        else:
            # Non-debug mode - direct access
            signal = signal_bus.domain.order_created

        signal.connect(handler)

        with qtbot.waitSignal(signal):
            signal.emit("order_via_bus")

        assert len(received) == 1
        assert received[0] == ("order_via_bus",)

    def test_cross_signal_independence(self, qtbot):
        """Test that different signals don't interfere with each other."""
        domain_received = []
        ui_received = []

        def domain_handler(*args):
            domain_received.append(args)

        def ui_handler(*args):
            ui_received.append(args)

        # Connect handlers to different signal types
        if hasattr(signal_bus.domain, "_signals"):
            # Debug mode
            domain_signal = signal_bus.domain._signals.order_created
            ui_signal = signal_bus.ui._signals.view_changed
        else:
            # Non-debug mode
            domain_signal = signal_bus.domain.order_created
            ui_signal = signal_bus.ui.view_changed

        domain_signal.connect(domain_handler)
        ui_signal.connect(ui_handler)

        # Emit both signals
        with qtbot.waitSignal(domain_signal):
            domain_signal.emit("order_test")

        with qtbot.waitSignal(ui_signal):
            ui_signal.emit("gallery")

        # Each handler should only receive its signal
        assert len(domain_received) == 1
        assert domain_received[0] == ("order_test",)

        assert len(ui_received) == 1
        assert ui_received[0] == ("gallery",)


class TestSignalLogging:
    """Test suite for signal logging in debug mode."""

    def test_debug_logging_emission(self, debug_mode, qtbot, monkeypatch):
        """Test that signal emissions are logged in debug mode."""
        # Recreate signal bus with debug mode
        from signals.signal_bus import SignalBus

        monkeypatch.setattr(SignalBus, "_instance", None)

        # Capture stderr
        stderr_capture = StringIO()

        with redirect_stderr(stderr_capture):
            bus = SignalBus()

            # Emit a signal
            bus.domain.order_created.emit("test_order_debug")

        output = stderr_capture.getvalue()

        # Check for debug initialization and emission
        assert "[SIGNAL]" in output
        assert "order_created" in output or "domain.order_created" in output

    def test_debug_logging_connection(self, debug_mode, monkeypatch):
        """Test that signal connections are logged in debug mode."""
        # Recreate signal bus with debug mode
        from signals.signal_bus import SignalBus

        monkeypatch.setattr(SignalBus, "_instance", None)

        stderr_capture = StringIO()

        def dummy_handler():
            pass

        with redirect_stderr(stderr_capture):
            bus = SignalBus()
            bus.domain.order_created.connect(dummy_handler)

        output = stderr_capture.getvalue()

        # Check for connection logging
        assert "[SIGNAL]" in output
        assert "Connected" in output or "connect" in output.lower()

    def test_no_logging_without_debug(self, qtbot, monkeypatch):
        """Test that signals don't log when not in debug mode."""
        # Ensure debug mode is off
        monkeypatch.delenv("AF_DEBUG", raising=False)

        # Recreate signal bus without debug mode
        from signals.signal_bus import SignalBus

        monkeypatch.setattr(SignalBus, "_instance", None)

        stderr_capture = StringIO()

        with redirect_stderr(stderr_capture):
            bus = SignalBus()
            bus.domain.order_created.emit("test_no_debug")

        output = stderr_capture.getvalue()

        # Should have no debug output
        assert "[SIGNAL]" not in output
