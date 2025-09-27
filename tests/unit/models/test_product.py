"""
Tests for Product model.
"""

import os
import tempfile
import pytest

from app.models.project import Project
from app.models.product import Product


class TestProduct:
    """Test Product model functionality."""

    def test_product_creation(self, session):
        """Test creating a product."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        product = Product(
            project_id=project.id,
            type="image",
            file_path="/path/to/image.jpg",
            width=1024,
            height=768,
            mime_type="image/jpeg",
        )
        session.add(product)
        session.commit()

        assert product.id is not None
        assert product.project_id == project.id
        assert product.type == "image"
        assert product.file_path == "/path/to/image.jpg"
        assert product.width == 1024
        assert product.height == 768
        assert product.mime_type == "image/jpeg"

    def test_product_defaults(self, session):
        """Test product default values."""
        product = Product(type="image", file_path="/path/to/image.jpg")
        session.add(product)
        session.commit()

        assert product.liked is False
        assert product.rating is None
        assert product.notes is None
        assert product.file_size is None
        assert product.file_hash is None

    def test_toggle_like(self, session):
        """Test toggling like status."""
        product = Product(type="image", file_path="/test.jpg")
        session.add(product)
        session.commit()

        assert not product.liked

        product.toggle_like()
        assert product.liked

        product.toggle_like()
        assert not product.liked

    def test_set_rating(self, session):
        """Test setting product rating."""
        product = Product(type="image", file_path="/test.jpg")
        session.add(product)
        session.commit()

        # Valid ratings
        product.set_rating(5)
        assert product.rating == 5

        product.set_rating(1)
        assert product.rating == 1

        # Invalid ratings
        with pytest.raises(ValueError):
            product.set_rating(0)

        with pytest.raises(ValueError):
            product.set_rating(6)

    def test_aspect_ratio_properties(self, session):
        """Test aspect ratio calculations."""
        # Landscape image
        landscape = Product(type="image", file_path="/landscape.jpg", width=1920, height=1080)
        assert landscape.aspect_ratio == pytest.approx(1.777, rel=1e-3)
        assert landscape.is_landscape
        assert not landscape.is_portrait
        assert not landscape.is_square

        # Portrait image
        portrait = Product(type="image", file_path="/portrait.jpg", width=1080, height=1920)
        assert portrait.aspect_ratio == pytest.approx(0.5625, rel=1e-3)
        assert not portrait.is_landscape
        assert portrait.is_portrait
        assert not portrait.is_square

        # Square image
        square = Product(type="image", file_path="/square.jpg", width=1024, height=1024)
        assert square.aspect_ratio == 1.0
        assert not square.is_landscape
        assert not square.is_portrait
        assert square.is_square

        # No dimensions
        no_dims = Product(type="image", file_path="/test.jpg")
        assert no_dims.aspect_ratio is None
        assert no_dims.is_landscape is None
        assert no_dims.is_portrait is None
        assert no_dims.is_square is None

    def test_thumbnail_paths_json(self, session):
        """Test thumbnail paths JSON field."""
        product = Product(type="image", file_path="/test.jpg")

        thumbnail_paths = {
            "small": "/thumbnails/small_test.jpg",
            "medium": "/thumbnails/medium_test.jpg",
            "large": "/thumbnails/large_test.jpg",
        }
        product.thumbnail_paths = thumbnail_paths

        session.add(product)
        session.commit()

        # Reload and verify
        session.expunge(product)
        reloaded = session.query(Product).filter_by(id=product.id).first()

        assert reloaded.thumbnail_paths == thumbnail_paths
        assert reloaded.has_thumbnails

    def test_get_thumbnail_path(self, session):
        """Test getting thumbnail paths."""
        product = Product(type="image", file_path="/test.jpg")

        # No thumbnails
        assert product.get_thumbnail_path() is None
        assert product.get_thumbnail_path("small") is None

        # With thumbnails
        product.thumbnail_paths = {
            "small": "/small.jpg",
            "medium": "/medium.jpg",
            "large": "/large.jpg",
        }

        assert product.get_thumbnail_path() == "/medium.jpg"  # Default
        assert product.get_thumbnail_path("small") == "/small.jpg"
        assert product.get_thumbnail_path("large") == "/large.jpg"
        assert product.get_thumbnail_path("xlarge") is None  # Non-existent

    def test_metadata_json(self, session):
        """Test metadata JSON field."""
        product = Product(type="image", file_path="/test.jpg")

        metadata = {
            "exif": {"camera": "Canon EOS R5", "iso": 100, "aperture": 2.8},
            "ai_params": {"model": "SDXL", "steps": 30, "cfg": 7.5},
        }
        product.extra_metadata = metadata

        session.add(product)
        session.commit()

        # Reload and verify
        session.expunge(product)
        reloaded = session.query(Product).filter_by(id=product.id).first()

        assert reloaded.extra_metadata == metadata
        assert reloaded.extra_metadata["exif"]["camera"] == "Canon EOS R5"
        assert reloaded.extra_metadata["ai_params"]["steps"] == 30

    def test_calculate_file_hash(self, session):
        """Test file hash calculation."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content for hashing")
            temp_path = f.name

        try:
            product = Product(type="image", file_path=temp_path)
            session.add(product)
            session.commit()

            # Calculate hash
            hash_value = product.calculate_file_hash()

            assert hash_value is not None
            assert len(hash_value) == 64  # SHA256 hex length
            assert product.file_hash == hash_value

        finally:
            os.unlink(temp_path)

    def test_calculate_file_hash_missing_file(self, session):
        """Test file hash calculation with missing file."""
        product = Product(type="image", file_path="/nonexistent/file.jpg")
        session.add(product)
        session.commit()

        hash_value = product.calculate_file_hash()
        assert hash_value is None
        assert product.file_hash is None

    def test_update_file_info(self, session):
        """Test updating file info from filesystem."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content for file info")
            temp_path = f.name

        try:
            product = Product(type="image", file_path=temp_path)
            session.add(product)
            session.commit()

            # Update file info
            product.update_file_info()

            assert product.file_size is not None
            assert product.file_size > 0
            assert product.file_hash is not None
            assert len(product.file_hash) == 64

        finally:
            os.unlink(temp_path)

    def test_product_repr(self, session):
        """Test product string representation."""
        product = Product(type="image", file_path="/test/image.jpg")
        session.add(product)
        session.commit()

        repr_str = repr(product)
        assert "image" in repr_str
        assert "/test/image.jpg" in repr_str
        assert product.id in repr_str
