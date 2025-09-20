"""Tests for domain signals."""

# Domain signals testing
from PyQt6.QtCore import QObject

from signals import DomainSignals


class SignalReceiver(QObject):
    """Helper class to receive and track signal emissions."""

    def __init__(self):
        super().__init__()
        self.received_signals = []

    def handle_signal(self, *args):
        """Record received signal with arguments."""
        self.received_signals.append(args)


class TestDomainSignals:
    """Test suite for DomainSignals class."""

    def test_domain_signals_creation(self):
        """Test that DomainSignals can be created."""
        signals = DomainSignals()
        assert signals is not None

    def test_order_created_signal(self, qtbot):
        """Test order_created signal emission and reception."""
        signals = DomainSignals()
        receiver = SignalReceiver()

        signals.order_created.connect(receiver.handle_signal)

        with qtbot.waitSignal(signals.order_created):
            signals.order_created.emit("order_123")

        assert len(receiver.received_signals) == 1
        assert receiver.received_signals[0] == ("order_123",)

    def test_order_items_expanded_signal(self, qtbot):
        """Test order_items_expanded signal with multiple parameters."""
        signals = DomainSignals()
        receiver = SignalReceiver()

        signals.order_items_expanded.connect(receiver.handle_signal)

        with qtbot.waitSignal(signals.order_items_expanded):
            signals.order_items_expanded.emit("order_456", 5)

        assert len(receiver.received_signals) == 1
        assert receiver.received_signals[0] == ("order_456", 5)

    def test_generation_progress_signal(self, qtbot):
        """Test generation_progress signal with progress value."""
        signals = DomainSignals()
        receiver = SignalReceiver()

        signals.generation_progress.connect(receiver.handle_signal)

        # Test multiple progress updates
        for progress in [0, 25, 50, 75, 100]:
            with qtbot.waitSignal(signals.generation_progress):
                signals.generation_progress.emit("item_789", progress)

        assert len(receiver.received_signals) == 5
        assert receiver.received_signals[-1] == ("item_789", 100)

    def test_generation_failed_signal(self, qtbot):
        """Test generation_failed signal with error message."""
        signals = DomainSignals()
        receiver = SignalReceiver()

        signals.generation_failed.connect(receiver.handle_signal)

        error_msg = "API rate limit exceeded"
        with qtbot.waitSignal(signals.generation_failed):
            signals.generation_failed.emit("item_999", error_msg)

        assert len(receiver.received_signals) == 1
        assert receiver.received_signals[0] == ("item_999", error_msg)

    def test_product_lifecycle_signals(self, qtbot):
        """Test product creation, like, and deletion signals."""
        signals = DomainSignals()
        created_receiver = SignalReceiver()
        liked_receiver = SignalReceiver()
        deleted_receiver = SignalReceiver()

        signals.product_created.connect(created_receiver.handle_signal)
        signals.product_liked.connect(liked_receiver.handle_signal)
        signals.product_deleted.connect(deleted_receiver.handle_signal)

        # Test product creation
        with qtbot.waitSignal(signals.product_created):
            signals.product_created.emit("product_001")

        # Test product like
        with qtbot.waitSignal(signals.product_liked):
            signals.product_liked.emit("product_001")

        # Test product deletion
        with qtbot.waitSignal(signals.product_deleted):
            signals.product_deleted.emit("product_001")

        assert created_receiver.received_signals[0] == ("product_001",)
        assert liked_receiver.received_signals[0] == ("product_001",)
        assert deleted_receiver.received_signals[0] == ("product_001",)

    def test_project_signals(self, qtbot):
        """Test project-related signals."""
        signals = DomainSignals()
        receiver = SignalReceiver()

        # Connect all project signals to the same receiver
        signals.project_changed.connect(receiver.handle_signal)
        signals.project_created.connect(receiver.handle_signal)
        signals.project_deleted.connect(receiver.handle_signal)

        # Emit signals
        with qtbot.waitSignal(signals.project_created):
            signals.project_created.emit("project_new")

        with qtbot.waitSignal(signals.project_changed):
            signals.project_changed.emit("project_new")

        with qtbot.waitSignal(signals.project_deleted):
            signals.project_deleted.emit("project_old")

        assert len(receiver.received_signals) == 3
        assert ("project_new",) in receiver.received_signals
        assert ("project_old",) in receiver.received_signals

    def test_multiple_receivers(self, qtbot):
        """Test that multiple receivers can connect to the same signal."""
        signals = DomainSignals()
        receiver1 = SignalReceiver()
        receiver2 = SignalReceiver()

        signals.order_created.connect(receiver1.handle_signal)
        signals.order_created.connect(receiver2.handle_signal)

        with qtbot.waitSignal(signals.order_created):
            signals.order_created.emit("order_multi")

        assert len(receiver1.received_signals) == 1
        assert len(receiver2.received_signals) == 1
        assert receiver1.received_signals[0] == receiver2.received_signals[0]
