"""
Project controller for managing project lifecycle and operations.
"""

from PyQt6.QtCore import pyqtSlot
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .base_controller import BaseController
from signals.signal_bus import SignalBus


class ProjectController(BaseController):
    """Controller for managing project lifecycle and operations.

    Responsibilities:
    - Manage project CRUD operations (create, read, update, delete)
    - Handle active project state and switching
    - Load project-specific data and coordinate updates
    - Manage project overview display and statistics
    - Handle project-level operations (export, archive, settings)
    """

    def __init__(self, signal_bus: SignalBus):
        """Initialize the project controller."""
        super().__init__(signal_bus)
        self.logger = logging.getLogger(__name__)

        # Project state
        self.projects: List[Dict[str, Any]] = []
        self.current_project: Optional[Dict[str, Any]] = None

        # Services (lazy loaded to avoid circular imports)
        self._project_service = None

    def _connect_signals(self):
        """Connect project controller signals."""
        # Domain signals for project events
        self.signal_bus.domain.project_created.connect(self._on_project_created)
        self.signal_bus.domain.project_changed.connect(self._on_project_changed)
        self.signal_bus.domain.project_deleted.connect(self._on_project_deleted)

        # UI signals that might trigger project operations
        self.signal_bus.ui.view_changed.connect(self._on_view_changed)

    @property
    def project_service(self):
        """Lazy loading of ProjectService to avoid circular imports."""
        if self._project_service is None:
            from ..services.project_service import ProjectService

            self._project_service = ProjectService()
        return self._project_service

    def load_projects(self, force_refresh: bool = False):
        """Load all projects for display.

        Args:
            force_refresh: Whether to force refresh from database
        """
        try:
            self.start_loading("Loading projects")
            self.logger.info("Loading projects")

            # TODO: Load from ProjectService when implemented
            # For now, create mock data
            if force_refresh or not self.projects:
                self.projects = self._create_mock_projects()

            # Update projects overview widget
            self._update_projects_display(self.projects)

            self.finish_loading()
            self.logger.info(f"Loaded {len(self.projects)} projects")

        except Exception as e:
            self.handle_error(f"Failed to load projects: {str(e)}", "Projects")
            self.finish_loading()

    def _create_mock_projects(self) -> List[Dict[str, Any]]:
        """Create mock project data for testing.

        Returns:
            List of mock project dictionaries
        """
        # This is temporary mock data until ProjectService is implemented
        mock_projects = [
            {
                "id": "project-1",
                "name": "Fantasy Landscapes",
                "description": "A collection of fantasy landscape generations",
                "created_at": "2025-09-27T10:00:00Z",
                "updated_at": "2025-09-27T15:30:00Z",
                "status": "active",
                "stats": {
                    "total_products": 15,
                    "total_orders": 8,
                    "last_generation": "2025-09-27T15:30:00Z",
                },
                "settings": {
                    "default_model": "stable-diffusion-xl",
                    "default_provider": "replicate",
                },
                "featured_product_id": "product-3",
            },
            {
                "id": "project-2",
                "name": "Character Portraits",
                "description": "AI-generated character portraits and concept art",
                "created_at": "2025-09-26T14:00:00Z",
                "updated_at": "2025-09-27T12:15:00Z",
                "status": "active",
                "stats": {
                    "total_products": 23,
                    "total_orders": 12,
                    "last_generation": "2025-09-27T12:15:00Z",
                },
                "settings": {
                    "default_model": "midjourney-v6",
                    "default_provider": "replicate",
                },
                "featured_product_id": "product-8",
            },
            {
                "id": "project-3",
                "name": "Abstract Art",
                "description": "Experimental abstract art generations",
                "created_at": "2025-09-25T09:00:00Z",
                "updated_at": "2025-09-26T16:45:00Z",
                "status": "archived",
                "stats": {
                    "total_products": 7,
                    "total_orders": 4,
                    "last_generation": "2025-09-26T16:45:00Z",
                },
                "settings": {
                    "default_model": "dalle-3",
                    "default_provider": "openai",
                },
                "featured_product_id": None,
            },
        ]

        return mock_projects

    def _update_projects_display(self, projects: List[Dict[str, Any]]):
        """Update the projects overview widget with projects.

        Args:
            projects: List of projects to display
        """
        # TODO: Update projects overview widget when available
        # This will involve calling projects_overview.set_projects(projects)
        pass

    def create_project(
        self,
        name: str,
        description: str = "",
        settings: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Create a new project.

        Args:
            name: Name of the project
            description: Optional description
            settings: Optional project settings

        Returns:
            Project ID if successful, None if failed
        """
        try:
            self.start_loading("Creating project")
            self.logger.info(f"Creating project: {name}")

            # Validate inputs
            if not name or not name.strip():
                self.handle_error("Project name is required", "Projects")
                self.finish_loading()
                return None

            # Check for duplicate names
            if any(p["name"].lower() == name.lower() for p in self.projects):
                self.handle_error("A project with this name already exists", "Projects")
                self.finish_loading()
                return None

            # TODO: Create project using ProjectService
            # For now, create mock project
            project_id = f"project-{len(self.projects) + 1}"
            new_project = {
                "id": project_id,
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "stats": {
                    "total_products": 0,
                    "total_orders": 0,
                    "last_generation": None,
                },
                "settings": settings
                or {
                    "default_model": "stable-diffusion-xl",
                    "default_provider": "replicate",
                },
                "featured_product_id": None,
            }

            # Add to local cache
            self.projects.append(new_project)

            # Emit project created signal
            self.signal_bus.domain.project_created.emit(project_id)

            # Update display
            self._update_projects_display(self.projects)

            self.finish_loading()
            self.logger.info(f"Project created: {project_id}")
            return project_id

        except Exception as e:
            self.handle_error(f"Failed to create project: {str(e)}", "Projects")
            self.finish_loading()
            return None

    def switch_to_project(self, project_id: str):
        """Switch to a different project.

        Args:
            project_id: ID of the project to switch to
        """
        try:
            self.logger.info(f"Switching to project: {project_id}")

            # Find the project
            project = self._get_project_by_id(project_id)
            if not project:
                self.handle_error(f"Project not found: {project_id}", "Projects")
                return

            # Update current project
            self.current_project = project

            # Update main controller
            main_controller = self.parent()
            if hasattr(main_controller, "set_current_project"):
                main_controller.set_current_project(project_id)

            # Emit project changed signal
            self.signal_bus.domain.project_changed.emit(project_id)

            self.logger.info(f"Switched to project: {project['name']}")

        except Exception as e:
            self.handle_error(f"Failed to switch project: {str(e)}", "Projects")

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing project.

        Args:
            project_id: ID of the project to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Updating project: {project_id}")

            # Find the project
            project = self._get_project_by_id(project_id)
            if not project:
                self.handle_error(f"Project not found: {project_id}", "Projects")
                return False

            # TODO: Update project using ProjectService
            # For now, update local cache
            project.update(updates)
            project["updated_at"] = datetime.now().isoformat()

            # Update display
            self._update_projects_display(self.projects)

            self.logger.info(f"Project updated: {project_id}")
            return True

        except Exception as e:
            self.handle_error(f"Failed to update project: {str(e)}", "Projects")
            return False

    def delete_project(self, project_id: str) -> bool:
        """Delete a project.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting project: {project_id}")

            # Find the project
            project = self._get_project_by_id(project_id)
            if not project:
                self.handle_error(f"Project not found: {project_id}", "Projects")
                return False

            # TODO: Delete project using ProjectService
            # For now, remove from local cache
            self.projects = [p for p in self.projects if p["id"] != project_id]

            # If this was the current project, clear it
            if self.current_project and self.current_project["id"] == project_id:
                self.current_project = None
                main_controller = self.parent()
                if hasattr(main_controller, "set_current_project"):
                    main_controller.set_current_project(None)

            # Emit project deleted signal
            self.signal_bus.domain.project_deleted.emit(project_id)

            # Update display
            self._update_projects_display(self.projects)

            self.logger.info(f"Project deleted: {project_id}")
            return True

        except Exception as e:
            self.handle_error(f"Failed to delete project: {str(e)}", "Projects")
            return False

    def archive_project(self, project_id: str) -> bool:
        """Archive a project.

        Args:
            project_id: ID of the project to archive

        Returns:
            True if successful, False otherwise
        """
        return self.update_project(project_id, {"status": "archived"})

    def unarchive_project(self, project_id: str) -> bool:
        """Unarchive a project.

        Args:
            project_id: ID of the project to unarchive

        Returns:
            True if successful, False otherwise
        """
        return self.update_project(project_id, {"status": "active"})

    def export_project(self, project_id: str, export_path: str) -> bool:
        """Export a project and its data.

        Args:
            project_id: ID of the project to export
            export_path: Path to export to

        Returns:
            True if successful, False otherwise
        """
        try:
            self.start_loading(f"Exporting project")
            self.logger.info(f"Exporting project {project_id} to {export_path}")

            # Find the project
            project = self._get_project_by_id(project_id)
            if not project:
                self.handle_error(f"Project not found: {project_id}", "Projects")
                self.finish_loading()
                return False

            # TODO: Implement actual export logic
            # This would involve:
            # 1. Exporting project metadata
            # 2. Exporting all products and their files
            # 3. Creating a project archive
            self.logger.info(f"Would export project {project['name']} to {export_path}")

            self.finish_loading()
            return True

        except Exception as e:
            self.handle_error(f"Export failed: {str(e)}", "Projects")
            self.finish_loading()
            return False

    def get_project_statistics(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with project statistics, or None if project not found
        """
        project = self._get_project_by_id(project_id)
        if not project:
            return None

        # TODO: Calculate real statistics from database
        # For now, return mock statistics
        return {
            "total_products": project["stats"]["total_products"],
            "total_orders": project["stats"]["total_orders"],
            "total_size": 1024 * 1024 * 50,  # 50MB mock size
            "last_generation": project["stats"]["last_generation"],
            "creation_date": project["created_at"],
            "last_modified": project["updated_at"],
            "status": project["status"],
        }

    def _get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by its ID.

        Args:
            project_id: ID of the project to find

        Returns:
            Project data dictionary, or None if not found
        """
        for project in self.projects:
            if project["id"] == project_id:
                return project
        return None

    @pyqtSlot(str)
    def _on_project_created(self, project_id: str):
        """Handle project creation events.

        Args:
            project_id: ID of the created project
        """
        self.logger.debug(f"Project created event received: {project_id}")

    @pyqtSlot(str)
    def _on_project_changed(self, project_id: str):
        """Handle project change events.

        Args:
            project_id: ID of the new current project
        """
        self.logger.info(f"Project changed event received: {project_id}")

        # Update current project
        self.current_project = self._get_project_by_id(project_id)

    @pyqtSlot(str)
    def _on_project_deleted(self, project_id: str):
        """Handle project deletion events.

        Args:
            project_id: ID of the deleted project
        """
        self.logger.info(f"Project deleted event received: {project_id}")

    @pyqtSlot(str)
    def _on_view_changed(self, view_name: str):
        """Handle view change events.

        Args:
            view_name: Name of the new view
        """
        if view_name == "projects":
            # Refresh projects when projects view is shown
            self.load_projects()

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects.

        Returns:
            List of all project dictionaries
        """
        return self.projects.copy()

    def get_active_projects(self) -> List[Dict[str, Any]]:
        """Get only active (non-archived) projects.

        Returns:
            List of active project dictionaries
        """
        return [p for p in self.projects if p.get("status") == "active"]

    def cleanup(self):
        """Clean up project controller resources."""
        self.projects.clear()
        self.current_project = None
        self.logger.info("Project controller cleaned up")
