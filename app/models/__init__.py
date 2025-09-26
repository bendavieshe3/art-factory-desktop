"""
Database models for Art Factory Desktop.

SQLAlchemy models with SQLite backend.
"""

from .base import Base, BaseModel
from .project import Project
from .order import Order, OrderItem
from .product import Product
from .collection import Collection, CollectionProduct

__all__ = [
    "Base",
    "BaseModel",
    "Project",
    "Order",
    "OrderItem",
    "Product",
    "Collection",
    "CollectionProduct",
]
