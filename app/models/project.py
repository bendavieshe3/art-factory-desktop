"""
Project model for organizing generated content.
"""

import json
from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.orm import relationship

from .base import BaseModel


class Project(BaseModel):
    """
    Project model for organizing work.

    A project is the primary organizational unit for grouping related
    orders, products, and collections.
    """

    __tablename__ = "projects"

    # Core fields
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")  # active, archived, completed

    # Denormalized counts for performance
    product_count = Column(Integer, default=0)
    order_count = Column(Integer, default=0)

    # JSON fields stored as TEXT in SQLite
    featured_product_ids_json = Column(Text)
    settings_json = Column(Text)

    # Relationships
    orders = relationship(
        "Order", back_populates="project", cascade="all, delete-orphan"
    )
    products = relationship(
        "Product", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"

    def archive(self):
        """Archive the project."""
        self.status = "archived"

    def complete(self):
        """Mark project as completed."""
        self.status = "completed"

    def activate(self):
        """Activate an archived or completed project."""
        self.status = "active"

    @property
    def is_active(self):
        """Check if project is active."""
        return self.status == "active"

    @property
    def featured_product_ids(self):
        """Get featured product IDs as list."""
        if self.featured_product_ids_json:
            return json.loads(self.featured_product_ids_json)
        return None

    @featured_product_ids.setter
    def featured_product_ids(self, value):
        """Set featured product IDs from list."""
        if value is not None:
            self.featured_product_ids_json = json.dumps(value)
        else:
            self.featured_product_ids_json = None

    @property
    def settings(self):
        """Get settings as dict."""
        if self.settings_json:
            return json.loads(self.settings_json)
        return None

    @settings.setter
    def settings(self, value):
        """Set settings from dict."""
        if value is not None:
            self.settings_json = json.dumps(value)
        else:
            self.settings_json = None

    def update_counts(self, session):
        """
        Update denormalized counts.

        Should be called when orders or products are added/removed.
        """
        from .order import Order
        from .product import Product

        self.order_count = (
            session.query(Order)
            .filter(Order.project_id == self.id, Order.deleted_at.is_(None))
            .count()
        )

        self.product_count = (
            session.query(Product)
            .filter(Product.project_id == self.id, Product.deleted_at.is_(None))
            .count()
        )
