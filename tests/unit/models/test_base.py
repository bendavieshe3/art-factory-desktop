"""
Tests for base model functionality.
"""

import uuid
from datetime import datetime

from app.models.project import Project


class TestBaseModel:
    """Test BaseModel functionality."""

    def test_base_model_creation(self, session):
        """Test creating a model with base fields."""
        project = Project(name="Test Project", description="A test project")
        session.add(project)
        session.commit()

        # Check UUID generation
        assert project.id is not None
        assert len(project.id) == 36  # UUID string length
        assert uuid.UUID(project.id)  # Valid UUID

        # Check timestamps
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.deleted_at is None

        # Check automatic table naming
        assert project.__tablename__ == "projects"

    def test_soft_delete(self, session):
        """Test soft delete functionality."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        # Initially not deleted
        assert not project.is_deleted
        assert project.deleted_at is None

        # Soft delete
        project.soft_delete()
        session.commit()

        assert project.is_deleted
        assert project.deleted_at is not None
        assert isinstance(project.deleted_at, datetime)

    def test_restore_soft_delete(self, session):
        """Test restoring a soft-deleted record."""
        project = Project(name="Test Project")
        project.soft_delete()
        session.add(project)
        session.commit()

        assert project.is_deleted

        # Restore
        project.restore()
        session.commit()

        assert not project.is_deleted
        assert project.deleted_at is None

    def test_to_dict(self, session):
        """Test converting model to dictionary."""
        project = Project(
            name="Test Project", description="A test project", status="active"
        )
        session.add(project)
        session.commit()

        data = project.to_dict()

        assert data["name"] == "Test Project"
        assert data["description"] == "A test project"
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_from_dict(self, session):
        """Test creating model from dictionary."""
        data = {
            "name": "Dict Project",
            "description": "Created from dict",
            "status": "active",
        }

        project = Project.create_from_dict(data)
        session.add(project)
        session.commit()

        assert project.name == "Dict Project"
        assert project.description == "Created from dict"
        assert project.status == "active"

    def test_json_field_storage(self, session):
        """Test JSON field storage and retrieval."""
        project = Project(name="Test Project")

        # Set JSON data
        project.settings = {"theme": "dark", "auto_save": True}
        project.featured_product_ids = ["id1", "id2", "id3"]

        session.add(project)
        session.commit()

        # Reload from database
        project_id = project.id
        session.expunge(project)
        reloaded = session.query(Project).filter_by(id=project_id).first()

        assert reloaded.settings == {"theme": "dark", "auto_save": True}
        assert reloaded.featured_product_ids == ["id1", "id2", "id3"]

    def test_json_field_none_handling(self, session):
        """Test JSON field with None values."""
        project = Project(name="Test Project")
        project.settings = None
        project.featured_product_ids = None

        session.add(project)
        session.commit()

        # Reload from database
        project_id = project.id
        session.expunge(project)
        reloaded = session.query(Project).filter_by(id=project_id).first()

        assert reloaded.settings is None
        assert reloaded.featured_product_ids is None

    def test_updated_at_auto_update(self, session):
        """Test that updated_at is automatically updated."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        original_updated_at = project.updated_at

        # Wait a moment and update
        import time

        time.sleep(0.01)
        project.name = "Updated Project"
        session.commit()

        assert project.updated_at > original_updated_at
