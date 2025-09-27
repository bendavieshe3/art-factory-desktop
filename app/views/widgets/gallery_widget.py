"""
Gallery widget for displaying products in a responsive grid layout.

Features:
- Responsive grid layout (4-8 columns based on width)
- Virtual scrolling for performance with large datasets
- Aspect-ratio preserved thumbnails in 180x180 containers
- Single and multi-selection support
- Context menu actions
- Drag and drop support
- Image preview on double-click
"""

from PyQt6.QtCore import (
    Qt,
    QSize,
    QPoint,
    QRect,
    pyqtSignal,
    QTimer,
    QThread,
    QMimeData,
    QUrl,
    QByteArray,
)
from PyQt6.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QAction,
    QPalette,
    QDrag,
    QKeyEvent,
    QResizeEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
)
from PyQt6.QtWidgets import (
    QWidget,
    QScrollArea,
    QGridLayout,
    QVBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QFrame,
)
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import math


class GalleryItemWidget(QFrame):
    """Individual gallery item widget with thumbnail and selection support."""

    clicked = pyqtSignal(str)  # product_id
    double_clicked = pyqtSignal(str)  # product_id
    context_menu_requested = pyqtSignal(QPoint, str)  # position, product_id

    def __init__(self, product_id: str, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.is_selected = False
        self.thumbnail_path: Optional[Path] = None
        self.thumbnail_pixmap: Optional[QPixmap] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI for the gallery item."""
        self.setFixedSize(QSize(180, 180))
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet(
            """
            GalleryItemWidget {
                background-color: #f0f0f0;
                border: 2px solid transparent;
                border-radius: 4px;
            }
            GalleryItemWidget:hover {
                background-color: #e0e0e0;
            }
            """
        )

        # Thumbnail label
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setScaledContents(False)
        self.thumbnail_label.setMinimumSize(180, 180)
        self.thumbnail_label.setMaximumSize(180, 180)

        # Set placeholder
        self._set_placeholder()

        layout.addWidget(self.thumbnail_label)

    def _set_placeholder(self):
        """Set placeholder image while loading."""
        self.thumbnail_label.setText("📷\nLoading...")
        self.thumbnail_label.setStyleSheet(
            """
            QLabel {
                color: #888;
                font-size: 14px;
                background-color: #f5f5f5;
            }
            """
        )

    def set_thumbnail(self, pixmap: QPixmap):
        """Set the thumbnail image with aspect ratio preservation."""
        if pixmap.isNull():
            self._set_placeholder()
            return

        # Scale pixmap to fit within 180x180 while preserving aspect ratio
        scaled_pixmap = pixmap.scaled(
            QSize(180, 180),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Create a new pixmap with transparent background for centering
        final_pixmap = QPixmap(180, 180)
        final_pixmap.fill(Qt.GlobalColor.transparent)

        # Paint the scaled image centered
        painter = QPainter(final_pixmap)
        x = (180 - scaled_pixmap.width()) // 2
        y = (180 - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()

        self.thumbnail_label.setPixmap(final_pixmap)
        self.thumbnail_pixmap = final_pixmap

    def set_selected(self, selected: bool):
        """Set selection state of the item."""
        self.is_selected = selected
        if selected:
            self.setStyleSheet(
                """
                GalleryItemWidget {
                    background-color: #e3f2fd;
                    border: 2px solid #2196F3;
                    border-radius: 4px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                GalleryItemWidget {
                    background-color: #f0f0f0;
                    border: 2px solid transparent;
                    border-radius: 4px;
                }
                GalleryItemWidget:hover {
                    background-color: #e0e0e0;
                }
                """
            )

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.product_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.product_id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """Handle context menu events."""
        self.context_menu_requested.emit(event.globalPos(), self.product_id)

    def mouseMoveEvent(self, event):
        """Handle mouse move for drag and drop."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Start drag operation
            drag_distance = (event.pos() - event.position().toPoint()).manhattanLength()
            if drag_distance > QApplication.startDragDistance():
                self._start_drag()
        super().mouseMoveEvent(event)

    def _start_drag(self):
        """Start drag operation with thumbnail."""
        drag = QDrag(self)
        mime_data = QMimeData()

        # Add product ID as custom data
        mime_data.setData("application/x-artfactory-product", self.product_id.encode())

        # If we have a file path, add it as URL
        if self.thumbnail_path:
            mime_data.setUrls([QUrl.fromLocalFile(str(self.thumbnail_path))])

        # Set drag pixmap (thumbnail)
        if self.thumbnail_pixmap:
            drag.setPixmap(
                self.thumbnail_pixmap.scaled(
                    QSize(100, 100),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            drag.setHotSpot(QPoint(50, 50))

        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)


class GalleryWidget(QScrollArea):
    """Main gallery widget with responsive grid layout and virtual scrolling."""

    # Signals
    selection_changed = pyqtSignal(list)  # List of selected product IDs
    product_double_clicked = pyqtSignal(str)  # Product ID for preview
    products_deleted = pyqtSignal(list)  # List of product IDs to delete
    product_details_requested = pyqtSignal(str)  # Product ID for details
    files_dropped = pyqtSignal(list)  # List of file paths dropped

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: Dict[str, GalleryItemWidget] = {}
        self.selected_items: Set[str] = set()
        self.products: List[Dict] = []  # Product data
        self.visible_range: Tuple[int, int] = (0, 0)
        self.columns = 4
        self.last_clicked_item: Optional[str] = None

        self._setup_ui()
        self._connect_signals()
        self._setup_drag_drop()

    def _setup_ui(self):
        """Set up the UI for the gallery widget."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Main container widget
        self.container = QWidget()
        self.setWidget(self.container)

        # Grid layout for items
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)

        # Calculate initial columns based on width
        self._update_column_count()

    def _connect_signals(self):
        """Connect internal signals."""
        # Will connect scroll signals for virtual scrolling
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def _setup_drag_drop(self):
        """Set up drag and drop support."""
        self.setAcceptDrops(True)

    def _update_column_count(self):
        """Update number of columns based on widget width."""
        width = self.width()
        # 180px per item + 10px spacing
        item_width = 190
        new_columns = max(4, min(8, width // item_width))

        if new_columns != self.columns:
            self.columns = new_columns
            self._rebuild_grid()

    def _rebuild_grid(self):
        """Rebuild the grid layout with new column count."""
        # Clear existing items from layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().hide()

        # Re-add visible items
        self._update_visible_items()

    def _calculate_visible_range(self) -> Tuple[int, int]:
        """Calculate which items should be visible based on scroll position."""
        if not self.products:
            return (0, 0)

        viewport_height = self.viewport().height()
        scroll_pos = self.verticalScrollBar().value()

        # Calculate row heights (180px + 10px spacing)
        row_height = 190
        first_visible_row = max(0, (scroll_pos // row_height) - 1)
        visible_rows = (viewport_height // row_height) + 3  # Buffer rows

        first_item = first_visible_row * self.columns
        last_item = min(
            len(self.products), (first_visible_row + visible_rows) * self.columns
        )

        # Add buffer of 50 items above and below
        first_item = max(0, first_item - 50)
        last_item = min(len(self.products), last_item + 50)

        return (first_item, last_item)

    def _update_visible_items(self):
        """Update which items are visible based on virtual scrolling."""
        new_range = self._calculate_visible_range()

        if new_range == self.visible_range:
            return

        old_start, old_end = self.visible_range
        new_start, new_end = new_range

        # Hide items that are no longer visible
        for i in range(old_start, old_end):
            if i < new_start or i >= new_end:
                product_id = self.products[i].get("id")
                if product_id in self.items:
                    self.items[product_id].hide()

        # Show or create items that should be visible
        for i in range(new_start, new_end):
            if i < len(self.products):
                product = self.products[i]
                product_id = product.get("id")

                if product_id not in self.items:
                    # Create new item widget
                    item = self._create_item_widget(product)
                    self.items[product_id] = item

                # Position in grid
                row = i // self.columns
                col = i % self.columns
                self.grid_layout.addWidget(self.items[product_id], row, col)
                self.items[product_id].show()

        self.visible_range = new_range

        # Update container size
        total_rows = math.ceil(len(self.products) / self.columns)
        self.container.setMinimumHeight(total_rows * 190)

    def _create_item_widget(self, product: Dict) -> GalleryItemWidget:
        """Create a new gallery item widget for a product."""
        item = GalleryItemWidget(product.get("id"))

        # Connect item signals
        item.clicked.connect(self._on_item_clicked)
        item.double_clicked.connect(self._on_item_double_clicked)
        item.context_menu_requested.connect(self._on_context_menu)

        # Set selection state if already selected
        if product.get("id") in self.selected_items:
            item.set_selected(True)

        # TODO: Load thumbnail in background thread
        # For now, just set placeholder

        return item

    def _on_scroll(self):
        """Handle scroll events for virtual scrolling."""
        self._update_visible_items()

    def _on_item_clicked(self, product_id: str):
        """Handle item click for selection."""
        modifiers = QApplication.instance().keyboardModifiers()

        if modifiers == Qt.KeyboardModifier.ControlModifier:
            # Toggle selection
            if product_id in self.selected_items:
                self.selected_items.remove(product_id)
                self.items[product_id].set_selected(False)
            else:
                self.selected_items.add(product_id)
                self.items[product_id].set_selected(True)

        elif modifiers == Qt.KeyboardModifier.ShiftModifier and self.last_clicked_item:
            # Range selection
            self._select_range(self.last_clicked_item, product_id)

        else:
            # Single selection
            self._clear_selection()
            self.selected_items.add(product_id)
            if product_id in self.items:
                self.items[product_id].set_selected(True)

        self.last_clicked_item = product_id
        self.selection_changed.emit(list(self.selected_items))

    def _on_item_double_clicked(self, product_id: str):
        """Handle item double-click for preview."""
        self.product_double_clicked.emit(product_id)

    def _on_context_menu(self, position: QPoint, product_id: str):
        """Show context menu for item."""
        menu = QMenu(self)

        # Single item actions
        if product_id not in self.selected_items:
            self._clear_selection()
            self.selected_items.add(product_id)
            if product_id in self.items:
                self.items[product_id].set_selected(True)
            self.selection_changed.emit(list(self.selected_items))

        # Check if multiple items selected
        if len(self.selected_items) == 1:
            open_action = QAction("Open Preview", self)
            open_action.triggered.connect(
                lambda: self.product_double_clicked.emit(product_id)
            )
            menu.addAction(open_action)

            details_action = QAction("Show Details", self)
            details_action.triggered.connect(
                lambda: self.product_details_requested.emit(product_id)
            )
            menu.addAction(details_action)

            menu.addSeparator()

            copy_path_action = QAction("Copy Path", self)
            # TODO: Connect to copy path handler
            menu.addAction(copy_path_action)

            menu.addSeparator()

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(
                lambda: self.products_deleted.emit([product_id])
            )
            menu.addAction(delete_action)

        else:
            # Multi-selection actions
            selected_count = len(self.selected_items)

            delete_action = QAction(f"Delete {selected_count} items", self)
            delete_action.triggered.connect(
                lambda: self.products_deleted.emit(list(self.selected_items))
            )
            menu.addAction(delete_action)

            menu.addSeparator()

            export_action = QAction(f"Export {selected_count} items...", self)
            # TODO: Connect to export handler
            menu.addAction(export_action)

            collection_action = QAction(
                f"Add {selected_count} items to Collection...", self
            )
            # TODO: Connect to collection handler
            menu.addAction(collection_action)

        menu.exec(position)

    def _select_range(self, start_id: str, end_id: str):
        """Select a range of items between start and end."""
        start_idx = next(
            (i for i, p in enumerate(self.products) if p.get("id") == start_id), -1
        )
        end_idx = next(
            (i for i, p in enumerate(self.products) if p.get("id") == end_id), -1
        )

        if start_idx == -1 or end_idx == -1:
            return

        # Clear previous selection
        self._clear_selection()

        # Select range
        min_idx = min(start_idx, end_idx)
        max_idx = max(start_idx, end_idx)

        for i in range(min_idx, max_idx + 1):
            product_id = self.products[i].get("id")
            self.selected_items.add(product_id)
            if product_id in self.items:
                self.items[product_id].set_selected(True)

        self.selection_changed.emit(list(self.selected_items))

    def _clear_selection(self):
        """Clear all selections."""
        for product_id in self.selected_items:
            if product_id in self.items:
                self.items[product_id].set_selected(False)
        self.selected_items.clear()

    def set_products(self, products: List[Dict]):
        """Set the products to display in the gallery."""
        self.products = products
        self.visible_range = (0, 0)

        # Clear existing items
        for item in self.items.values():
            item.hide()
        self.items.clear()
        self.selected_items.clear()

        # Update visible items
        self._update_visible_items()

    def resizeEvent(self, event: QResizeEvent):
        """Handle resize events to update column count."""
        super().resizeEvent(event)
        self._update_column_count()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        if not self.products:
            return super().keyPressEvent(event)

        key = event.key()

        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            # Arrow key navigation
            if not self.last_clicked_item:
                # Select first item
                first_id = self.products[0].get("id")
                self._on_item_clicked(first_id)
            else:
                current_idx = next(
                    (
                        i
                        for i, p in enumerate(self.products)
                        if p.get("id") == self.last_clicked_item
                    ),
                    -1,
                )

                if current_idx != -1:
                    new_idx = current_idx

                    if key == Qt.Key.Key_Left:
                        new_idx = max(0, current_idx - 1)
                    elif key == Qt.Key.Key_Right:
                        new_idx = min(len(self.products) - 1, current_idx + 1)
                    elif key == Qt.Key.Key_Up:
                        new_idx = max(0, current_idx - self.columns)
                    elif key == Qt.Key.Key_Down:
                        new_idx = min(
                            len(self.products) - 1, current_idx + self.columns
                        )

                    if new_idx != current_idx:
                        new_id = self.products[new_idx].get("id")
                        self._on_item_clicked(new_id)

                        # Ensure item is visible
                        self._ensure_item_visible(new_idx)

        elif key == Qt.Key.Key_Return and self.last_clicked_item:
            # Enter key for preview
            self.product_double_clicked.emit(self.last_clicked_item)

        else:
            super().keyPressEvent(event)

    def _ensure_item_visible(self, item_index: int):
        """Ensure the item at the given index is visible."""
        row = item_index // self.columns
        row_y = row * 190

        viewport_height = self.viewport().height()
        scroll_pos = self.verticalScrollBar().value()

        if row_y < scroll_pos:
            self.verticalScrollBar().setValue(row_y)
        elif row_y + 190 > scroll_pos + viewport_height:
            self.verticalScrollBar().setValue(row_y + 190 - viewport_height)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        mime_data = event.mimeData()

        # Accept image files or internal product drags
        if mime_data.hasUrls():
            # Check if any URLs are image files
            for url in mime_data.urls():
                if url.isLocalFile():
                    path = Path(url.toLocalFile())
                    if path.suffix.lower() in [
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".gif",
                        ".bmp",
                        ".webp",
                    ]:
                        event.acceptProposedAction()
                        return
        elif mime_data.hasFormat("application/x-artfactory-product"):
            # Internal product drag
            event.acceptProposedAction()
            return

        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move events."""
        # Could add visual feedback here for drop zones
        if event.mimeData().hasUrls() or event.mimeData().hasFormat(
            "application/x-artfactory-product"
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            # Handle file drops
            file_paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    path = Path(url.toLocalFile())
                    if path.suffix.lower() in [
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".gif",
                        ".bmp",
                        ".webp",
                    ]:
                        file_paths.append(str(path))

            if file_paths:
                self.files_dropped.emit(file_paths)
                event.acceptProposedAction()
            else:
                event.ignore()

        elif mime_data.hasFormat("application/x-artfactory-product"):
            # Handle internal product drop (for future reordering)
            product_id = bytes(
                mime_data.data("application/x-artfactory-product")
            ).decode()
            # TODO: Implement reordering logic
            event.acceptProposedAction()
        else:
            event.ignore()


# Import QApplication for keyboard modifiers
from PyQt6.QtWidgets import QApplication
