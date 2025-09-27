"""
Generation Queue model for persisting generation queue state.
"""

import json
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class GenerationQueue(BaseModel):
    """
    Generation Queue model for managing persisted generation queue.

    This model tracks OrderItems that are queued, in-progress, or completed
    for generation processing. It provides persistence across app restarts.
    """

    __tablename__ = "generation_queue"

    # Core fields
    order_item_id = Column(
        String(36), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    # Queue state
    status = Column(
        String(50), nullable=False, default="queued"
    )  # queued, processing, completed, failed, cancelled
    priority = Column(Integer, default=0)  # Higher number = higher priority

    # Generation details
    provider = Column(String(100), nullable=False)  # From OrderItem
    model = Column(String(200), nullable=False)  # From OrderItem

    # Progress tracking
    progress_percent = Column(Float, default=0.0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Worker tracking
    worker_id = Column(String(100))  # ID of worker processing this item

    # Provider concurrency grouping
    concurrency_group = Column(String(200))  # Used for per-provider limits

    # Metadata stored as JSON text
    metadata_json = Column(Text)

    # Relationships
    order_item = relationship("OrderItem", back_populates="generation_queue")
    order = relationship("Order")

    def __repr__(self):
        return (
            f"<GenerationQueue(id={self.id}, order_item_id='{self.order_item_id}', "
            f"status='{self.status}', provider='{self.provider}')>"
        )

    @property
    def metadata(self):
        """Get metadata as dict."""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}

    @metadata.setter
    def metadata(self, value):
        """Set metadata from dict."""
        if value is not None:
            self.metadata_json = json.dumps(value)
        else:
            self.metadata_json = None

    def mark_processing(self, worker_id: str = None):
        """Mark the queue item as processing."""
        self.status = "processing"
        self.started_at = datetime.utcnow()
        self.worker_id = worker_id

    def mark_completed(self):
        """Mark the queue item as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100.0
        self.worker_id = None

    def mark_failed(self, error_message: str):
        """Mark the queue item as failed."""
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.worker_id = None

    def mark_cancelled(self):
        """Mark the queue item as cancelled."""
        self.status = "cancelled"
        self.completed_at = datetime.utcnow()
        self.worker_id = None

    def can_retry(self):
        """Check if the item can be retried."""
        return self.status == "failed" and self.retry_count < self.max_retries

    def increment_retry(self):
        """Increment retry count and reset for retry."""
        if self.can_retry():
            self.retry_count += 1
            self.status = "queued"
            self.error_message = None
            self.started_at = None
            self.completed_at = None
            self.worker_id = None
            return True
        return False

    def update_progress(self, progress_percent: float):
        """Update generation progress."""
        self.progress_percent = min(max(progress_percent, 0.0), 100.0)

    def get_duration(self):
        """Get generation duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None

    @property
    def is_active(self):
        """Check if the item is actively being processed."""
        return self.status in ["queued", "processing"]

    @property
    def is_finished(self):
        """Check if the item is finished (completed, failed, or cancelled)."""
        return self.status in ["completed", "failed", "cancelled"]

    def set_concurrency_group(self):
        """Set the concurrency group based on provider."""
        # Group by provider for concurrency limits
        self.concurrency_group = self.provider

    @classmethod
    def get_status_priority(cls, status: str) -> int:
        """Get sorting priority for status (lower = higher priority)."""
        priority_map = {"processing": 0, "queued": 1, "failed": 2, "cancelled": 3, "completed": 4}
        return priority_map.get(status, 5)
