"""Tests for UI signals."""

# UI signals testing
from PyQt6.QtCore import QObject

from app.signals import UISignals


class SignalReceiver(QObject):
    """Helper class to receive and track signal emissions."""

    def __init__(self):
        super().__init__()
        self.received_signals = []

    def handle_signal(self, *args):
        """Record received signal with arguments."""
        self.received_signals.append(args)


class TestUISignals:
    """Test suite for UISignals class."""

    def test_ui_signals_creation(self):
        """Test that UISignals can be created."""
        signals = UISignals()
        assert signals is not None

    def test_request_generation_signal(self, qtbot):
        """Test request_generation signal with parameters dictionary."""
        signals = UISignals()
        receiver = SignalReceiver()

        signals.request_generation.connect(receiver.handle_signal)

        params = {"prompt": "A beautiful landscape", "steps": 20, "seed": 42}

        with qtbot.waitSignal(signals.request_generation):
            signals.request_generation.emit(params)

        assert len(receiver.received_signals) == 1
        received_params = receiver.received_signals[0][0]
        assert received_params == params
        assert received_params["prompt"] == "A beautiful landscape"

    def test_request_cancel_signal(self, qtbot):
        """Test request_cancel signal."""
        signals = UISignals()
        receiver = SignalReceiver()

        signals.request_cancel.connect(receiver.handle_signal)

        with qtbot.waitSignal(signals.request_cancel):
            signals.request_cancel.emit("item_to_cancel")

        assert receiver.received_signals[0] == ("item_to_cancel",)

    def test_view_changed_signal(self, qtbot):
        """Test view_changed signal for navigation."""
        signals = UISignals()
        receiver = SignalReceiver()

        signals.view_changed.connect(receiver.handle_signal)

        views = ["projects", "gallery", "orders", "settings"]
        for view in views:
            with qtbot.waitSignal(signals.view_changed):
                signals.view_changed.emit(view)

        assert len(receiver.received_signals) == 4
        received_views = [args[0] for args in receiver.received_signals]
        assert received_views == views

    def test_selection_changed_signal(self, qtbot):
        """Test selection_changed signal with list of IDs."""
        signals = UISignals()
        receiver = SignalReceiver()

        signals.selection_changed.connect(receiver.handle_signal)

        selected_items = ["prod_1", "prod_2", "prod_3"]

        with qtbot.waitSignal(signals.selection_changed):
            signals.selection_changed.emit(selected_items)

        assert len(receiver.received_signals) == 1
        assert receiver.received_signals[0][0] == selected_items

    def test_filter_applied_signal(self, qtbot):
        """Test filter_applied signal with filter parameters."""
        signals = UISignals()
        receiver = SignalReceiver()

        signals.filter_applied.connect(receiver.handle_signal)

        filters = {
            "type": "image",
            "date_from": "2025-01-01",
            "liked": True,
            "project": "project_123",
        }

        with qtbot.waitSignal(signals.filter_applied):
            signals.filter_applied.emit(filters)

        received_filters = receiver.received_signals[0][0]
        assert received_filters == filters

    def test_loading_state_signals(self, qtbot):
        """Test loading_started and loading_finished signals."""
        signals = UISignals()
        started_receiver = SignalReceiver()
        finished_receiver = SignalReceiver()

        signals.loading_started.connect(started_receiver.handle_signal)
        signals.loading_finished.connect(finished_receiver.handle_signal)

        # Start loading
        with qtbot.waitSignal(signals.loading_started):
            signals.loading_started.emit("Loading products...")

        assert started_receiver.received_signals[0] == ("Loading products...",)

        # Finish loading
        with qtbot.waitSignal(signals.loading_finished):
            signals.loading_finished.emit()

        assert len(finished_receiver.received_signals) == 1

    def test_error_occurred_signal(self, qtbot):
        """Test error_occurred signal."""
        signals = UISignals()
        receiver = SignalReceiver()

        signals.error_occurred.connect(receiver.handle_signal)

        error_msg = "Failed to connect to provider API"

        with qtbot.waitSignal(signals.error_occurred):
            signals.error_occurred.emit(error_msg)

        assert receiver.received_signals[0] == (error_msg,)

    def test_page_changed_signal(self, qtbot):
        """Test page_changed signal for pagination."""
        signals = UISignals()
        receiver = SignalReceiver()

        signals.page_changed.connect(receiver.handle_signal)

        for page in range(1, 4):
            with qtbot.waitSignal(signals.page_changed):
                signals.page_changed.emit(page)

        assert len(receiver.received_signals) == 3
        assert receiver.received_signals[-1] == (3,)

    def test_search_requested_signal(self, qtbot):
        """Test search_requested signal."""
        signals = UISignals()
        receiver = SignalReceiver()

        signals.search_requested.connect(receiver.handle_signal)

        search_query = "sunset landscape"

        with qtbot.waitSignal(signals.search_requested):
            signals.search_requested.emit(search_query)

        assert receiver.received_signals[0] == (search_query,)

    def test_disconnecting_signals(self, qtbot):
        """Test that signals can be disconnected."""
        signals = UISignals()
        receiver = SignalReceiver()

        # Connect and verify it works
        signals.error_occurred.connect(receiver.handle_signal)
        with qtbot.waitSignal(signals.error_occurred):
            signals.error_occurred.emit("Error 1")

        assert len(receiver.received_signals) == 1

        # Disconnect and verify no more signals received
        signals.error_occurred.disconnect(receiver.handle_signal)
        signals.error_occurred.emit("Error 2")

        # Should still be just 1 signal
        assert len(receiver.received_signals) == 1
