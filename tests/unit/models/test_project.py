"""
Tests for Project model.
"""

from app.models.project import Project


class TestProject:
    """Test Project model functionality."""

    def test_project_creation(self, session):
        """Test creating a project."""
        project = Project(name="My Project", description="A test project", status="active")
        session.add(project)
        session.commit()

        assert project.id is not None
        assert project.name == "My Project"
        assert project.description == "A test project"
        assert project.status == "active"
        assert project.product_count == 0
        assert project.order_count == 0

    def test_project_defaults(self, session):
        """Test project default values."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        assert project.status == "active"
        assert project.product_count == 0
        assert project.order_count == 0
        assert project.featured_product_ids is None
        assert project.settings is None

    def test_project_status_methods(self, session):
        """Test project status change methods."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        # Test archive
        project.archive()
        assert project.status == "archived"

        # Test complete
        project.complete()
        assert project.status == "completed"

        # Test activate
        project.activate()
        assert project.status == "active"

    def test_is_active_property(self, session):
        """Test is_active property."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        assert project.is_active

        project.archive()
        assert not project.is_active

        project.activate()
        assert project.is_active

    def test_json_fields(self, session):
        """Test JSON field functionality."""
        project = Project(name="Test Project")

        # Set featured products
        project.featured_product_ids = ["prod1", "prod2", "prod3"]

        # Set settings
        project.settings = {
            "theme": "dark",
            "auto_save": True,
            "notifications": {"email": True, "push": False},
        }

        session.add(project)
        session.commit()

        # Reload and verify
        session.expunge(project)
        reloaded = session.query(Project).filter_by(id=project.id).first()

        assert reloaded.featured_product_ids == ["prod1", "prod2", "prod3"]
        assert reloaded.settings["theme"] == "dark"
        assert reloaded.settings["auto_save"] is True
        assert reloaded.settings["notifications"]["email"] is True

    def test_project_repr(self, session):
        """Test project string representation."""
        project = Project(name="Test Project", status="active")
        session.add(project)
        session.commit()

        repr_str = repr(project)
        assert "Test Project" in repr_str
        assert "active" in repr_str
        assert project.id in repr_str

    def test_update_counts_method(self, session):
        """Test update_counts method (placeholder test)."""
        project = Project(name="Test Project")
        session.add(project)
        session.commit()

        # This is a placeholder test - full test requires Order and Product models
        project.update_counts(session)
        assert project.order_count == 0
        assert project.product_count == 0
