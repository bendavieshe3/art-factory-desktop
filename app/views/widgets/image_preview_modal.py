"""
Image preview modal for full-size viewing with zoom, pan, and navigation.
"""

from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPixmap,
    QPainter,
    QWheelEvent,
    QMouseEvent,
    QKeyEvent,
    QTransform,
)
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QToolBar,
    QSizePolicy,
)
from typing import List, Optional
from pathlib import Path


class ImageViewer(QGraphicsView):
    """Custom graphics view for image display with zoom and pan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.image_item: Optional[QGraphicsPixmapItem] = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.is_panning = False
        self.pan_start_pos = QPointF()

        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

    def set_image(self, pixmap: QPixmap):
        """Set the image to display."""
        self.scene.clear()
        self.image_item = self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(pixmap.rect())
        self.fit_in_view()

    def fit_in_view(self):
        """Fit the image in the view."""
        if self.image_item:
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom_factor = self.transform().m11()

    def zoom_in(self):
        """Zoom in by 25%."""
        self.scale_view(1.25)

    def zoom_out(self):
        """Zoom out by 25%."""
        self.scale_view(0.8)

    def zoom_actual(self):
        """Reset to actual size (100%)."""
        self.resetTransform()
        self.zoom_factor = 1.0

    def scale_view(self, factor: float):
        """Scale the view by the given factor."""
        new_zoom = self.zoom_factor * factor

        if new_zoom < self.min_zoom or new_zoom > self.max_zoom:
            return

        self.scale(factor, factor)
        self.zoom_factor = new_zoom

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl+Wheel
            delta = event.angleDelta().y()
            factor = 1.1 if delta > 0 else 0.9
            self.scale_view(factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() == Qt.KeyboardModifier.ShiftModifier
        ):
            self.is_panning = True
            self.pan_start_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for panning."""
        if self.is_panning:
            delta = event.position() - self.pan_start_pos
            self.pan_start_pos = event.position()

            # Pan the view
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(int(h_bar.value() - delta.x()))
            v_bar.setValue(int(v_bar.value() - delta.y()))

            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop panning."""
        if self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to toggle fit/actual size."""
        if event.button() == Qt.MouseButton.LeftButton:
            if abs(self.zoom_factor - 1.0) < 0.01:
                self.fit_in_view()
            else:
                self.zoom_actual()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class ImagePreviewModal(QDialog):
    """Modal dialog for full-size image preview with navigation."""

    # Signals
    navigate_previous = pyqtSignal()
    navigate_next = pyqtSignal()
    delete_requested = pyqtSignal(str)  # product_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_product_id: Optional[str] = None
        self.product_list: List[str] = []
        self.current_index = 0

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI for the preview modal."""
        self.setWindowTitle("Image Preview")
        self.setModal(True)
        self.resize(1200, 800)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        layout.addWidget(self.toolbar)

        # Image viewer (create before toolbar actions that reference it)
        self.viewer = ImageViewer()
        layout.addWidget(self.viewer)

        # Add toolbar actions (after viewer is created)
        self._create_toolbar_actions()

        # Bottom navigation bar
        nav_widget = QWidget()
        nav_widget.setMaximumHeight(60)
        nav_layout = QHBoxLayout(nav_widget)

        # Previous button
        self.prev_button = QPushButton("◀ Previous")
        self.prev_button.clicked.connect(self._navigate_previous)
        nav_layout.addWidget(self.prev_button)

        # Current position label
        self.position_label = QLabel("1 of 1")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.position_label)

        # Next button
        self.next_button = QPushButton("Next ▶")
        self.next_button.clicked.connect(self._navigate_next)
        nav_layout.addWidget(self.next_button)

        layout.addWidget(nav_widget)

        # Set dark background for better image viewing
        self.setStyleSheet(
            """
            ImagePreviewModal {
                background-color: #2b2b2b;
            }
            QToolBar {
                background-color: #3c3c3c;
                border: none;
                padding: 5px;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #4a4a4a;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #888;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            """
        )

    def _create_toolbar_actions(self):
        """Create toolbar actions for image controls."""
        # Zoom in
        zoom_in_action = self.toolbar.addAction("🔍+")
        zoom_in_action.setToolTip("Zoom In (Ctrl++)")
        zoom_in_action.triggered.connect(self.viewer.zoom_in)

        # Zoom out
        zoom_out_action = self.toolbar.addAction("🔍-")
        zoom_out_action.setToolTip("Zoom Out (Ctrl+-)")
        zoom_out_action.triggered.connect(self.viewer.zoom_out)

        # Fit to window
        fit_action = self.toolbar.addAction("⬜")
        fit_action.setToolTip("Fit to Window (F)")
        fit_action.triggered.connect(self.viewer.fit_in_view)

        # Actual size
        actual_action = self.toolbar.addAction("1:1")
        actual_action.setToolTip("Actual Size (1)")
        actual_action.triggered.connect(self.viewer.zoom_actual)

        self.toolbar.addSeparator()

        # Full screen toggle
        fullscreen_action = self.toolbar.addAction("⛶")
        fullscreen_action.setToolTip("Toggle Fullscreen (F11)")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)

        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        # Info label for zoom level
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: white; padding: 0 10px;")
        self.toolbar.addWidget(self.zoom_label)

    def _connect_signals(self):
        """Connect internal signals."""
        # Update zoom label when view changes
        self.viewer.scale(1, 1)  # Trigger initial update

    def _navigate_previous(self):
        """Navigate to previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.navigate_previous.emit()
            self._update_navigation()

    def _navigate_next(self):
        """Navigate to next image."""
        if self.current_index < len(self.product_list) - 1:
            self.current_index += 1
            self.navigate_next.emit()
            self._update_navigation()

    def _update_navigation(self):
        """Update navigation button states and position label."""
        total = len(self.product_list)
        current = self.current_index + 1 if total > 0 else 0

        self.position_label.setText(f"{current} of {total}")
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < total - 1)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def set_image(self, product_id: str, image_path: Path):
        """Set the image to display."""
        self.current_product_id = product_id

        if image_path.exists():
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                self.viewer.set_image(pixmap)
                self.setWindowTitle(f"Image Preview - {image_path.name}")
                self._update_zoom_label()
            else:
                # Show error placeholder
                self._show_error("Failed to load image")
        else:
            self._show_error("Image file not found")

    def set_product_list(self, product_ids: List[str], current_id: str):
        """Set the list of products for navigation."""
        self.product_list = product_ids
        try:
            self.current_index = product_ids.index(current_id)
        except ValueError:
            self.current_index = 0
        self._update_navigation()

    def _show_error(self, message: str):
        """Show error message in viewer."""
        error_pixmap = QPixmap(400, 300)
        error_pixmap.fill(Qt.GlobalColor.darkGray)

        painter = QPainter(error_pixmap)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(error_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, message)
        painter.end()

        self.viewer.set_image(error_pixmap)

    def _update_zoom_label(self):
        """Update the zoom level label."""
        zoom_percent = int(self.viewer.zoom_factor * 100)
        self.zoom_label.setText(f"{zoom_percent}%")

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        key = event.key()

        if key == Qt.Key.Key_Left:
            self._navigate_previous()
        elif key == Qt.Key.Key_Right:
            self._navigate_next()
        elif key == Qt.Key.Key_F:
            self.viewer.fit_in_view()
        elif key == Qt.Key.Key_1:
            self.viewer.zoom_actual()
        elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.viewer.zoom_in()
        elif key == Qt.Key.Key_Minus:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.viewer.zoom_out()
        elif key == Qt.Key.Key_F11:
            self._toggle_fullscreen()
        elif key == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.close()
        else:
            super().keyPressEvent(event)
