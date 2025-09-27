"""
Metadata panel for product inspection.

Right-docked panel for examining selected products and their properties.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QScrollArea,
    QTextEdit,
    QSpinBox,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal


class MetadataPanel(QWidget):
    """
    Right dock panel for product metadata and inspection.

    Provides interface for:
    - Selected product details
    - File information
    - Generation parameters used
    - Product actions (like, rate, export)
    """

    # Signals
    product_liked = pyqtSignal(str, bool)  # product_id, liked
    product_rated = pyqtSignal(str, int)  # product_id, rating
    product_exported = pyqtSignal(str)  # product_id
    product_deleted = pyqtSignal(str)  # product_id
    regenerate_requested = pyqtSignal(str)  # product_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_product = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the metadata panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("Product Details")
        title_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #333;"
        )
        layout.addWidget(title_label)

        # Scroll area for metadata
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Metadata widget
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(12)

        # No selection message
        self.no_selection_label = QLabel("No product selected")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #999; padding: 40px;")
        metadata_layout.addWidget(self.no_selection_label)

        # Product info container (hidden initially)
        self.product_container = QWidget()
        product_layout = QVBoxLayout(self.product_container)
        product_layout.setContentsMargins(0, 0, 0, 0)
        product_layout.setSpacing(12)

        # Thumbnail preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setMinimumHeight(150)
        self.thumbnail_label.setStyleSheet(
            """
            QLabel {
                border: 1px solid #ddd;
                background-color: #f9f9f9;
                border-radius: 4px;
            }
        """
        )
        preview_layout.addWidget(self.thumbnail_label)

        product_layout.addWidget(preview_group)

        # Basic info
        info_group = QGroupBox("File Information")
        info_layout = QGridLayout(info_group)

        self.filename_label = QLabel()
        self.filetype_label = QLabel()
        self.filesize_label = QLabel()
        self.dimensions_label = QLabel()
        self.created_label = QLabel()

        info_layout.addWidget(QLabel("File:"), 0, 0)
        info_layout.addWidget(self.filename_label, 0, 1)
        info_layout.addWidget(QLabel("Type:"), 1, 0)
        info_layout.addWidget(self.filetype_label, 1, 1)
        info_layout.addWidget(QLabel("Size:"), 2, 0)
        info_layout.addWidget(self.filesize_label, 2, 1)
        info_layout.addWidget(QLabel("Dimensions:"), 3, 0)
        info_layout.addWidget(self.dimensions_label, 3, 1)
        info_layout.addWidget(QLabel("Created:"), 4, 0)
        info_layout.addWidget(self.created_label, 4, 1)

        product_layout.addWidget(info_group)

        # User interactions
        interaction_group = QGroupBox("Actions")
        interaction_layout = QVBoxLayout(interaction_group)

        # Like button
        self.like_button = QPushButton("♡ Like")
        self.like_button.setCheckable(True)
        self.like_button.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton:checked {
                color: #FF3B30;
                border-color: #FF3B30;
            }
        """
        )
        interaction_layout.addWidget(self.like_button)

        # Rating
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(QLabel("Rating:"))
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(0, 5)
        self.rating_spin.setSpecialValueText("None")
        self.rating_spin.setSuffix(" stars")
        rating_layout.addWidget(self.rating_spin)
        rating_layout.addStretch()
        interaction_layout.addLayout(rating_layout)

        # Notes
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Add notes about this product...")
        self.notes_text.setMaximumHeight(80)
        interaction_layout.addWidget(QLabel("Notes:"))
        interaction_layout.addWidget(self.notes_text)

        product_layout.addWidget(interaction_group)

        # Generation parameters (if available)
        self.params_group = QGroupBox("Generation Parameters")
        params_layout = QVBoxLayout(self.params_group)

        self.params_text = QTextEdit()
        self.params_text.setReadOnly(True)
        self.params_text.setMaximumHeight(120)
        self.params_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #f9f9f9;
                font-family: monospace;
                font-size: 11px;
            }
        """
        )
        params_layout.addWidget(self.params_text)

        product_layout.addWidget(self.params_group)

        # Action buttons
        actions_layout = QHBoxLayout()

        self.export_button = QPushButton("Export...")
        actions_layout.addWidget(self.export_button)

        self.regenerate_button = QPushButton("Regenerate")
        self.regenerate_button.setStyleSheet(
            """
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #30B74D;
            }
        """
        )
        actions_layout.addWidget(self.regenerate_button)

        actions_layout.addStretch()

        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D70015;
            }
        """
        )
        actions_layout.addWidget(self.delete_button)

        product_layout.addLayout(actions_layout)

        # Stretch to push content to top
        product_layout.addStretch()

        metadata_layout.addWidget(self.product_container)
        self.product_container.hide()

        scroll_area.setWidget(metadata_widget)
        layout.addWidget(scroll_area)

    def _connect_signals(self):
        """Connect internal signals."""
        self.like_button.toggled.connect(self._on_like_toggled)
        self.rating_spin.valueChanged.connect(self._on_rating_changed)
        self.export_button.clicked.connect(self._on_export_clicked)
        self.regenerate_button.clicked.connect(self._on_regenerate_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)

    def set_product(self, product):
        """Set the product to display metadata for."""
        self._current_product = product

        if product is None:
            self.no_selection_label.show()
            self.product_container.hide()
            return

        self.no_selection_label.hide()
        self.product_container.show()

        # Update file information
        self.filename_label.setText(
            product.get("file_path", "Unknown").split("/")[-1]
        )
        self.filetype_label.setText(product.get("type", "Unknown").title())

        file_size = product.get("file_size", 0)
        if file_size > 0:
            if file_size > 1024 * 1024:
                self.filesize_label.setText(
                    f"{file_size / (1024*1024):.1f} MB"
                )
            elif file_size > 1024:
                self.filesize_label.setText(f"{file_size / 1024:.1f} KB")
            else:
                self.filesize_label.setText(f"{file_size} bytes")
        else:
            self.filesize_label.setText("Unknown")

        width = product.get("width", 0)
        height = product.get("height", 0)
        if width and height:
            self.dimensions_label.setText(f"{width} × {height}")
        else:
            self.dimensions_label.setText("Unknown")

        created_at = product.get("created_at", "Unknown")
        self.created_label.setText(str(created_at))

        # Update interactions
        self.like_button.setChecked(product.get("liked", False))
        self.like_button.setText(
            "♥ Liked" if product.get("liked", False) else "♡ Like"
        )

        rating = product.get("rating", 0)
        self.rating_spin.setValue(rating)

        notes = product.get("notes", "")
        self.notes_text.setPlainText(notes)

        # Update generation parameters if available
        extra_metadata = product.get("extra_metadata", {})
        if extra_metadata:
            params_text = ""
            for key, value in extra_metadata.items():
                params_text += f"{key}: {value}\n"
            self.params_text.setPlainText(params_text)
            self.params_group.show()
        else:
            self.params_group.hide()

        # Update thumbnail (placeholder for now)
        self.thumbnail_label.setText("Thumbnail\n(Not implemented)")

    def _on_like_toggled(self, liked):
        """Handle like button toggle."""
        if self._current_product:
            self.like_button.setText("♥ Liked" if liked else "♡ Like")
            product_id = self._current_product.get("id")
            if product_id:
                self.product_liked.emit(product_id, liked)

    def _on_rating_changed(self, rating):
        """Handle rating change."""
        if self._current_product:
            product_id = self._current_product.get("id")
            if product_id:
                self.product_rated.emit(product_id, rating)

    def _on_export_clicked(self):
        """Handle export button click."""
        if self._current_product:
            product_id = self._current_product.get("id")
            if product_id:
                self.product_exported.emit(product_id)

    def _on_regenerate_clicked(self):
        """Handle regenerate button click."""
        if self._current_product:
            product_id = self._current_product.get("id")
            if product_id:
                self.regenerate_requested.emit(product_id)

    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self._current_product:
            product_id = self._current_product.get("id")
            if product_id:
                from PyQt6.QtWidgets import QMessageBox

                reply = QMessageBox.question(
                    self,
                    "Confirm Delete",
                    "Are you sure you want to delete this product?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.product_deleted.emit(product_id)

    def clear_selection(self):
        """Clear the current product selection."""
        self.set_product(None)
