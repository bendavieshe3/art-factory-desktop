"""
Unit tests for gallery widget components.
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap
from PyQt6.QtTest import QTest

from app.views.widgets.gallery_widget import GalleryWidget, GalleryItemWidget
from app.views.widgets.thumbnail_loader import ThumbnailCache
from app.views.widgets.image_preview_modal import ImagePreviewModal


class TestGalleryItemWidget:
    """Test cases for individual gallery item widget."""

    def test_item_creation(self, qtbot):
        """Test creating a gallery item widget."""
        item = GalleryItemWidget("test-product-123")
        qtbot.addWidget(item)

        assert item.product_id == "test-product-123"
        assert not item.is_selected
        assert item.size().width() == 180
        assert item.size().height() == 180

    def test_item_selection(self, qtbot):
        """Test item selection state changes."""
        item = GalleryItemWidget("test-product")
        qtbot.addWidget(item)

        # Initially not selected
        assert not item.is_selected

        # Set selected
        item.set_selected(True)
        assert item.is_selected

        # Set unselected
        item.set_selected(False)
        assert not item.is_selected

    def test_item_thumbnail(self, qtbot):
        """Test setting thumbnail on item."""
        item = GalleryItemWidget("test-product")
        qtbot.addWidget(item)

        # Create test pixmap
        test_pixmap = QPixmap(100, 100)
        test_pixmap.fill(Qt.GlobalColor.red)

        # Set thumbnail
        item.set_thumbnail(test_pixmap)
        assert item.thumbnail_pixmap is not None
        assert item.thumbnail_pixmap.size().width() == 180
        assert item.thumbnail_pixmap.size().height() == 180

    def test_item_signals(self, qtbot):
        """Test item signal emissions."""
        item = GalleryItemWidget("test-product")
        qtbot.addWidget(item)

        # Track signals
        clicked_signals = []
        double_clicked_signals = []

        item.clicked.connect(lambda pid: clicked_signals.append(pid))
        item.double_clicked.connect(lambda pid: double_clicked_signals.append(pid))

        # Test single click
        QTest.mouseClick(item, Qt.MouseButton.LeftButton)
        assert "test-product" in clicked_signals

        # Test double click
        QTest.mouseDClick(item, Qt.MouseButton.LeftButton)
        assert "test-product" in double_clicked_signals


class TestGalleryWidget:
    """Test cases for main gallery widget."""

    def test_gallery_creation(self, qtbot):
        """Test creating a gallery widget."""
        gallery = GalleryWidget()
        qtbot.addWidget(gallery)

        assert gallery.columns == 4
        assert len(gallery.products) == 0
        assert len(gallery.selected_items) == 0
        assert len(gallery.items) == 0

    def test_column_calculation(self, qtbot):
        """Test responsive column calculation."""
        gallery = GalleryWidget()
        qtbot.addWidget(gallery)

        # Test different widths
        gallery.resize(800, 600)  # Should fit 4 columns (4 * 190 = 760)
        gallery._update_column_count()
        assert gallery.columns == 4

        gallery.resize(1200, 600)  # Should fit 6 columns (6 * 190 = 1140)
        gallery._update_column_count()
        assert gallery.columns == 6

        gallery.resize(400, 600)  # Should use minimum 4 columns
        gallery._update_column_count()
        assert gallery.columns == 4

    def test_set_products(self, qtbot):
        """Test setting products in gallery."""
        gallery = GalleryWidget()
        qtbot.addWidget(gallery)

        # Create test products
        test_products = [
            {"id": "product-1", "name": "Test Product 1"},
            {"id": "product-2", "name": "Test Product 2"},
            {"id": "product-3", "name": "Test Product 3"},
        ]

        gallery.set_products(test_products)

        assert len(gallery.products) == 3
        assert gallery.products[0]["id"] == "product-1"

    def test_virtual_scrolling_range(self, qtbot):
        """Test virtual scrolling visible range calculation."""
        gallery = GalleryWidget()
        qtbot.addWidget(gallery)

        # Create many test products
        test_products = [{"id": f"product-{i}", "name": f"Test Product {i}"} for i in range(100)]

        gallery.set_products(test_products)

        # Test range calculation
        start, end = gallery._calculate_visible_range()

        # Should have buffer items
        assert start >= 0
        assert end <= len(test_products)
        assert end > start

    def test_selection_signals(self, qtbot):
        """Test selection change signals."""
        gallery = GalleryWidget()
        qtbot.addWidget(gallery)

        # Track selection signals
        selection_changes = []
        gallery.selection_changed.connect(lambda items: selection_changes.append(items))

        # Create test products and items
        test_products = [
            {"id": "product-1", "name": "Test Product 1"},
            {"id": "product-2", "name": "Test Product 2"},
        ]

        gallery.set_products(test_products)
        gallery._update_visible_items()

        # Simulate item click
        if "product-1" in gallery.items:
            gallery._on_item_clicked("product-1")
            assert len(selection_changes) > 0
            assert "product-1" in selection_changes[-1]

    def test_keyboard_navigation(self, qtbot):
        """Test keyboard navigation in gallery."""
        gallery = GalleryWidget()
        qtbot.addWidget(gallery)

        # Create test products
        test_products = [{"id": f"product-{i}", "name": f"Test Product {i}"} for i in range(10)]

        gallery.set_products(test_products)
        gallery._update_visible_items()

        # Test arrow key navigation
        QTest.keyPress(gallery, Qt.Key.Key_Right)
        # Should select first item

        QTest.keyPress(gallery, Qt.Key.Key_Left)
        # Should move selection

        QTest.keyPress(gallery, Qt.Key.Key_Down)
        # Should move down a row


class TestThumbnailCache:
    """Test cases for thumbnail cache."""

    def test_cache_creation(self):
        """Test creating thumbnail cache."""
        cache = ThumbnailCache(cache_size_mb=50)
        assert cache is not None

    def test_cache_operations(self):
        """Test cache put and get operations."""
        cache = ThumbnailCache()

        # Create test pixmap
        test_pixmap = QPixmap(100, 100)
        test_pixmap.fill(Qt.GlobalColor.blue)

        # Test put
        cache.put("test-product", test_pixmap)

        # Test get
        cached_pixmap = cache.get("test-product")
        assert cached_pixmap is not None

        # Test miss
        missing_pixmap = cache.get("nonexistent-product")
        assert missing_pixmap is None

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = ThumbnailCache()

        # Add item
        test_pixmap = QPixmap(50, 50)
        cache.put("test-product", test_pixmap)

        # Verify it exists
        assert cache.get("test-product") is not None

        # Clear cache
        cache.clear()

        # Verify it's gone
        assert cache.get("test-product") is None


class TestImagePreviewModal:
    """Test cases for image preview modal."""

    def test_modal_creation(self, qtbot):
        """Test creating image preview modal."""
        modal = ImagePreviewModal()
        qtbot.addWidget(modal)

        assert modal.windowTitle() == "Image Preview"
        assert modal.isModal()

    def test_navigation_setup(self, qtbot):
        """Test navigation setup with product list."""
        modal = ImagePreviewModal()
        qtbot.addWidget(modal)

        product_ids = ["product-1", "product-2", "product-3"]
        modal.set_product_list(product_ids, "product-2")

        assert modal.product_list == product_ids
        assert modal.current_index == 1  # product-2 is at index 1

    def test_navigation_buttons(self, qtbot):
        """Test navigation button states."""
        modal = ImagePreviewModal()
        qtbot.addWidget(modal)

        # Single item - both buttons disabled
        modal.set_product_list(["product-1"], "product-1")
        assert not modal.prev_button.isEnabled()
        assert not modal.next_button.isEnabled()

        # Multiple items - test boundary conditions
        modal.set_product_list(["product-1", "product-2", "product-3"], "product-1")
        assert not modal.prev_button.isEnabled()  # At beginning
        assert modal.next_button.isEnabled()

        modal.set_product_list(["product-1", "product-2", "product-3"], "product-3")
        assert modal.prev_button.isEnabled()
        assert not modal.next_button.isEnabled()  # At end

    def test_keyboard_shortcuts(self, qtbot):
        """Test keyboard shortcuts in preview modal."""
        modal = ImagePreviewModal()
        qtbot.addWidget(modal)

        # Test escape key (should close modal)
        QTest.keyPress(modal, Qt.Key.Key_Escape)

        # Test arrow keys
        modal.set_product_list(["product-1", "product-2"], "product-1")
        QTest.keyPress(modal, Qt.Key.Key_Right)  # Should navigate next

        QTest.keyPress(modal, Qt.Key.Key_Left)  # Should navigate previous


def test_gallery_integration(qtbot):
    """Test integration between gallery components."""
    gallery = GalleryWidget()
    qtbot.addWidget(gallery)

    # Test signals are properly connected
    assert gallery.selection_changed is not None
    assert gallery.product_double_clicked is not None
    assert gallery.products_deleted is not None

    # Test products can be set
    test_products = [{"id": "test-1", "name": "Test"}]
    gallery.set_products(test_products)
    assert len(gallery.products) == 1


if __name__ == "__main__":
    # Run tests if executed directly
    app = QApplication([])
    pytest.main([__file__])
