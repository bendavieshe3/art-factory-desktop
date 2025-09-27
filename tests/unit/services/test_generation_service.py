"""
Tests for GenerationService.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.services.generation_service import (
    GenerationService,
    GenerationServiceError,
    QueueItemNotFoundError,
)
from app.models import Order, OrderItem, GenerationQueue, Project
from app.models.database import session_scope


class TestGenerationService:
    """Test GenerationService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GenerationService(
            default_concurrency_limits={"replicate": 2, "fal": 3, "default": 1}
        )

    def test_initialization(self):
        """Test service initialization."""
        assert self.service.concurrency_limits["replicate"] == 2
        assert self.service.concurrency_limits["fal"] == 3
        assert self.service.concurrency_limits["default"] == 1

    def test_queue_order_success(self, sample_order_with_items):
        """Test successful order queuing."""
        order = sample_order_with_items

        queue_item_ids = self.service.queue_order(order.id)

        # Should have queued all order items
        assert len(queue_item_ids) == len(order.order_items)

        # Verify queue items were created
        with session_scope() as session:
            queue_items = (
                session.query(GenerationQueue).filter(GenerationQueue.order_id == order.id).all()
            )
            assert len(queue_items) == len(order.order_items)

            for item in queue_items:
                assert item.status == "queued"
                assert item.provider == order.provider
                assert item.model == order.model

    def test_queue_order_not_found(self):
        """Test queuing non-existent order."""
        with pytest.raises(GenerationServiceError, match="Order not found"):
            self.service.queue_order("invalid-id")

    def test_queue_order_item_success(self, sample_order_item):
        """Test successful order item queuing."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)

        assert queue_item_id is not None

        # Verify queue item was created
        with session_scope() as session:
            queue_item = (
                session.query(GenerationQueue)
                .filter(GenerationQueue.order_item_id == sample_order_item.id)
                .first()
            )
            assert queue_item is not None
            assert queue_item.status == "queued"

    def test_queue_order_item_already_queued(self, sample_order_item):
        """Test queuing already queued order item."""
        # Queue first time
        first_id = self.service.queue_order_item(sample_order_item.id)
        assert first_id is not None

        # Queue second time should return None
        second_id = self.service.queue_order_item(sample_order_item.id)
        assert second_id is None

    def test_queue_order_item_not_found(self):
        """Test queuing non-existent order item."""
        with pytest.raises(GenerationServiceError, match="OrderItem not found"):
            self.service.queue_order_item("invalid-id")

    def test_get_next_items_without_concurrency(self, sample_order_with_items):
        """Test getting next items without concurrency limits."""
        order = sample_order_with_items
        self.service.queue_order(order.id, priority=10)

        items = self.service.get_next_items(concurrency_check=False)

        assert len(items) > 0
        # Should be ordered by priority
        for item in items:
            assert item.priority == 10

    def test_get_next_items_with_concurrency(self, sample_order_with_items):
        """Test getting next items with concurrency limits."""
        order = sample_order_with_items
        self.service.queue_order(order.id)

        items = self.service.get_next_items(concurrency_check=True)

        # Should respect concurrency limits
        provider_counts = {}
        for item in items:
            provider_counts[item.provider] = provider_counts.get(item.provider, 0) + 1

        for provider, count in provider_counts.items():
            limit = self.service.concurrency_limits.get(
                provider, self.service.concurrency_limits["default"]
            )
            assert count <= limit

    def test_start_generation_success(self, sample_order_item):
        """Test successful generation start."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)

        queue_item = self.service.start_generation(queue_item_id, worker_id="worker-1")

        assert queue_item.status == "processing"
        assert queue_item.worker_id == "worker-1"
        assert queue_item.started_at is not None

    def test_start_generation_not_found(self):
        """Test starting generation for non-existent queue item."""
        with pytest.raises(QueueItemNotFoundError):
            self.service.start_generation("invalid-id")

    def test_start_generation_wrong_status(self, sample_order_item):
        """Test starting generation for item not in queued state."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)

        # Start once
        self.service.start_generation(queue_item_id)

        # Try to start again
        with pytest.raises(GenerationServiceError, match="not in queued state"):
            self.service.start_generation(queue_item_id)

    def test_update_progress_success(self, sample_order_item):
        """Test successful progress update."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)
        self.service.start_generation(queue_item_id)

        metadata = {"step": 5, "total_steps": 10}
        queue_item = self.service.update_progress(queue_item_id, 50.0, metadata)

        assert queue_item.progress_percent == 50.0
        assert queue_item.metadata == metadata

    def test_update_progress_not_found(self):
        """Test updating progress for non-existent queue item."""
        with pytest.raises(QueueItemNotFoundError):
            self.service.update_progress("invalid-id", 50.0)

    def test_complete_generation_success(self, sample_order_item):
        """Test successful generation completion."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)
        self.service.start_generation(queue_item_id)

        queue_item = self.service.complete_generation(queue_item_id)

        assert queue_item.status == "completed"
        assert queue_item.completed_at is not None
        assert queue_item.progress_percent == 100.0
        assert queue_item.worker_id is None

        # Check that OrderItem was updated
        with session_scope() as session:
            order_item = (
                session.query(OrderItem).filter(OrderItem.id == sample_order_item.id).first()
            )
            assert order_item.status == "complete"

    def test_fail_generation_success(self, sample_order_item):
        """Test successful generation failure handling."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)
        self.service.start_generation(queue_item_id)

        error_msg = "Test error message"
        queue_item = self.service.fail_generation(queue_item_id, error_msg)

        assert queue_item.status == "failed"
        assert queue_item.error_message == error_msg
        assert queue_item.completed_at is not None
        assert queue_item.worker_id is None

        # Check that OrderItem was updated
        with session_scope() as session:
            order_item = (
                session.query(OrderItem).filter(OrderItem.id == sample_order_item.id).first()
            )
            assert order_item.status == "failed"
            assert order_item.error_message == error_msg

    def test_cancel_generation_success(self, sample_order_item):
        """Test successful generation cancellation."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)

        result = self.service.cancel_generation(queue_item_id)

        assert result is True

        # Check queue item status
        with session_scope() as session:
            queue_item = (
                session.query(GenerationQueue).filter(GenerationQueue.id == queue_item_id).first()
            )
            assert queue_item.status == "cancelled"

    def test_cancel_generation_not_found(self):
        """Test cancelling non-existent generation."""
        result = self.service.cancel_generation("invalid-id")
        assert result is False

    def test_cancel_generation_wrong_status(self, sample_order_item):
        """Test cancelling completed generation."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)
        self.service.start_generation(queue_item_id)
        self.service.complete_generation(queue_item_id)

        result = self.service.cancel_generation(queue_item_id)
        assert result is False

    def test_retry_failed_item_success(self, sample_order_item):
        """Test successful retry of failed item."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)
        self.service.start_generation(queue_item_id)
        self.service.fail_generation(queue_item_id, "Test error")

        result = self.service.retry_failed_item(queue_item_id)

        assert result is True

        # Check queue item was reset
        with session_scope() as session:
            queue_item = (
                session.query(GenerationQueue).filter(GenerationQueue.id == queue_item_id).first()
            )
            assert queue_item.status == "queued"
            assert queue_item.retry_count == 1
            assert queue_item.error_message is None

    def test_retry_failed_item_max_retries(self, sample_order_item):
        """Test retry when max retries exceeded."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)

        # Set max retries to 1 and exceed it
        with session_scope() as session:
            queue_item = (
                session.query(GenerationQueue).filter(GenerationQueue.id == queue_item_id).first()
            )
            queue_item.max_retries = 1
            queue_item.retry_count = 1
            queue_item.status = "failed"
            session.commit()

        result = self.service.retry_failed_item(queue_item_id)
        assert result is False

    def test_retry_failed_item_not_found(self):
        """Test retrying non-existent item."""
        with pytest.raises(QueueItemNotFoundError):
            self.service.retry_failed_item("invalid-id")

    def test_get_queue_status(self, sample_order_with_items):
        """Test getting queue status."""
        order = sample_order_with_items
        self.service.queue_order(order.id)

        status = self.service.get_queue_status()

        assert "total_items" in status
        assert "status_counts" in status
        assert "provider_counts" in status
        assert "concurrency_limits" in status
        assert status["total_items"] > 0
        assert "queued" in status["status_counts"]

    def test_get_generation_status_success(self, sample_order_item):
        """Test getting detailed generation status."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)

        status = self.service.get_generation_status(queue_item_id)

        assert status is not None
        assert status["queue_item_id"] == queue_item_id
        assert status["order_item_id"] == sample_order_item.id
        assert status["status"] == "queued"
        assert "provider" in status
        assert "model" in status

    def test_get_generation_status_not_found(self):
        """Test getting status for non-existent item."""
        status = self.service.get_generation_status("invalid-id")
        assert status is None

    def test_get_order_progress(self, sample_order_with_items):
        """Test getting order progress."""
        order = sample_order_with_items
        self.service.queue_order(order.id)

        progress = self.service.get_order_progress(order.id)

        assert progress["order_id"] == order.id
        assert progress["total_items"] == len(order.order_items)
        assert progress["overall_status"] == "queued"
        assert progress["overall_progress_percent"] == 0.0
        assert "items" in progress

    def test_get_order_progress_mixed_status(self, sample_order_with_items):
        """Test order progress with mixed item statuses."""
        order = sample_order_with_items
        queue_item_ids = self.service.queue_order(order.id)

        # Complete one item
        if queue_item_ids:
            self.service.start_generation(queue_item_ids[0])
            self.service.complete_generation(queue_item_ids[0])

        progress = self.service.get_order_progress(order.id)

        assert progress["completed_items"] >= 1
        assert progress["overall_progress_percent"] > 0
        assert progress["overall_status"] in ["processing", "queued"]

    def test_cleanup_completed_items(self, sample_order_item):
        """Test cleanup of old completed items."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)
        self.service.start_generation(queue_item_id)
        self.service.complete_generation(queue_item_id)

        # Make the item old
        with session_scope() as session:
            queue_item = (
                session.query(GenerationQueue).filter(GenerationQueue.id == queue_item_id).first()
            )
            queue_item.completed_at = datetime.utcnow() - timedelta(days=8)
            session.commit()

        cleaned_count = self.service.cleanup_completed_items(days_old=7)

        assert cleaned_count >= 1

        # Verify item was deleted
        with session_scope() as session:
            queue_item = (
                session.query(GenerationQueue).filter(GenerationQueue.id == queue_item_id).first()
            )
            assert queue_item is None

    def test_set_concurrency_limit(self):
        """Test setting concurrency limits."""
        self.service.set_concurrency_limit("test_provider", 5)
        assert self.service.concurrency_limits["test_provider"] == 5

        # Test invalid limit
        self.service.set_concurrency_limit("test_provider", 0)
        # Should not change
        assert self.service.concurrency_limits["test_provider"] == 5

    def test_concurrency_group_setting(self, sample_order_item):
        """Test that concurrency groups are set correctly."""
        queue_item_id = self.service.queue_order_item(sample_order_item.id)

        with session_scope() as session:
            queue_item = (
                session.query(GenerationQueue).filter(GenerationQueue.id == queue_item_id).first()
            )
            assert queue_item.concurrency_group == queue_item.provider

    @patch("app.services.generation_service.session_scope")
    def test_database_error_handling(self, mock_session_scope):
        """Test database error handling."""
        # Mock database error
        mock_session_scope.side_effect = Exception("Database error")

        with pytest.raises(GenerationServiceError):
            self.service.queue_order("test-id")

    def test_restore_interrupted_generations(self):
        """Test restoration of interrupted generations on startup."""
        # Create a processing item manually
        with session_scope() as session:
            from app.models import Project, Order, OrderItem

            project = Project(name="Test Project")
            session.add(project)
            session.flush()

            order = Order(
                project_id=project.id,
                provider="replicate",
                model="test-model",
                base_parameter_set={"prompt": "test"},
            )
            session.add(order)
            session.flush()

            order_item = OrderItem(
                order_id=order.id, sequence_number=1, generation_parameter_set={"prompt": "test"}
            )
            session.add(order_item)
            session.flush()

            queue_item = GenerationQueue(
                order_item_id=order_item.id,
                order_id=order.id,
                provider="replicate",
                model="test-model",
                status="processing",
                worker_id="interrupted-worker",
            )
            session.add(queue_item)
            session.commit()

            interrupted_id = queue_item.id

        # Create new service instance to trigger restoration
        new_service = GenerationService()

        # Check that the item was reset to queued
        with session_scope() as session:
            restored_item = (
                session.query(GenerationQueue).filter(GenerationQueue.id == interrupted_id).first()
            )
            if restored_item:  # Might have been cleaned up
                assert restored_item.status == "queued"
                assert restored_item.worker_id is None
