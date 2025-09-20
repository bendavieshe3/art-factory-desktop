"""Main window for Art Factory application.

Provides the primary application interface with menu bar, central area,
and status bar.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStatusBar,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()

    def _setup_window(self):
        """Configure basic window properties."""
        self.setWindowTitle("Art Factory")
        self.setGeometry(100, 100, 1200, 800)

    def _create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")

        new_project_action = QAction("New Project...", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_project_action)

        file_menu.addSeparator()

        preferences_action = QAction("Preferences...", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self._on_preferences)
        file_menu.addAction(preferences_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setEnabled(False)  # Placeholder
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Shift+Z")
        redo_action.setEnabled(False)  # Placeholder
        edit_menu.addAction(redo_action)

        # View Menu
        view_menu = menubar.addMenu("View")

        fullscreen_action = QAction("Enter Full Screen", self)
        fullscreen_action.setShortcut("Ctrl+Cmd+F")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Help Menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About Art Factory", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_central_widget(self):
        """Create central widget placeholder."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Placeholder content
        placeholder_label = QLabel("Art Factory")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                color: #666;
                padding: 40px;
            }
        """
        )

        subtitle_label = QLabel("AI Media Generation Management")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                color: #999;
                padding: 10px;
            }
        """
        )

        layout.addWidget(placeholder_label)
        layout.addWidget(subtitle_label)

    def _create_status_bar(self):
        """Create status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready")

    # Menu action handlers (placeholders)
    def _on_new_project(self):
        """Handle new project action."""
        self.statusBar().showMessage("New Project - Not implemented yet", 2000)

    def _on_preferences(self):
        """Handle preferences action."""
        self.statusBar().showMessage("Preferences - Not implemented yet", 2000)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_about(self):
        """Handle about action."""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About Art Factory",
            "Art Factory v0.1.0-dev\\n\\n"
            "AI Media Generation Management\\n\\n"
            "Built with PyQt6",
        )
