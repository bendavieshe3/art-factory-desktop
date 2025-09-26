"""
Collection models for organizing products.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from .base import BaseModel, Base


class Collection(BaseModel):
    """
    Collection model for user-defined product groups.

    Collections allow users to organize products into curated groups
    independent of their original projects.
    """

    __tablename__ = "collections"

    # Core fields
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Cover image
    cover_product_id = Column(
        String(36), ForeignKey("products.id", ondelete="SET NULL")
    )

    # Denormalized count
    product_count = Column(Integer, default=0)

    # Visibility
    is_public = Column(Boolean, default=False)

    # Relationships
    products = relationship(
        "CollectionProduct", back_populates="collection", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Collection(id={self.id}, name='{self.name}', "
            f"product_count={self.product_count})>"
        )

    def add_product(self, product_id: str, position: int = None):
        """
        Add a product to the collection.

        Args:
            product_id: ID of the product to add
            position: Optional position in collection

        Returns:
            CollectionProduct association
        """
        if position is None:
            position = self.product_count

        association = CollectionProduct(
            collection_id=self.id, product_id=product_id, position=position
        )
        self.product_count += 1
        return association

    def remove_product(self, product_id: str):
        """Remove a product from the collection."""
        # This will be handled via the relationship
        self.product_count = max(0, self.product_count - 1)

    def reorder_products(self, product_ids: list):
        """
        Reorder products in the collection.

        Args:
            product_ids: List of product IDs in desired order
        """
        for position, product_id in enumerate(product_ids):
            for assoc in self.products:
                if assoc.product_id == product_id:
                    assoc.position = position
                    break

    def update_count(self, session):
        """Update the denormalized product count."""
        self.product_count = (
            session.query(CollectionProduct)
            .filter(CollectionProduct.collection_id == self.id)
            .count()
        )

    @property
    def is_empty(self):
        """Check if collection has no products."""
        return self.product_count == 0


class CollectionProduct(Base):
    """
    Association table between Collections and Products.

    Handles many-to-many relationship with additional fields.
    """

    __tablename__ = "collection_products"

    # Composite primary key
    collection_id = Column(
        String(36), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True
    )
    product_id = Column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )

    # Additional fields
    position = Column(Integer, default=0)  # For custom ordering
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    collection = relationship("Collection", back_populates="products")
    product = relationship("Product", back_populates="collections")

    def __repr__(self):
        return (
            f"<CollectionProduct(collection_id={self.collection_id}, "
            f"product_id={self.product_id}, position={self.position})>"
        )

    def move_to_position(self, new_position: int):
        """Move product to a new position in the collection."""
        self.position = new_position
