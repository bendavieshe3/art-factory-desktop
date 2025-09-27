"""Main window for Art Factory application.

Provides the primary application interface with menu bar, dockable panels,
central area, and status bar. Integrates with the signal bus for
application-wide events.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStatusBar,
    QDockWidget,
    QStackedWidget,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction

from signals import signal_bus
from .widgets import (
    ParameterPanel,
    MetadataPanel,
    ProgressPanel,
    ProjectsOverview,
)


class MainWindow(QMainWindow):
    """Main application window with dockable panels and signal bus integration."""  # noqa: E501

    def __init__(self):
        super().__init__()
        self.signal_bus = signal_bus
        self.settings = QSettings("Art Factory", "Desktop")
        self._current_theme = "light"

        # Initialize components
        self._setup_window()
        self._create_dockable_panels()
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        self._connect_signals()
        self._restore_window_state()
        self._apply_theme()

    def _setup_window(self):
        """Configure basic window properties."""
        self.setWindowTitle("Art Factory")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)

    def _create_dockable_panels(self):
        """Create and configure dockable panels."""
        # Parameter panel (left dock)
        self.parameter_panel = ParameterPanel()
        self.parameter_dock = QDockWidget("Parameters", self)
        self.parameter_dock.setWidget(self.parameter_panel)
        self.parameter_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self.parameter_dock
        )

        # Metadata panel (right dock)
        self.metadata_panel = MetadataPanel()
        self.metadata_dock = QDockWidget("Product Details", self)
        self.metadata_dock.setWidget(self.metadata_panel)
        self.metadata_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.metadata_dock
        )

        # Progress panel (bottom dock)
        self.progress_panel = ProgressPanel()
        self.progress_dock = QDockWidget("Progress", self)
        self.progress_dock.setWidget(self.progress_panel)
        self.progress_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.progress_dock
        )

        # Set initial dock sizes
        self.resizeDocks(
            [self.parameter_dock, self.metadata_dock],
            [300, 300],
            Qt.Orientation.Horizontal,
        )
        self.resizeDocks([self.progress_dock], [150], Qt.Orientation.Vertical)

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

        # Panel toggles
        panels_menu = view_menu.addMenu("Panels")
        panels_menu.addAction(self.parameter_dock.toggleViewAction())
        panels_menu.addAction(self.metadata_dock.toggleViewAction())
        panels_menu.addAction(self.progress_dock.toggleViewAction())

        view_menu.addSeparator()

        # View switching
        self.projects_view_action = QAction("Projects View", self)
        self.projects_view_action.setShortcut("Ctrl+1")
        self.projects_view_action.setCheckable(True)
        self.projects_view_action.setChecked(True)
        self.projects_view_action.triggered.connect(
            lambda: self._switch_view("projects")
        )
        view_menu.addAction(self.projects_view_action)

        self.gallery_view_action = QAction("Gallery View", self)
        self.gallery_view_action.setShortcut("Ctrl+2")
        self.gallery_view_action.setCheckable(True)
        self.gallery_view_action.triggered.connect(
            lambda: self._switch_view("gallery")
        )
        view_menu.addAction(self.gallery_view_action)

        view_menu.addSeparator()

        # Theme toggle
        self.theme_action = QAction("Dark Theme", self)
        self.theme_action.setCheckable(True)
        self.theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.theme_action)

        view_menu.addSeparator()

        fullscreen_action = QAction("Enter Full Screen", self)
        fullscreen_action.setShortcut("Ctrl+Cmd+F")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Tools Menu
        tools_menu = menubar.addMenu("Tools")

        providers_action = QAction("Manage Providers...", self)
        providers_action.triggered.connect(self._on_manage_providers)
        tools_menu.addAction(providers_action)

        templates_action = QAction("Manage Templates...", self)
        templates_action.triggered.connect(self._on_manage_templates)
        tools_menu.addAction(templates_action)

        tools_menu.addSeparator()

        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self._on_settings)
        tools_menu.addAction(settings_action)

        # Help Menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About Art Factory", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_central_widget(self):
        """Create central widget with view switching."""
        # Create stacked widget for view switching
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # Projects overview (default view)
        self.projects_overview = ProjectsOverview()
        self.central_stack.addWidget(self.projects_overview)

        # Gallery view placeholder (to be implemented later)
        gallery_placeholder = QWidget()
        gallery_layout = QVBoxLayout(gallery_placeholder)
        gallery_label = QLabel("Gallery View")
        gallery_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gallery_label.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                color: #666;
                padding: 40px;
            }
        """
        )
        gallery_subtitle = QLabel("Coming Soon...")
        gallery_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gallery_subtitle.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                color: #999;
                padding: 10px;
            }
        """
        )
        gallery_layout.addWidget(gallery_label)
        gallery_layout.addWidget(gallery_subtitle)
        self.central_stack.addWidget(gallery_placeholder)

        # Set default view (projects)
        self.central_stack.setCurrentIndex(0)
        self._current_view = "projects"

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

    def _connect_signals(self):
        """Connect to signal bus for application-wide events."""
        # Connect UI signals for status updates
        self.signal_bus.ui.loading_started.connect(self._on_loading_started)
        self.signal_bus.ui.loading_finished.connect(self._on_loading_finished)
        self.signal_bus.ui.error_occurred.connect(self._on_error_occurred)

        # Connect domain signals for business events
        self.signal_bus.domain.order_created.connect(self._on_order_created)
        self.signal_bus.domain.product_created.connect(
            self._on_product_created
        )

        # Connect panel signals
        self.parameter_panel.generation_requested.connect(
            self._on_generation_requested
        )
        self.parameter_panel.template_saved.connect(self._on_template_saved)
        self.parameter_panel.template_loaded.connect(self._on_template_loaded)

        self.metadata_panel.product_liked.connect(self._on_product_liked)
        self.metadata_panel.product_rated.connect(self._on_product_rated)
        self.metadata_panel.product_exported.connect(self._on_product_exported)
        self.metadata_panel.product_deleted.connect(self._on_product_deleted)
        self.metadata_panel.regenerate_requested.connect(
            self._on_regenerate_requested
        )

        self.progress_panel.generation_cancelled.connect(
            self._on_generation_cancelled
        )
        self.progress_panel.progress_cleared.connect(self._on_progress_cleared)

        self.projects_overview.project_selected.connect(
            self._on_project_selected
        )
        self.projects_overview.project_create_requested.connect(
            self._on_project_create_requested
        )
        self.projects_overview.project_edit_requested.connect(
            self._on_project_edit_requested
        )
        self.projects_overview.view_switch_requested.connect(self._switch_view)

        # Emit initial view changed signal
        self.signal_bus.ui.view_changed.emit("projects")

    def _on_loading_started(self, task_name: str):
        """Handle loading started signal."""
        self.statusBar().showMessage(f"Loading: {task_name}")

    def _on_loading_finished(self):
        """Handle loading finished signal."""
        self.statusBar().showMessage("Ready", 2000)

    def _on_error_occurred(self, error_message: str):
        """Handle error signal."""
        from PyQt6.QtWidgets import QMessageBox

        self.statusBar().showMessage(f"Error: {error_message}", 5000)
        QMessageBox.warning(self, "Error", error_message)

    def _on_order_created(self, order_id: str):
        """Handle order created signal."""
        self.statusBar().showMessage(f"Order created: {order_id}", 3000)

    def _on_product_created(self, product_id: str):
        """Handle product created signal."""
        self.statusBar().showMessage(f"Product created: {product_id}", 3000)

    def _switch_view(self, view_name):
        """Switch between different central views."""
        if view_name == "projects":
            self.central_stack.setCurrentIndex(0)
            self.projects_view_action.setChecked(True)
            self.gallery_view_action.setChecked(False)
        elif view_name == "gallery":
            self.central_stack.setCurrentIndex(1)
            self.projects_view_action.setChecked(False)
            self.gallery_view_action.setChecked(True)

        self._current_view = view_name
        self.signal_bus.ui.view_changed.emit(view_name)
        self.statusBar().showMessage(f"Switched to {view_name} view", 2000)

    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        if self._current_theme == "light":
            self._current_theme = "dark"
            self.theme_action.setText("Light Theme")
            self.theme_action.setChecked(True)
        else:
            self._current_theme = "light"
            self.theme_action.setText("Dark Theme")
            self.theme_action.setChecked(False)

        self._apply_theme()
        self.settings.setValue("theme", self._current_theme)
        self.statusBar().showMessage(
            f"Switched to {self._current_theme} theme", 2000
        )

    def _apply_theme(self):
        """Apply the current theme to the application."""
        if self._current_theme == "dark":
            # Dark theme stylesheet
            dark_style = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QDockWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(undock.png);
            }
            QDockWidget::title {
                text-align: left;
                background-color: #3c3c3c;
                padding-left: 5px;
                padding-top: 3px;
                padding-bottom: 3px;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 3px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow_white.png);
                width: 10px;
                height: 10px;
            }
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #404040;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #404040;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 2px;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #555555;
                border-radius: 2px;
                background-color: #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #007AFF;
            }
            /* Project Card Dark Theme Styling */
            QFrame#ProjectCard {
                background-color: #404040 !important;
                border: 1px solid #555555 !important;
                border-radius: 8px;
                color: #ffffff !important;
            }
            QFrame#ProjectCard:hover {
                border-color: #007AFF !important;
                background-color: #4a4a4a !important;
            }
            QFrame#ProjectCard QLabel {
                color: #ffffff !important;
                background-color: transparent !important;
            }
            QFrame#ProjectCard QFrame {
                background-color: #353535 !important;
                border: 1px solid #505050 !important;
                color: #cccccc !important;
            }
            """
            self.setStyleSheet(dark_style)
        else:
            # Light theme (default)
            self.setStyleSheet("")

    def _restore_window_state(self):
        """Restore window state from settings."""
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore window state (docks, toolbars)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

        # Restore theme
        saved_theme = self.settings.value("theme", "light")
        self._current_theme = saved_theme
        if self._current_theme == "dark":
            self.theme_action.setText("Light Theme")
            self.theme_action.setChecked(True)

        # Restore current view
        saved_view = self.settings.value("current_view", "projects")
        if saved_view in ["projects", "gallery"]:
            self._switch_view(saved_view)

    def _save_window_state(self):
        """Save window state to settings."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("theme", self._current_theme)
        self.settings.setValue("current_view", self._current_view)

    def closeEvent(self, event):
        """Handle application close event."""
        self._save_window_state()
        super().closeEvent(event)

    def _on_manage_providers(self):
        """Handle manage providers action."""
        self.statusBar().showMessage(
            "Manage Providers - Not implemented yet", 2000
        )

    def _on_manage_templates(self):
        """Handle manage templates action."""
        self.statusBar().showMessage(
            "Manage Templates - Not implemented yet", 2000
        )

    def _on_settings(self):
        """Handle settings action."""
        self.statusBar().showMessage("Settings - Not implemented yet", 2000)

    # Panel signal handlers
    def _on_generation_requested(self, parameters: dict):
        """Handle generation request from parameter panel."""
        self.statusBar().showMessage("Starting generation...", 2000)
        # TODO: Forward to generation controller
        self.signal_bus.domain.order_created.emit(
            f"order_{parameters.get('prompt', 'unknown')[:10]}"
        )

    def _on_template_saved(self, template_name: str, parameters: dict):
        """Handle template save request."""
        self.statusBar().showMessage(f"Template '{template_name}' saved", 2000)

    def _on_template_loaded(self, template_name: str):
        """Handle template load request."""
        self.statusBar().showMessage(
            f"Template '{template_name}' loaded", 2000
        )

    def _on_product_liked(self, product_id: str, liked: bool):
        """Handle product like toggle."""
        action = "liked" if liked else "unliked"
        self.statusBar().showMessage(f"Product {action}", 1000)

    def _on_product_rated(self, product_id: str, rating: int):
        """Handle product rating."""
        self.statusBar().showMessage(f"Product rated {rating} stars", 1000)

    def _on_product_exported(self, product_id: str):
        """Handle product export request."""
        self.statusBar().showMessage("Export - Not implemented yet", 2000)

    def _on_product_deleted(self, product_id: str):
        """Handle product deletion."""
        self.statusBar().showMessage(f"Product deleted: {product_id}", 2000)

    def _on_regenerate_requested(self, product_id: str):
        """Handle regeneration request."""
        self.statusBar().showMessage(
            f"Regenerating product: {product_id}", 2000
        )

    def _on_generation_cancelled(self, item_id: str):
        """Handle generation cancellation."""
        self.statusBar().showMessage(f"Generation cancelled: {item_id}", 2000)

    def _on_progress_cleared(self):
        """Handle progress panel clear."""
        self.statusBar().showMessage("Progress cleared", 1000)

    def _on_project_selected(self, project_id: str):
        """Handle project selection."""
        self.statusBar().showMessage(f"Selected project: {project_id}", 2000)

    def _on_project_create_requested(self):
        """Handle new project creation request."""
        self.statusBar().showMessage(
            "Create Project - Not implemented yet", 2000
        )

    def _on_project_edit_requested(self, project_id: str):
        """Handle project edit request."""
        self.statusBar().showMessage(
            f"Edit project: {project_id} - Not implemented yet", 2000
        )
