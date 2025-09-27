"""
Progress panel for generation monitoring.

Bottom-docked panel for tracking ongoing operations and generation queue.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# QFont unused but kept for future use


class ProgressItemWidget(QWidget):
    """Widget representing a single generation task in progress."""

    cancel_requested = pyqtSignal(str)  # item_id

    def __init__(self, item_id, description, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self._setup_ui(description)

    def _setup_ui(self, description):
        """Set up the progress item UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Description
        self.description_label = QLabel(description)
        self.description_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.description_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(150)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Starting...")
        self.status_label.setMinimumWidth(80)
        layout.addWidget(self.status_label)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMaximumWidth(60)
        self.cancel_button.setMaximumHeight(24)
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #D70015;
            }
        """
        )
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(self.cancel_button)

        # Stretch
        layout.addStretch()

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.cancel_requested.emit(self.item_id)

    def update_progress(self, progress, status="Processing..."):
        """Update progress bar and status."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)

        if progress >= 100:
            self.cancel_button.setText("Remove")
            self.cancel_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #34C759;
                    color: white;
                    border: none;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #30B74D;
                }
            """
            )

    def set_error(self, error_message):
        """Set error state."""
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: #FF3B30;")
        self.cancel_button.setText("Remove")


class ProgressPanel(QWidget):
    """
    Bottom dock panel for progress monitoring.

    Provides interface for:
    - Active generation queue
    - Progress bars and status
    - Error messages and logs
    - Generation cancellation
    """

    # Signals
    generation_cancelled = pyqtSignal(str)  # item_id
    progress_cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress_items = {}  # item_id -> ProgressItemWidget
        self._setup_ui()
        self._setup_demo_timer()  # For demonstration

    def _setup_ui(self):
        """Set up the progress panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Generation Progress")
        title_label.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #333;"
        )
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Clear completed button
        self.clear_button = QPushButton("Clear Completed")
        self.clear_button.setMaximumHeight(24)
        self.clear_button.setStyleSheet(
            """
            QPushButton {
                background-color: #8E8E93;
                color: white;
                border: none;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #6D6D70;
            }
        """
        )
        self.clear_button.clicked.connect(self._on_clear_completed)
        header_layout.addWidget(self.clear_button)

        layout.addLayout(header_layout)

        # Progress items scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setMaximumHeight(120)  # Limit height for bottom dock

        # Progress items container
        self.progress_container = QWidget()
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(2)

        # No activity message
        self.no_activity_label = QLabel("No active generations")
        self.no_activity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_activity_label.setStyleSheet("color: #999; padding: 20px;")
        self.progress_layout.addWidget(self.no_activity_label)

        # Stretch to push items to top
        self.progress_layout.addStretch()

        self.scroll_area.setWidget(self.progress_container)
        layout.addWidget(self.scroll_area)

    def _setup_demo_timer(self):
        """Set up demo timer for testing (remove in production)."""
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self._demo_progress_update)
        self.demo_progress = {}

    def add_generation(self, item_id, description):
        """Add a new generation to the progress monitor."""
        if item_id in self._progress_items:
            return  # Already exists

        # Hide no activity message
        self.no_activity_label.hide()

        # Create progress item
        progress_item = ProgressItemWidget(item_id, description)
        progress_item.cancel_requested.connect(self._on_cancel_requested)

        # Add to layout
        self.progress_layout.insertWidget(
            self.progress_layout.count() - 1, progress_item  # Before stretch
        )

        # Store reference
        self._progress_items[item_id] = progress_item

        # Update container
        self._update_container()

    def update_generation_progress(
        self, item_id, progress, status="Processing..."
    ):
        """Update progress for a generation."""
        if item_id in self._progress_items:
            self._progress_items[item_id].update_progress(progress, status)

    def set_generation_error(self, item_id, error_message):
        """Set error state for a generation."""
        if item_id in self._progress_items:
            self._progress_items[item_id].set_error(error_message)

    def remove_generation(self, item_id):
        """Remove a generation from progress monitor."""
        if item_id in self._progress_items:
            progress_item = self._progress_items[item_id]
            self.progress_layout.removeWidget(progress_item)
            progress_item.deleteLater()
            del self._progress_items[item_id]

            self._update_container()

    def _update_container(self):
        """Update container state."""
        if not self._progress_items:
            self.no_activity_label.show()
        else:
            self.no_activity_label.hide()

    def _on_cancel_requested(self, item_id):
        """Handle generation cancellation request."""
        self.generation_cancelled.emit(item_id)
        # Remove from UI (the controller should handle actual cancellation)
        self.remove_generation(item_id)

    def _on_clear_completed(self):
        """Clear all completed generations."""
        completed_items = []
        for item_id, progress_item in self._progress_items.items():
            if progress_item.progress_bar.value() >= 100:
                completed_items.append(item_id)

        for item_id in completed_items:
            self.remove_generation(item_id)

        self.progress_cleared.emit()

    # Demo methods (remove in production)
    def start_demo_generation(self):
        """Start a demo generation for testing."""
        import random

        item_id = f"demo_{random.randint(1000, 9999)}"
        self.add_generation(item_id, "Generating image with SDXL")

        # Initialize demo progress
        self.demo_progress[item_id] = 0

        # Start timer if not running
        if not self.demo_timer.isActive():
            self.demo_timer.start(100)  # Update every 100ms

    def _demo_progress_update(self):
        """Update demo progress (remove in production)."""
        if not self.demo_progress:
            self.demo_timer.stop()
            return

        for item_id in list(self.demo_progress.keys()):
            progress = self.demo_progress[item_id]
            progress += 2  # Increment by 2%

            if progress >= 100:
                self.update_generation_progress(item_id, 100, "Completed")
                del self.demo_progress[item_id]
            else:
                self.update_generation_progress(
                    item_id, progress, f"Processing... {progress}%"
                )
                self.demo_progress[item_id] = progress

        if not self.demo_progress:
            self.demo_timer.stop()
