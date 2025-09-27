"""
Tests for ProductService.
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from app.services.product_service import (
    ProductService,
    ProductServiceError,
    ProductNotFoundError,
    ProductValidationError,
)
from app.models import Product, Project
from app.models.database import session_scope


class TestProductService:
    """Test ProductService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProductService()

    def test_create_product_success(self, sample_project):
        """Test successful product creation."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(b"fake image data")
            file_path = temp_file.name

        try:
            product = self.service.create_product(
                project_id=sample_project.id,
                file_path=file_path,
                product_type="image",
                metadata={"test": "value"},
            )

            assert product.id is not None
            assert product.project_id == sample_project.id
            assert product.file_path == file_path
            assert product.type == "image"
            assert product.extra_metadata == {"test": "value"}
            assert product.file_size > 0
            assert product.file_hash is not None

        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_create_product_invalid_project(self):
        """Test product creation with invalid project ID."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(b"fake image data")
            file_path = temp_file.name

        try:
            with pytest.raises(ProductValidationError, match="Project not found"):
                self.service.create_product(project_id="invalid-id", file_path=file_path)
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_create_product_missing_file(self, sample_project):
        """Test product creation with missing file."""
        with pytest.raises(ProductValidationError, match="File does not exist"):
            self.service.create_product(
                project_id=sample_project.id, file_path="/nonexistent/file.png"
            )

    def test_get_product_success(self, sample_product):
        """Test successful product retrieval."""
        product = self.service.get_product(sample_product.id)
        assert product is not None
        assert product.id == sample_product.id

    def test_get_product_not_found(self):
        """Test product retrieval with invalid ID."""
        product = self.service.get_product("invalid-id")
        assert product is None

    def test_get_products_by_project(self, sample_project):
        """Test getting products by project."""
        # Create test products
        products = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file.write(f"fake image data {i}".encode())
                file_path = temp_file.name

            try:
                product = self.service.create_product(
                    project_id=sample_project.id, file_path=file_path, product_type="image"
                )
                products.append(product)
            finally:
                if os.path.exists(file_path):
                    os.unlink(file_path)

        # Test retrieval
        retrieved = self.service.get_products_by_project(sample_project.id)
        assert len(retrieved) == 3

        # Test with limit
        limited = self.service.get_products_by_project(sample_project.id, limit=2)
        assert len(limited) == 2

        # Test with type filter
        typed = self.service.get_products_by_project(sample_project.id, product_type="image")
        assert len(typed) == 3

    def test_search_products(self, sample_product):
        """Test product search functionality."""
        # Update product with searchable content
        self.service.update_product(
            sample_product.id, {"notes": "This is a beautiful landscape image"}
        )

        # Search by notes
        results = self.service.search_products("landscape")
        assert len(results) >= 1
        assert any(p.id == sample_product.id for p in results)

        # Search with no matches
        results = self.service.search_products("nonexistent")
        assert len(results) == 0

    def test_update_product_success(self, sample_product):
        """Test successful product update."""
        updates = {"notes": "Updated notes", "liked": True, "rating": 5}

        updated = self.service.update_product(sample_product.id, updates)
        assert updated is not None
        assert updated.notes == "Updated notes"
        assert updated.liked is True
        assert updated.rating == 5

    def test_update_product_not_found(self):
        """Test product update with invalid ID."""
        result = self.service.update_product("invalid-id", {"notes": "test"})
        assert result is None

    def test_update_product_invalid_field(self, sample_product):
        """Test product update with invalid field."""
        with pytest.raises(ProductValidationError, match="Invalid field"):
            self.service.update_product(sample_product.id, {"invalid_field": "value"})

    def test_delete_product_success(self, sample_product):
        """Test successful product deletion."""
        result = self.service.delete_product(sample_product.id)
        assert result is True

        # Verify product is soft deleted
        product = self.service.get_product(sample_product.id)
        assert product is None

    def test_delete_product_not_found(self):
        """Test product deletion with invalid ID."""
        result = self.service.delete_product("invalid-id")
        assert result is False

    def test_toggle_like(self, sample_product):
        """Test like toggling functionality."""
        # Initially not liked
        assert sample_product.liked is False

        # Toggle to liked
        result = self.service.toggle_like(sample_product.id)
        assert result is True

        # Toggle back to not liked
        result = self.service.toggle_like(sample_product.id)
        assert result is False

    def test_toggle_like_not_found(self):
        """Test like toggling with invalid ID."""
        result = self.service.toggle_like("invalid-id")
        assert result is None

    def test_set_rating_success(self, sample_product):
        """Test successful rating setting."""
        result = self.service.set_rating(sample_product.id, 4)
        assert result is not None
        assert result.rating == 4

    def test_set_rating_invalid_value(self, sample_product):
        """Test rating setting with invalid value."""
        with pytest.raises(ProductValidationError, match="Rating must be"):
            self.service.set_rating(sample_product.id, 0)

        with pytest.raises(ProductValidationError, match="Rating must be"):
            self.service.set_rating(sample_product.id, 6)

    def test_set_rating_not_found(self):
        """Test rating setting with invalid ID."""
        result = self.service.set_rating("invalid-id", 3)
        assert result is None

    def test_get_product_statistics(self, sample_project):
        """Test product statistics calculation."""
        # Create test products with different properties
        products_data = [
            {"type": "image", "liked": True, "rating": 5, "file_size": 1000},
            {"type": "image", "liked": False, "rating": 3, "file_size": 2000},
            {"type": "video", "liked": True, "rating": 4, "file_size": 5000},
        ]

        for data in products_data:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file.write(b"fake data")
                file_path = temp_file.name

            try:
                product = self.service.create_product(
                    project_id=sample_project.id, file_path=file_path, product_type=data["type"]
                )

                # Update with test data
                self.service.update_product(
                    product.id, {"liked": data["liked"], "rating": data["rating"]}
                )

                # Manually set file size for testing
                with session_scope() as session:
                    db_product = session.query(Product).filter(Product.id == product.id).first()
                    db_product.file_size = data["file_size"]
                    session.commit()

            finally:
                if os.path.exists(file_path):
                    os.unlink(file_path)

        # Get statistics
        stats = self.service.get_product_statistics(sample_project.id)

        assert stats["total_products"] == 3
        assert stats["by_type"]["image"] == 2
        assert stats["by_type"]["video"] == 1
        assert stats["liked_count"] == 2
        assert stats["rated_count"] == 3
        assert stats["average_rating"] == 4.0  # (5+3+4)/3
        assert stats["total_file_size"] == 8000

    def test_cleanup_missing_files(self, sample_project):
        """Test cleanup of products with missing files."""
        # Create product with temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(b"fake data")
            file_path = temp_file.name

        product = self.service.create_product(project_id=sample_project.id, file_path=file_path)

        # Delete the file
        os.unlink(file_path)

        # Run cleanup
        cleaned_count = self.service.cleanup_missing_files(sample_project.id)
        assert cleaned_count == 1

        # Verify product is soft deleted
        retrieved_product = self.service.get_product(product.id)
        assert retrieved_product is None
