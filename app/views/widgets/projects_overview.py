"""
Projects overview widget for the central area.

Displays project cards in a grid layout as the default view.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QFrame,
    QLineEdit,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal


class ProjectCard(QFrame):
    """Widget representing a single project in the overview."""

    clicked = pyqtSignal(str)  # project_id
    context_menu_requested = pyqtSignal(str, object)  # project_id, position

    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.project_id = project_data.get("id", "")
        self._setup_ui()

    def _setup_ui(self):
        """Set up the project card UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        # Set object name for CSS targeting
        self.setObjectName("ProjectCard")
        # Basic styling - theme styling will be applied by main window
        self.setStyleSheet(
            """
            QFrame#ProjectCard {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame#ProjectCard:hover {
                border-color: #007AFF;
                background-color: #F8F9FA;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Project name
        name_label = QLabel(self.project_data.get("name", "Untitled Project"))
        name_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #333;"
        )
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # Description
        description = self.project_data.get("description", "")
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #666; font-size: 12px;")
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(40)  # Limit height
            layout.addWidget(desc_label)

        # Thumbnail area (placeholder)
        thumbnail_frame = QFrame()
        thumbnail_frame.setFixedHeight(80)
        thumbnail_frame.setStyleSheet(
            """
            QFrame {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
        """
        )
        thumbnail_layout = QVBoxLayout(thumbnail_frame)
        thumbnail_label = QLabel("Featured Images")
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setStyleSheet("color: #999; font-size: 11px;")
        thumbnail_layout.addWidget(thumbnail_label)
        layout.addWidget(thumbnail_frame)

        # Statistics
        stats_layout = QHBoxLayout()

        # Order count
        order_count = self.project_data.get("order_count", 0)
        order_label = QLabel(f"{order_count} orders")
        order_label.setStyleSheet("color: #666; font-size: 11px;")
        stats_layout.addWidget(order_label)

        stats_layout.addStretch()

        # Product count
        product_count = self.project_data.get("product_count", 0)
        product_label = QLabel(f"{product_count} products")
        product_label.setStyleSheet("color: #666; font-size: 11px;")
        stats_layout.addWidget(product_label)

        layout.addLayout(stats_layout)

        # Status indicator
        status = self.project_data.get("status", "active")
        status_layout = QHBoxLayout()

        status_indicator = QLabel("●")
        if status == "active":
            status_indicator.setStyleSheet("color: #34C759;")
        elif status == "archived":
            status_indicator.setStyleSheet("color: #8E8E93;")
        else:
            status_indicator.setStyleSheet("color: #FF9500;")

        status_label = QLabel(status.title())
        status_label.setStyleSheet("color: #666; font-size: 11px;")

        status_layout.addWidget(status_indicator)
        status_layout.addWidget(status_label)
        status_layout.addStretch()

        # Last activity
        created_at = self.project_data.get("created_at", "")
        if created_at:
            time_label = QLabel(
                str(created_at).split("T")[0]
            )  # Just date part
            time_label.setStyleSheet("color: #999; font-size: 10px;")
            status_layout.addWidget(time_label)

        layout.addLayout(status_layout)

        # Set fixed size for consistent grid
        self.setFixedSize(220, 180)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project_id)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(
                self.project_id, event.globalPosition()
            )
        super().mousePressEvent(event)


class ProjectsOverview(QWidget):
    """
    Central widget showing projects overview.

    Displays project cards in a grid layout with search and filtering.
    """

    # Signals
    project_selected = pyqtSignal(str)  # project_id
    project_create_requested = pyqtSignal()
    project_edit_requested = pyqtSignal(str)  # project_id
    view_switch_requested = pyqtSignal(str)  # view_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects = []
        self._filtered_projects = []
        self._setup_ui()
        self._connect_signals()
        self._load_demo_projects()  # For demonstration

    def _setup_ui(self):
        """Set up the projects overview UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        # Title
        title_label = QLabel("Projects")
        title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #333;"
        )
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # View switcher
        self.gallery_button = QPushButton("Gallery View")
        self.gallery_button.setStyleSheet(
            """
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """
        )
        header_layout.addWidget(self.gallery_button)

        # Create project button
        self.create_button = QPushButton("+ New Project")
        self.create_button.setStyleSheet(
            """
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30B74D;
            }
        """
        )
        header_layout.addWidget(self.create_button)

        layout.addLayout(header_layout)

        # Search and filter bar
        filter_layout = QHBoxLayout()

        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search projects...")
        self.search_edit.setMaximumWidth(300)
        filter_layout.addWidget(self.search_edit)

        # Status filter
        self.status_combo = QComboBox()
        self.status_combo.addItems(
            ["All Status", "Active", "Archived", "Completed"]
        )
        self.status_combo.setMaximumWidth(120)
        filter_layout.addWidget(self.status_combo)

        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Projects grid scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Projects container
        self.projects_container = QWidget()
        self.projects_layout = QGridLayout(self.projects_container)
        self.projects_layout.setSpacing(16)
        self.projects_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        # No projects message
        self.no_projects_label = QLabel("No projects found")
        self.no_projects_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_projects_label.setStyleSheet(
            """
            QLabel {
                color: #999;
                font-size: 18px;
                padding: 60px;
            }
        """
        )
        self.projects_layout.addWidget(self.no_projects_label, 0, 0)

        scroll_area.setWidget(self.projects_container)
        layout.addWidget(scroll_area)

    def _connect_signals(self):
        """Connect internal signals."""
        self.create_button.clicked.connect(self.project_create_requested.emit)
        self.gallery_button.clicked.connect(
            lambda: self.view_switch_requested.emit("gallery")
        )
        self.search_edit.textChanged.connect(self._filter_projects)
        self.status_combo.currentTextChanged.connect(self._filter_projects)

    def resizeEvent(self, event):
        """Handle resize events to update grid layout."""
        super().resizeEvent(event)
        # Delay the update to avoid excessive recalculations
        if hasattr(self, "_resize_timer"):
            self._resize_timer.stop()
        else:
            from PyQt6.QtCore import QTimer

            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._update_projects_display)
        self._resize_timer.start(100)  # 100ms delay

    def set_projects(self, projects):
        """Set the list of projects to display."""
        self._projects = projects
        self._filter_projects()

    def _filter_projects(self):
        """Filter projects based on search and status."""
        search_text = self.search_edit.text().lower()
        status_filter = self.status_combo.currentText()

        filtered = []
        for project in self._projects:
            # Status filter
            if status_filter != "All Status":
                project_status = project.get("status", "active").title()
                if project_status != status_filter:
                    continue

            # Search filter
            if search_text:
                name = project.get("name", "").lower()
                description = project.get("description", "").lower()
                if search_text not in name and search_text not in description:
                    continue

            filtered.append(project)

        self._filtered_projects = filtered
        self._update_projects_display()

    def _update_projects_display(self):
        """Update the projects grid display."""
        # Clear existing cards
        for i in reversed(range(self.projects_layout.count())):
            child = self.projects_layout.itemAt(i).widget()
            if child and not isinstance(
                child, QLabel
            ):  # Keep the no projects label
                self.projects_layout.removeWidget(child)
                child.deleteLater()

        if not self._filtered_projects:
            self.no_projects_label.show()
            return

        self.no_projects_label.hide()

        # Add project cards with responsive columns
        container_width = self.projects_container.width()
        card_width = 220  # Fixed card width
        card_margin = 16  # Spacing between cards
        available_width = max(container_width - 32, 240)  # Account for margins
        columns = max(1, available_width // (card_width + card_margin))

        for i, project in enumerate(self._filtered_projects):
            row = i // columns
            col = i % columns

            card = ProjectCard(project)
            card.clicked.connect(self._on_project_clicked)
            card.context_menu_requested.connect(self._on_project_context_menu)

            self.projects_layout.addWidget(card, row, col)

    def _on_project_clicked(self, project_id):
        """Handle project card click."""
        self.project_selected.emit(project_id)

    def _on_project_context_menu(self, project_id, position):
        """Handle project context menu request."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction

        menu = QMenu(self)

        # View action
        view_action = QAction("View Details", self)
        view_action.triggered.connect(
            lambda: self.project_selected.emit(project_id)
        )
        menu.addAction(view_action)

        # Edit action
        edit_action = QAction("Edit Project", self)
        edit_action.triggered.connect(
            lambda: self.project_edit_requested.emit(project_id)
        )
        menu.addAction(edit_action)

        menu.addSeparator()

        # Archive/Activate action
        archive_action = QAction("Archive Project", self)
        menu.addAction(archive_action)

        menu.exec(position.toPoint())

    def _load_demo_projects(self):
        """Load demo projects for testing (remove in production)."""
        demo_projects = [
            {
                "id": "proj_1",
                "name": "Character Portraits",
                "description": "Fantasy character portraits using SDXL",
                "status": "active",
                "order_count": 5,
                "product_count": 23,
                "created_at": "2024-01-15T10:30:00",
            },
            {
                "id": "proj_2",
                "name": "Landscape Photography",
                "description": "AI-generated landscape scenes",
                "status": "active",
                "order_count": 8,
                "product_count": 45,
                "created_at": "2024-01-10T14:20:00",
            },
            {
                "id": "proj_3",
                "name": "Product Mockups",
                "description": "Marketing materials and product shots",
                "status": "completed",
                "order_count": 3,
                "product_count": 12,
                "created_at": "2024-01-05T09:15:00",
            },
            {
                "id": "proj_4",
                "name": "Abstract Art",
                "description": "Experimental abstract compositions",
                "status": "archived",
                "order_count": 12,
                "product_count": 67,
                "created_at": "2023-12-20T16:45:00",
            },
        ]
        self.set_projects(demo_projects)
