"""
Product model for generated content.
"""

import os
import hashlib
import json
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class Product(BaseModel):
    """
    Product model representing generated outputs.

    Products are the actual generated files (images, videos, audio)
    created from OrderItems.
    """

    __tablename__ = "products"

    # Core fields
    order_item_id = Column(String(36), ForeignKey("order_items.id", ondelete="SET NULL"))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))

    # File information
    type = Column(String(50), nullable=False)  # image, video, audio
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer)  # Size in bytes
    file_hash = Column(String(64))  # SHA256 for deduplication

    # Thumbnail paths stored as JSON text
    thumbnail_paths_json = Column(Text)

    # Media dimensions
    width = Column(Integer)  # For images/video
    height = Column(Integer)  # For images/video
    duration = Column(Float)  # For video/audio in seconds

    # File metadata
    mime_type = Column(String(100))

    # Additional metadata stored as JSON text
    metadata_json = Column(Text)

    # User interaction
    liked = Column(Boolean, default=False)
    rating = Column(Integer)  # 1-5 star rating
    notes = Column(Text)

    # Relationships
    order_item = relationship("OrderItem", back_populates="products")
    project = relationship("Project", back_populates="products")
    collections = relationship(
        "CollectionProduct", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Product(id={self.id}, type='{self.type}', file_path='{self.file_path}')>"

    def calculate_file_hash(self):
        """Calculate SHA256 hash of the file."""
        if not os.path.exists(self.file_path):
            return None

        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        self.file_hash = sha256_hash.hexdigest()
        return self.file_hash

    def update_file_info(self):
        """Update file size and hash from filesystem."""
        if os.path.exists(self.file_path):
            self.file_size = os.path.getsize(self.file_path)
            self.calculate_file_hash()

    def toggle_like(self):
        """Toggle the liked status."""
        self.liked = not self.liked

    def set_rating(self, rating: int):
        """Set product rating (1-5)."""
        if 1 <= rating <= 5:
            self.rating = rating
        else:
            raise ValueError("Rating must be between 1 and 5")

    @property
    def has_thumbnails(self):
        """Check if product has generated thumbnails."""
        return bool(self.thumbnail_paths)

    @property
    def aspect_ratio(self):
        """Calculate aspect ratio for images/videos."""
        if self.width and self.height:
            return self.width / self.height
        return None

    @property
    def is_landscape(self):
        """Check if image/video is landscape orientation."""
        if self.width and self.height:
            return self.width > self.height
        return None

    @property
    def is_portrait(self):
        """Check if image/video is portrait orientation."""
        if self.width and self.height:
            return self.height > self.width
        return None

    @property
    def is_square(self):
        """Check if image/video is square."""
        if self.width and self.height:
            return self.width == self.height
        return None

    @property
    def thumbnail_paths(self):
        """Get thumbnail paths as dict."""
        if self.thumbnail_paths_json:
            return json.loads(self.thumbnail_paths_json)
        return None

    @thumbnail_paths.setter
    def thumbnail_paths(self, value):
        """Set thumbnail paths from dict."""
        if value is not None:
            self.thumbnail_paths_json = json.dumps(value)
        else:
            self.thumbnail_paths_json = None

    @property
    def extra_metadata(self):
        """Get extra metadata as dict."""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return None

    @extra_metadata.setter
    def extra_metadata(self, value):
        """Set extra metadata from dict."""
        if value is not None:
            self.metadata_json = json.dumps(value)
        else:
            self.metadata_json = None

    def get_thumbnail_path(self, size="medium"):
        """
        Get thumbnail path for specified size.

        Args:
            size: 'small', 'medium', or 'large'

        Returns:
            Path to thumbnail or None if not available
        """
        if self.thumbnail_paths:
            return self.thumbnail_paths.get(size)
        return None
