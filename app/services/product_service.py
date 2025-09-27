"""
Product Management Service.

Handles Product creation, querying, and management operations.
"""

import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from ..models import Product, Project
from ..models.database import session_scope


class ProductServiceError(Exception):
    """Base exception for ProductService errors."""

    pass


class ProductNotFoundError(ProductServiceError):
    """Raised when a product cannot be found."""

    pass


class ProductValidationError(ProductServiceError):
    """Raised when product validation fails."""

    pass


class ProductService:
    """
    Service for managing Product operations.

    Provides CRUD operations, querying, and file management for products.
    """

    def __init__(self):
        """Initialize the ProductService."""
        pass

    def create_product(
        self,
        project_id: str,
        file_path: str,
        product_type: str = "image",
        order_item_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Product:
        """
        Create a new product.

        Args:
            project_id: ID of the project this product belongs to
            file_path: Path to the product file
            product_type: Type of product (image, video, audio)
            order_item_id: Optional ID of the order item that created this product
            metadata: Optional metadata dictionary
            **kwargs: Additional product fields

        Returns:
            Created Product instance

        Raises:
            ProductValidationError: If validation fails
            ProductServiceError: If creation fails
        """
        try:
            with session_scope() as session:
                # Validate project exists
                project = (
                    session.query(Project)
                    .filter(and_(Project.id == project_id, Project.deleted_at.is_(None)))
                    .first()
                )
                if not project:
                    raise ProductValidationError(f"Project not found: {project_id}")

                # Validate file exists
                if not os.path.exists(file_path):
                    raise ProductValidationError(f"File does not exist: {file_path}")

                # Create product
                product = Product(
                    project_id=project_id,
                    order_item_id=order_item_id,
                    type=product_type,
                    file_path=file_path,
                    **kwargs,
                )

                # Set metadata if provided
                if metadata:
                    product.extra_metadata = metadata

                # Update file information
                product.update_file_info()

                # Add to session
                session.add(product)
                session.flush()  # Get the ID

                # Update project counts
                project.update_counts(session)

                session.commit()
                return product

        except SQLAlchemyError as e:
            raise ProductServiceError(f"Database error creating product: {str(e)}")

    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Get a product by ID.

        Args:
            product_id: ID of the product to retrieve

        Returns:
            Product instance or None if not found
        """
        try:
            with session_scope() as session:
                return (
                    session.query(Product)
                    .filter(and_(Product.id == product_id, Product.deleted_at.is_(None)))
                    .first()
                )
        except SQLAlchemyError:
            return None

    def get_products_by_project(
        self,
        project_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        product_type: Optional[str] = None,
        liked_only: bool = False,
    ) -> List[Product]:
        """
        Get products for a specific project.

        Args:
            project_id: ID of the project
            limit: Maximum number of products to return
            offset: Number of products to skip
            product_type: Filter by product type
            liked_only: Return only liked products

        Returns:
            List of Product instances
        """
        try:
            with session_scope() as session:
                query = session.query(Product).filter(
                    and_(Product.project_id == project_id, Product.deleted_at.is_(None))
                )

                # Apply filters
                if product_type:
                    query = query.filter(Product.type == product_type)

                if liked_only:
                    query = query.filter(Product.liked == True)

                # Apply ordering (most recent first)
                query = query.order_by(Product.created_at.desc())

                # Apply pagination
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)

                return query.all()

        except SQLAlchemyError:
            return []

    def search_products(
        self, query: str, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Product]:
        """
        Search products by notes or metadata.

        Args:
            query: Search query string
            project_id: Optional project ID to limit search
            limit: Maximum number of results

        Returns:
            List of matching Product instances
        """
        try:
            with session_scope() as session:
                db_query = session.query(Product).filter(Product.deleted_at.is_(None))

                # Add project filter if specified
                if project_id:
                    db_query = db_query.filter(Product.project_id == project_id)

                # Search in notes and metadata
                search_term = f"%{query}%"
                db_query = db_query.filter(
                    or_(Product.notes.like(search_term), Product.metadata_json.like(search_term))
                )

                # Order by relevance (created_at for now)
                db_query = db_query.order_by(Product.created_at.desc())

                if limit:
                    db_query = db_query.limit(limit)

                return db_query.all()

        except SQLAlchemyError:
            return []

    def update_product(self, product_id: str, updates: Dict[str, Any]) -> Optional[Product]:
        """
        Update a product.

        Args:
            product_id: ID of the product to update
            updates: Dictionary of field updates

        Returns:
            Updated Product instance or None if not found

        Raises:
            ProductValidationError: If validation fails
            ProductServiceError: If update fails
        """
        try:
            with session_scope() as session:
                product = (
                    session.query(Product)
                    .filter(and_(Product.id == product_id, Product.deleted_at.is_(None)))
                    .first()
                )

                if not product:
                    return None

                # Update fields
                for key, value in updates.items():
                    if hasattr(product, key):
                        setattr(product, key, value)
                    else:
                        raise ProductValidationError(f"Invalid field: {key}")

                session.commit()
                return product

        except SQLAlchemyError as e:
            raise ProductServiceError(f"Database error updating product: {str(e)}")

    def delete_product(self, product_id: str) -> bool:
        """
        Soft delete a product.

        Args:
            product_id: ID of the product to delete

        Returns:
            True if deleted successfully, False if not found

        Raises:
            ProductServiceError: If deletion fails
        """
        try:
            with session_scope() as session:
                product = (
                    session.query(Product)
                    .filter(and_(Product.id == product_id, Product.deleted_at.is_(None)))
                    .first()
                )

                if not product:
                    return False

                # Get project before deletion for count update
                project = product.project

                # Soft delete
                product.soft_delete()

                # Update project counts
                if project:
                    project.update_counts(session)

                session.commit()
                return True

        except SQLAlchemyError as e:
            raise ProductServiceError(f"Database error deleting product: {str(e)}")

    def toggle_like(self, product_id: str) -> Optional[bool]:
        """
        Toggle the liked status of a product.

        Args:
            product_id: ID of the product

        Returns:
            New liked status or None if product not found

        Raises:
            ProductServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                product = (
                    session.query(Product)
                    .filter(and_(Product.id == product_id, Product.deleted_at.is_(None)))
                    .first()
                )

                if not product:
                    return None

                product.toggle_like()
                session.commit()
                return product.liked

        except SQLAlchemyError as e:
            raise ProductServiceError(f"Database error toggling like: {str(e)}")

    def set_rating(self, product_id: str, rating: int) -> Optional[Product]:
        """
        Set the rating for a product.

        Args:
            product_id: ID of the product
            rating: Rating value (1-5)

        Returns:
            Updated Product instance or None if not found

        Raises:
            ProductValidationError: If rating is invalid
            ProductServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                product = (
                    session.query(Product)
                    .filter(and_(Product.id == product_id, Product.deleted_at.is_(None)))
                    .first()
                )

                if not product:
                    return None

                product.set_rating(rating)
                session.commit()
                return product

        except ValueError as e:
            raise ProductValidationError(str(e))
        except SQLAlchemyError as e:
            raise ProductServiceError(f"Database error setting rating: {str(e)}")

    def get_product_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get product statistics.

        Args:
            project_id: Optional project ID to limit statistics

        Returns:
            Dictionary with statistics
        """
        try:
            with session_scope() as session:
                query = session.query(Product).filter(Product.deleted_at.is_(None))

                if project_id:
                    query = query.filter(Product.project_id == project_id)

                products = query.all()

                stats = {
                    "total_products": len(products),
                    "by_type": {},
                    "liked_count": 0,
                    "rated_count": 0,
                    "average_rating": 0.0,
                    "total_file_size": 0,
                }

                # Calculate statistics
                total_rating = 0
                rated_products = 0

                for product in products:
                    # Count by type
                    product_type = product.type or "unknown"
                    stats["by_type"][product_type] = stats["by_type"].get(product_type, 0) + 1

                    # Liked count
                    if product.liked:
                        stats["liked_count"] += 1

                    # Rating statistics
                    if product.rating:
                        total_rating += product.rating
                        rated_products += 1

                    # File size
                    if product.file_size:
                        stats["total_file_size"] += product.file_size

                # Calculate averages
                stats["rated_count"] = rated_products
                if rated_products > 0:
                    stats["average_rating"] = total_rating / rated_products

                return stats

        except SQLAlchemyError:
            return {"error": "Failed to calculate statistics"}

    def cleanup_missing_files(self, project_id: Optional[str] = None) -> int:
        """
        Find and soft-delete products whose files no longer exist.

        Args:
            project_id: Optional project ID to limit cleanup

        Returns:
            Number of products cleaned up

        Raises:
            ProductServiceError: If cleanup fails
        """
        try:
            with session_scope() as session:
                query = session.query(Product).filter(Product.deleted_at.is_(None))

                if project_id:
                    query = query.filter(Product.project_id == project_id)

                products = query.all()
                cleaned_count = 0

                for product in products:
                    if not os.path.exists(product.file_path):
                        product.soft_delete()
                        cleaned_count += 1

                session.commit()
                return cleaned_count

        except SQLAlchemyError as e:
            raise ProductServiceError(f"Database error during cleanup: {str(e)}")
