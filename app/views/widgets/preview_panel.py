"""
Preview panel for the Generate screen.

Shows live preview of generation parameters and recent generations.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPalette


class PreviewPanel(QWidget):
    """
    Central panel for the Generate screen.

    Shows preview of current generation settings and recent results.
    """

    # Signals
    preview_clicked = pyqtSignal(str)  # product_id
    use_as_input = pyqtSignal(str)  # product_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recent_products = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the preview panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("Generation Preview")
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #333;"
        )
        layout.addWidget(title_label)

        # Current settings preview
        settings_frame = QFrame()
        settings_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        settings_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        settings_layout = QVBoxLayout(settings_frame)

        settings_title = QLabel("Current Settings")
        settings_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        settings_layout.addWidget(settings_title)

        self.prompt_preview = QLabel("No prompt entered")
        self.prompt_preview.setWordWrap(True)
        self.prompt_preview.setStyleSheet("color: #666; padding: 8px;")
        settings_layout.addWidget(self.prompt_preview)

        self.settings_preview = QLabel("Model: None selected")
        self.settings_preview.setStyleSheet("color: #888; font-size: 12px;")
        settings_layout.addWidget(self.settings_preview)

        layout.addWidget(settings_frame)

        # Recent generations section
        recent_label = QLabel("Recent Generations")
        recent_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(recent_label)

        # Scroll area for recent items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Recent items container
        self.recent_container = QWidget()
        self.recent_layout = QGridLayout(self.recent_container)
        self.recent_layout.setSpacing(12)
        self.recent_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        # No recent items message
        self.no_recent_label = QLabel("No recent generations")
        self.no_recent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_recent_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 14px;
                padding: 40px;
            }
        """)
        self.recent_layout.addWidget(self.no_recent_label, 0, 0)

        scroll_area.setWidget(self.recent_container)
        layout.addWidget(scroll_area)

        # Action buttons
        actions_layout = QHBoxLayout()

        self.clear_button = QPushButton("Clear History")
        self.clear_button.setEnabled(False)
        actions_layout.addWidget(self.clear_button)

        actions_layout.addStretch()

        self.generate_more_button = QPushButton("Generate Variations")
        self.generate_more_button.setEnabled(False)
        self.generate_more_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #0056CC;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        actions_layout.addWidget(self.generate_more_button)

        layout.addLayout(actions_layout)

    def update_preview(self, prompt: str, model: str, params: dict):
        """Update the preview with current generation settings."""
        if prompt:
            self.prompt_preview.setText(f'Prompt: "{prompt}"')
            self.prompt_preview.setStyleSheet("color: #333; padding: 8px;")
        else:
            self.prompt_preview.setText("No prompt entered")
            self.prompt_preview.setStyleSheet("color: #666; padding: 8px;")

        if model:
            param_text = f"Model: {model}"
            if params:
                size = f"{params.get('width', '?')}x{params.get('height', '?')}"
                steps = params.get('steps', '?')
                param_text += f" | Size: {size} | Steps: {steps}"
            self.settings_preview.setText(param_text)
        else:
            self.settings_preview.setText("Model: None selected")

    def add_recent_generation(self, product_data):
        """Add a recently generated product to the preview."""
        # Implementation for adding recent generation preview cards
        # This would create thumbnail cards similar to project cards
        self._recent_products.append(product_data)
        self._update_recent_display()

    def _update_recent_display(self):
        """Update the recent generations display."""
        # Clear existing items except the no_recent_label
        for i in reversed(range(self.recent_layout.count())):
            item = self.recent_layout.itemAt(i)
            if item and item.widget() != self.no_recent_label:
                self.recent_layout.removeWidget(item.widget())
                item.widget().deleteLater()

        if not self._recent_products:
            self.no_recent_label.show()
            self.clear_button.setEnabled(False)
            self.generate_more_button.setEnabled(False)
        else:
            self.no_recent_label.hide()
            self.clear_button.setEnabled(True)
            self.generate_more_button.setEnabled(True)

            # Add recent product preview cards in a grid
            columns = 3
            for i, product in enumerate(self._recent_products[:9]):  # Show last 9
                row = i // columns
                col = i % columns

                # Create simple preview card
                card = self._create_preview_card(product)
                self.recent_layout.addWidget(card, row, col)

    def _create_preview_card(self, product_data):
        """Create a preview card for a recent generation."""
        card = QFrame()
        card.setFixedSize(150, 150)
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QFrame:hover {
                border-color: #007AFF;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)

        # Placeholder for image
        image_label = QLabel("Image")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("color: #999; padding: 20px;")
        layout.addWidget(image_label)

        # Timestamp or ID
        info_label = QLabel(product_data.get("id", "Unknown")[:8])
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(info_label)

        return card

    def clear_history(self):
        """Clear the recent generations history."""
        self._recent_products = []
        self._update_recent_display()