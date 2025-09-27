"""
Tests for ProjectService.
"""

import pytest

from app.services.project_service import (
    ProjectService,
    ProjectServiceError,
    ProjectNotFoundError,
    ProjectValidationError,
)
from app.models import Project, Product, Order


class TestProjectService:
    """Test ProjectService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ProjectService()

    def test_create_project_success(self):
        """Test successful project creation."""
        project = self.service.create_project(
            name="Test Project", description="A test project", settings={"theme": "dark"}
        )

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.status == "active"
        assert project.settings == {"theme": "dark"}

    def test_create_project_minimal(self):
        """Test project creation with minimal data."""
        project = self.service.create_project(name="Minimal Project")

        assert project.id is not None
        assert project.name == "Minimal Project"
        assert project.description is None
        assert project.status == "active"

    def test_create_project_empty_name(self):
        """Test project creation with empty name."""
        with pytest.raises(ProjectValidationError, match="Project name is required"):
            self.service.create_project(name="")

        with pytest.raises(ProjectValidationError, match="Project name is required"):
            self.service.create_project(name="   ")

    def test_create_project_duplicate_name(self):
        """Test project creation with duplicate name."""
        # Create first project
        self.service.create_project(name="Duplicate Test")

        # Try to create second project with same name
        with pytest.raises(ProjectValidationError, match="already exists"):
            self.service.create_project(name="Duplicate Test")

        # Case-insensitive check
        with pytest.raises(ProjectValidationError, match="already exists"):
            self.service.create_project(name="duplicate test")

    def test_get_project_success(self, sample_project):
        """Test successful project retrieval."""
        project = self.service.get_project(sample_project.id)
        assert project is not None
        assert project.id == sample_project.id

    def test_get_project_not_found(self):
        """Test project retrieval with invalid ID."""
        project = self.service.get_project("invalid-id")
        assert project is None

    def test_get_all_projects(self):
        """Test getting all projects."""
        # Create test projects
        active_project = self.service.create_project(name="Active Project")
        archived_project = self.service.create_project(name="Archived Project")

        # Archive one project
        self.service.archive_project(archived_project.id)

        # Get all projects (excluding archived by default)
        projects = self.service.get_all_projects()
        project_ids = [p.id for p in projects]
        assert active_project.id in project_ids
        assert archived_project.id not in project_ids

        # Get all projects including archived
        all_projects = self.service.get_all_projects(include_archived=True)
        all_project_ids = [p.id for p in all_projects]
        assert active_project.id in all_project_ids
        assert archived_project.id in all_project_ids

    def test_get_all_projects_pagination(self):
        """Test project pagination."""
        # Create multiple projects
        projects = []
        for i in range(5):
            project = self.service.create_project(name=f"Project {i}")
            projects.append(project)

        # Test limit
        limited = self.service.get_all_projects(limit=3)
        assert len(limited) == 3

        # Test offset
        offset_projects = self.service.get_all_projects(limit=2, offset=2)
        assert len(offset_projects) == 2

    def test_get_active_projects(self):
        """Test getting only active projects."""
        active_project = self.service.create_project(name="Active Project")
        archived_project = self.service.create_project(name="Archived Project")

        # Archive one project
        self.service.archive_project(archived_project.id)

        # Get active projects
        active_projects = self.service.get_active_projects()
        active_ids = [p.id for p in active_projects]

        assert active_project.id in active_ids
        assert archived_project.id not in active_ids

    def test_update_project_success(self, sample_project):
        """Test successful project update."""
        updates = {
            "name": "Updated Name",
            "description": "Updated description",
            "status": "completed",
        }

        updated = self.service.update_project(sample_project.id, updates)
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.status == "completed"

    def test_update_project_not_found(self):
        """Test project update with invalid ID."""
        result = self.service.update_project("invalid-id", {"name": "New Name"})
        assert result is None

    def test_update_project_empty_name(self, sample_project):
        """Test project update with empty name."""
        with pytest.raises(ProjectValidationError, match="Project name is required"):
            self.service.update_project(sample_project.id, {"name": ""})

    def test_update_project_duplicate_name(self, sample_project):
        """Test project update with duplicate name."""
        # Create another project
        other_project = self.service.create_project(name="Other Project")

        # Try to update sample_project to use other_project's name
        with pytest.raises(ProjectValidationError, match="already exists"):
            self.service.update_project(sample_project.id, {"name": "Other Project"})

    def test_update_project_invalid_field(self, sample_project):
        """Test project update with invalid field."""
        with pytest.raises(ProjectValidationError, match="Invalid field"):
            self.service.update_project(sample_project.id, {"invalid_field": "value"})

    def test_delete_project_success(self, sample_project):
        """Test successful project deletion."""
        result = self.service.delete_project(sample_project.id)
        assert result is True

        # Verify project is soft deleted
        project = self.service.get_project(sample_project.id)
        assert project is None

    def test_delete_project_not_found(self):
        """Test project deletion with invalid ID."""
        result = self.service.delete_project("invalid-id")
        assert result is False

    def test_archive_project(self, sample_project):
        """Test project archiving."""
        result = self.service.archive_project(sample_project.id)
        assert result is not None
        assert result.status == "archived"

    def test_unarchive_project(self, sample_project):
        """Test project unarchiving."""
        # First archive the project
        self.service.archive_project(sample_project.id)

        # Then unarchive it
        result = self.service.unarchive_project(sample_project.id)
        assert result is not None
        assert result.status == "active"

    def test_get_project_statistics(self, sample_project):
        """Test project statistics calculation."""
        # The statistics will be mostly empty for the test project
        stats = self.service.get_project_statistics(sample_project.id)

        assert stats is not None
        assert stats["project_id"] == sample_project.id
        assert stats["name"] == sample_project.name
        assert stats["status"] == sample_project.status
        assert "created_at" in stats
        assert "product_count" in stats
        assert "order_count" in stats
        assert "total_file_size" in stats

    def test_get_project_statistics_not_found(self):
        """Test project statistics with invalid ID."""
        stats = self.service.get_project_statistics("invalid-id")
        assert stats is None

    def test_search_projects(self):
        """Test project search functionality."""
        # Create test projects
        project1 = self.service.create_project(
            name="Landscape Photography", description="Beautiful outdoor scenes"
        )
        project2 = self.service.create_project(
            name="Portrait Studies", description="Character portraits and concept art"
        )
        project3 = self.service.create_project(
            name="Abstract Art", description="Experimental compositions"
        )

        # Search by name
        results = self.service.search_projects("Landscape")
        assert len(results) == 1
        assert results[0].id == project1.id

        # Search by description
        results = self.service.search_projects("portraits")
        assert len(results) == 1
        assert results[0].id == project2.id

        # Search with multiple matches
        results = self.service.search_projects("art")
        result_ids = [p.id for p in results]
        assert project2.id in result_ids  # "concept art"
        assert project3.id in result_ids  # "Abstract Art"

        # Search with no matches
        results = self.service.search_projects("nonexistent")
        assert len(results) == 0

    def test_get_featured_products_empty(self, sample_project):
        """Test getting featured products when none are set."""
        products = self.service.get_featured_products(sample_project.id)
        assert products == []

    def test_set_featured_products_success(self, sample_project, sample_product):
        """Test setting featured products."""
        result = self.service.set_featured_products(sample_project.id, [sample_product.id])
        assert result is not None
        assert result.featured_product_ids == [sample_product.id]

        # Verify we can get them back
        featured = self.service.get_featured_products(sample_project.id)
        assert len(featured) == 1
        assert featured[0].id == sample_product.id

    def test_set_featured_products_invalid_product(self, sample_project):
        """Test setting featured products with invalid product ID."""
        with pytest.raises(ProjectValidationError, match="Invalid product ID"):
            self.service.set_featured_products(sample_project.id, ["invalid-id"])

    def test_set_featured_products_not_found(self):
        """Test setting featured products with invalid project ID."""
        result = self.service.set_featured_products("invalid-id", [])
        assert result is None

    def test_get_project_summary(self):
        """Test getting project summary statistics."""
        # Create test projects
        active_project = self.service.create_project(name="Active Project")
        archived_project = self.service.create_project(name="Archived Project")
        self.service.archive_project(archived_project.id)

        summary = self.service.get_project_summary()

        assert "total_projects" in summary
        assert "active_projects" in summary
        assert "archived_projects" in summary
        assert "total_products" in summary
        assert "total_orders" in summary

        # Should have at least our test projects
        assert summary["total_projects"] >= 2
        assert summary["active_projects"] >= 1
        assert summary["archived_projects"] >= 1
