"""
Tests for Order and OrderItem models.
"""

from datetime import datetime

from app.models.project import Project
from app.models.order import Order, OrderItem


class TestOrder:
    """Test Order model functionality."""

    def test_order_creation(self, session):
        """Test creating an order."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        order = Order(
            project_id=project.id,
            provider="replicate",
            model="stability-ai/sdxl",
            model_family="stable-diffusion",
            model_modality="text-to-image",
            base_parameter_set={"prompt": "a red car", "steps": 20},
        )
        session.add(order)
        session.commit()

        assert order.id is not None
        assert order.project_id == project.id
        assert order.provider == "replicate"
        assert order.model == "stability-ai/sdxl"
        assert order.status == "pending"
        assert order.base_parameter_set == {"prompt": "a red car", "steps": 20}

    def test_order_defaults(self, session):
        """Test order default values."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        order = Order(
            project_id=project.id,
            provider="replicate",
            model="test-model",
            base_parameter_set={"prompt": "test"},
        )
        session.add(order)
        session.commit()

        assert order.status == "pending"
        assert order.expanded_count == 0
        assert order.completed_count == 0
        assert order.failed_count == 0
        assert order.template_id is None

    def test_order_status_properties(self, session):
        """Test order status properties."""
        order = Order(
            provider="replicate",
            model="test-model",
            base_parameter_set={"prompt": "test"},
        )

        # Test pending
        assert not order.is_complete
        assert not order.is_processing

        # Test processing
        order.status = "processing"
        assert not order.is_complete
        assert order.is_processing

        # Test complete
        order.status = "fulfilled"
        assert order.is_complete
        assert not order.is_processing

    def test_update_status_method(self, session):
        """Test status update based on counts."""
        order = Order(
            provider="replicate",
            model="test-model",
            base_parameter_set={"prompt": "test"},
            expanded_count=3,
        )

        # All failed
        order.failed_count = 3
        order.update_status()
        assert order.status == "failed"

        # All completed
        order.failed_count = 0
        order.completed_count = 3
        order.update_status()
        assert order.status == "fulfilled"

        # Some completed
        order.completed_count = 1
        order.update_status()
        assert order.status == "processing"

        # None completed
        order.completed_count = 0
        order.update_status()
        assert order.status == "pending"

    def test_cancel_order(self, session):
        """Test canceling an order."""
        order = Order(
            provider="replicate",
            model="test-model",
            base_parameter_set={"prompt": "test"},
        )
        session.add(order)
        session.commit()

        # Add some order items
        item1 = OrderItem(order_id=order.id, sequence_number=1, status="pending")
        item2 = OrderItem(order_id=order.id, sequence_number=2, status="generating")
        item3 = OrderItem(order_id=order.id, sequence_number=3, status="complete")

        order.order_items = [item1, item2, item3]
        session.commit()

        # Cancel order
        order.cancel()

        assert order.status == "cancelled"
        assert item1.status == "cancelled"
        assert item2.status == "cancelled"
        assert item3.status == "complete"  # Already complete items unchanged

    def test_order_repr(self, session):
        """Test order string representation."""
        order = Order(
            provider="replicate",
            model="test-model",
            base_parameter_set={"prompt": "test"},
            status="pending",
        )
        session.add(order)
        session.commit()

        repr_str = repr(order)
        assert "replicate" in repr_str
        assert "test-model" in repr_str
        assert "pending" in repr_str


class TestOrderItem:
    """Test OrderItem model functionality."""

    def test_order_item_creation(self, session):
        """Test creating an order item."""
        project = Project(name="Test Project")
        order = Order(
            project_id=project.id,
            provider="replicate",
            model="test-model",
            base_parameter_set={"prompt": "test"},
        )
        session.add(project)
        session.add(order)
        session.commit()

        item = OrderItem(
            order_id=order.id,
            sequence_number=1,
            generation_parameter_set={"prompt": "a red car", "steps": 20},
        )
        session.add(item)
        session.commit()

        assert item.id is not None
        assert item.order_id == order.id
        assert item.sequence_number == 1
        assert item.status == "pending"
        assert item.generation_parameter_set == {"prompt": "a red car", "steps": 20}

    def test_order_item_defaults(self, session):
        """Test order item default values."""
        item = OrderItem(order_id="test-order", sequence_number=1)
        session.add(item)
        session.commit()

        assert item.status == "pending"
        assert item.retry_count == 0
        assert item.started_at is None
        assert item.completed_at is None
        assert item.error_message is None

    def test_start_generation(self, session):
        """Test starting generation."""
        item = OrderItem(order_id="test-order", sequence_number=1)
        session.add(item)
        session.commit()

        item.start_generation()

        assert item.status == "generating"
        assert item.started_at is not None
        assert isinstance(item.started_at, datetime)

    def test_complete_generation(self, session):
        """Test completing generation."""
        item = OrderItem(order_id="test-order", sequence_number=1)
        item.start_generation()
        session.add(item)
        session.commit()

        return_params = {"seed": 12345, "guidance_scale": 7.5}
        item.complete_generation(return_params)

        assert item.status == "complete"
        assert item.completed_at is not None
        assert item.return_parameter_set == return_params

    def test_fail_generation(self, session):
        """Test failing generation."""
        item = OrderItem(order_id="test-order", sequence_number=1)
        item.start_generation()
        session.add(item)
        session.commit()

        error_msg = "API timeout"
        item.fail_generation(error_msg)

        assert item.status == "failed"
        assert item.completed_at is not None
        assert item.error_message == error_msg

    def test_duration_property(self, session):
        """Test duration calculation."""
        item = OrderItem(order_id="test-order", sequence_number=1)

        # No duration without start/end times
        assert item.duration is None

        # Start generation
        item.start_generation()
        assert item.duration is None  # No end time yet

        # Complete generation
        import time

        time.sleep(0.01)  # Small delay
        item.complete_generation({"seed": 123})

        duration = item.duration
        assert duration is not None
        assert duration > 0

    def test_can_retry_property(self, session):
        """Test retry capability check."""
        item = OrderItem(order_id="test-order", sequence_number=1)

        # Not failed, can't retry
        assert not item.can_retry

        # Failed with low retry count
        item.status = "failed"
        item.retry_count = 1
        assert item.can_retry

        # Failed with high retry count
        item.retry_count = 3
        assert not item.can_retry

    def test_order_item_repr(self, session):
        """Test order item string representation."""
        item = OrderItem(order_id="test-order", sequence_number=1, status="pending")
        session.add(item)
        session.commit()

        repr_str = repr(item)
        assert "test-order" in repr_str
        assert "1" in repr_str
        assert "pending" in repr_str
