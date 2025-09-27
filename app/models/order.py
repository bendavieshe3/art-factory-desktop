"""
Order and OrderItem models for generation requests.
"""

import json
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from .base import BaseModel


class Order(BaseModel):
    """
    Order model representing a user's generation request.

    An order contains a base parameter set and creates one or more
    OrderItems based on parameter expansion (tokens, interpolation, etc.).
    """

    __tablename__ = "orders"

    # Core fields
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))
    provider = Column(String(100), nullable=False)  # replicate, fal, civitai
    model = Column(String(200), nullable=False)  # Model identifier
    model_family = Column(String(100))  # stable-diffusion, flux, midjourney
    model_modality = Column(String(100))  # text-to-image, image-to-image, etc.

    # Status tracking
    status = Column(
        String(50), default="pending"
    )  # pending, processing, fulfilled, failed, cancelled

    # Parameter sets stored as JSON
    base_parameter_set_json = Column(Text, nullable=False)

    # Counts
    expanded_count = Column(Integer, default=0)  # Number of items after expansion
    completed_count = Column(Integer, default=0)  # Number of completed items
    failed_count = Column(Integer, default=0)  # Number of failed items

    # Optional template reference
    template_id = Column(String(36), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def base_parameter_set(self):
        """Get base parameter set as dict."""
        if self.base_parameter_set_json:
            return json.loads(self.base_parameter_set_json)
        return None

    @base_parameter_set.setter
    def base_parameter_set(self, value):
        """Set base parameter set from dict."""
        if value is not None:
            self.base_parameter_set_json = json.dumps(value)
        else:
            self.base_parameter_set_json = None

    def __repr__(self):
        return (
            f"<Order(id={self.id}, provider='{self.provider}', "
            f"model='{self.model}', status='{self.status}')>"
        )

    @property
    def is_complete(self):
        """Check if all order items are complete."""
        return self.status == "fulfilled"

    @property
    def is_processing(self):
        """Check if order is currently processing."""
        return self.status == "processing"

    def update_status(self):
        """Update order status based on item statuses."""
        if self.failed_count == self.expanded_count:
            self.status = "failed"
        elif self.completed_count == self.expanded_count:
            self.status = "fulfilled"
        elif self.completed_count > 0 or self.failed_count > 0:
            self.status = "processing"
        else:
            self.status = "pending"

    def cancel(self):
        """Cancel the order and all its items."""
        self.status = "cancelled"
        for item in self.order_items:
            if item.status in ("pending", "generating"):
                item.status = "cancelled"


class OrderItem(BaseModel):
    """
    OrderItem model representing a single API request.

    Previously called "Generation" in early documentation.
    Each item represents one API call to a provider.
    """

    __tablename__ = "order_items"

    # Core fields
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    sequence_number = Column(Integer, nullable=False)  # Order within the batch

    # Status tracking
    status = Column(
        String(50), default="pending"
    )  # pending, generating, complete, failed, cancelled

    # Parameter sets
    generation_parameter_set_json = Column(Text)
    actual_parameter_set_json = Column(Text)
    return_parameter_set_json = Column(Text)

    # Provider tracking
    provider_request_id = Column(String(255))  # Provider's ID for tracking

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Relationships
    order = relationship("Order", back_populates="order_items")
    products = relationship("Product", back_populates="order_item", cascade="all, delete-orphan")
    generation_queue = relationship(
        "GenerationQueue", back_populates="order_item", cascade="all, delete-orphan", uselist=False
    )

    @property
    def generation_parameter_set(self):
        """Get generation parameter set as dict."""
        if self.generation_parameter_set_json:
            return json.loads(self.generation_parameter_set_json)
        return None

    @generation_parameter_set.setter
    def generation_parameter_set(self, value):
        """Set generation parameter set from dict."""
        if value is not None:
            self.generation_parameter_set_json = json.dumps(value)
        else:
            self.generation_parameter_set_json = None

    @property
    def actual_parameter_set(self):
        """Get actual parameter set as dict."""
        if self.actual_parameter_set_json:
            return json.loads(self.actual_parameter_set_json)
        return None

    @actual_parameter_set.setter
    def actual_parameter_set(self, value):
        """Set actual parameter set from dict."""
        if value is not None:
            self.actual_parameter_set_json = json.dumps(value)
        else:
            self.actual_parameter_set_json = None

    @property
    def return_parameter_set(self):
        """Get return parameter set as dict."""
        if self.return_parameter_set_json:
            return json.loads(self.return_parameter_set_json)
        return None

    @return_parameter_set.setter
    def return_parameter_set(self, value):
        """Set return parameter set from dict."""
        if value is not None:
            self.return_parameter_set_json = json.dumps(value)
        else:
            self.return_parameter_set_json = None

    def __repr__(self):
        return (
            f"<OrderItem(id={self.id}, order_id={self.order_id}, "
            f"sequence={self.sequence_number}, status='{self.status}')>"
        )

    def start_generation(self):
        """Mark generation as started."""
        self.status = "generating"
        self.started_at = datetime.utcnow()

    def complete_generation(self, return_params: dict):
        """Mark generation as complete."""
        self.status = "complete"
        self.completed_at = datetime.utcnow()
        self.return_parameter_set = return_params

    def fail_generation(self, error_message: str):
        """Mark generation as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message

    @property
    def duration(self):
        """Calculate generation duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def can_retry(self):
        """Check if item can be retried."""
        return self.status == "failed" and self.retry_count < 3
