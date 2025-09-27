"""
Tests for OrderService.

Tests both Phase 1 (basic order management) and Phase 2 (parameter expansion).
"""

import pytest

from app.services.order_service import (
    OrderService,
    ExpansionError,
)
from app.models import Order, Project
from app.models.database import init_database, TEST_DATABASE_URL


class TestOrderServiceBasic:
    """Test basic OrderService functionality (Phase 1)."""

    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        db_manager = init_database(TEST_DATABASE_URL, echo=False)
        with db_manager.session_scope() as session:
            yield session

    @pytest.fixture
    def order_service(self):
        """Create OrderService instance."""
        return OrderService(max_items=10)  # Lower limit for testing

    @pytest.fixture
    def sample_project(self, db_session):
        """Create a sample project."""
        project = Project(name="Test Project", description="Test project for order service tests")
        db_session.add(project)
        db_session.commit()
        return project

    @pytest.fixture
    def basic_order(self, db_session, sample_project):
        """Create a basic order for testing."""
        order = Order(
            project_id=sample_project.id,
            provider="replicate",
            model="stability-ai/sdxl",
            model_family="stable-diffusion",
            model_modality="text-to-image",
            base_parameter_set={
                "prompt": "A red dog",
                "steps": 20,
                "guidance_scale": 7.5,
            },
        )
        db_session.add(order)
        db_session.commit()
        return order

    def test_create_basic_order_items(self, order_service, basic_order, db_session):
        """Test creating OrderItems from basic Order (1:1 mapping)."""
        order_items = order_service.create_order_items(basic_order, db_session)

        assert len(order_items) == 1
        assert order_items[0].order_id == basic_order.id
        assert order_items[0].sequence_number == 1
        assert order_items[0].status == "pending"
        assert order_items[0].generation_parameter_set == basic_order.base_parameter_set

        # Check order was updated
        assert basic_order.expanded_count == 1
        assert basic_order.status == "processing"

    def test_parameter_validation_success(self, order_service):
        """Test successful parameter validation."""
        params = {
            "prompt": "A beautiful landscape",
            "steps": 20,
            "guidance_scale": 7.5,
            "negative_prompt": "blurry",
        }

        result = order_service.validate_base_parameters(params)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_parameter_validation_missing_required(self, order_service):
        """Test validation failure for missing required fields."""
        params = {"steps": 20, "guidance_scale": 7.5}

        result = order_service.validate_base_parameters(params)

        assert not result.is_valid
        assert "Required field 'prompt' is missing or empty" in result.errors

    def test_parameter_validation_wrong_types(self, order_service):
        """Test validation failure for wrong parameter types."""
        params = {
            "prompt": 123,  # Should be string
            "steps": "not_a_number",  # Should be number or valid range
            "guidance_scale": [],  # Should be number or valid range
        }

        result = order_service.validate_base_parameters(params)

        assert not result.is_valid
        assert "'prompt' must be a string" in result.errors
        assert "'steps' has invalid range syntax: not_a_number" in result.errors
        assert "'guidance_scale' must be a number or valid range string" in result.errors

    def test_parameter_validation_negative_values(self, order_service):
        """Test validation failure for negative values."""
        params = {"prompt": "A dog", "steps": -5}

        result = order_service.validate_base_parameters(params)

        assert not result.is_valid
        assert "'steps' must be positive" in result.errors

    def test_update_order_status(self, order_service, basic_order, db_session):
        """Test order status update based on OrderItem statuses."""
        # Create some order items
        order_items = order_service.create_order_items(basic_order, db_session)

        # Simulate completion
        order_items[0].status = "complete"
        db_session.commit()

        # Update order status
        order_service.update_order_status(basic_order.id, db_session)

        assert basic_order.status == "fulfilled"
        assert basic_order.completed_count == 1
        assert basic_order.failed_count == 0


class TestOrderServiceExpansion:
    """Test parameter expansion functionality (Phase 2)."""

    @pytest.fixture
    def order_service(self):
        """Create OrderService instance."""
        return OrderService(max_items=50)

    def test_token_expansion_simple(self, order_service):
        """Test simple token expansion."""
        params = {"prompt": "[red,blue,green] dog"}

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 3
        assert expanded[0]["prompt"] == "red dog"
        assert expanded[1]["prompt"] == "blue dog"
        assert expanded[2]["prompt"] == "green dog"

    def test_range_expansion_integers(self, order_service):
        """Test range expansion with integers."""
        params = {"steps": "18..20"}

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 3
        assert expanded[0]["steps"] == 18
        assert expanded[1]["steps"] == 19
        assert expanded[2]["steps"] == 20

    def test_range_expansion_floats(self, order_service):
        """Test range expansion with floats."""
        params = {"guidance_scale": "7.0..9.0"}

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 3
        assert expanded[0]["guidance_scale"] == 7.0
        assert expanded[1]["guidance_scale"] == 8.0
        assert expanded[2]["guidance_scale"] == 9.0

    def test_subprompt_expansion(self, order_service):
        """Test sub-prompt expansion."""
        params = {"prompt": "A dog || A cat"}

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 2
        assert expanded[0]["prompt"] == "A dog"
        assert expanded[1]["prompt"] == "A cat"

    def test_combined_expansion(self, order_service):
        """Test combination of token, range, and sub-prompt expansion."""
        params = {"prompt": "[red,blue] dog || cat", "steps": "19..20"}

        expanded = order_service.expand_parameters(params)

        # Should be: (2 token colors + 1 unchanged subprompt) × 2 steps = 6 combinations
        assert len(expanded) == 6

        # Check some specific combinations
        prompts = [p["prompt"] for p in expanded]
        steps = [p["steps"] for p in expanded]

        assert "red dog" in prompts
        assert "blue dog" in prompts
        assert "cat" in prompts
        assert 19 in steps
        assert 20 in steps

    def test_expansion_preview(self, order_service):
        """Test expansion preview functionality."""
        params = {"prompt": "[red,blue] dog || cat", "steps": "19..20"}

        preview = order_service.preview_expansion(params)

        assert preview.total_items == 6
        assert preview.has_tokens
        assert preview.has_ranges
        assert preview.has_subprompts

    def test_expansion_limits(self, order_service):
        """Test expansion limits are enforced."""
        # Create parameters that would expand beyond limit
        params = {"prompt": "[" + ",".join([f"color{i}" for i in range(100)]) + "] dog"}

        with pytest.raises(ExpansionError) as exc_info:
            order_service.expand_parameters(params)

        assert "more than 50 OrderItems" in str(exc_info.value)

    def test_invalid_token_syntax(self, order_service):
        """Test invalid token expansion syntax."""
        params = {"prompt": "[red] dog"}  # Single value, should have at least 2

        result = order_service.validate_base_parameters(params)

        assert not result.is_valid
        assert "invalid token expansion syntax" in result.errors[0]

    def test_invalid_range_syntax(self, order_service):
        """Test invalid range expansion syntax."""
        params = {"steps": "20..10"}  # Start > end

        with pytest.raises(ExpansionError):
            order_service.expand_parameters(params)

    def test_empty_token_expansion(self, order_service):
        """Test empty token expansion."""
        params = {"prompt": "[] dog"}

        with pytest.raises(ExpansionError) as exc_info:
            order_service.expand_parameters(params)

        assert "Empty token expansion" in str(exc_info.value)

    def test_complex_token_patterns(self, order_service):
        """Test complex token patterns in strings."""
        params = {"prompt": "A [red,blue] dog with [big,small] ears"}

        # Currently only handles first token group
        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 2
        assert "red" in expanded[0]["prompt"]
        assert "blue" in expanded[1]["prompt"]

    def test_no_expansion_needed(self, order_service):
        """Test parameters that don't need expansion."""
        params = {"prompt": "A simple dog", "steps": 20, "guidance_scale": 7.5}

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 1
        assert expanded[0] == params


class TestOrderServiceEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def order_service(self):
        """Create OrderService instance."""
        return OrderService()

    def test_empty_parameters(self, order_service):
        """Test handling of empty parameters."""
        params = {}

        result = order_service.validate_base_parameters(params)

        assert not result.is_valid
        assert "Required field 'prompt' is missing or empty" in result.errors

    def test_whitespace_handling(self, order_service):
        """Test proper whitespace handling in expansions."""
        params = {"prompt": "[ red , blue , green ] dog"}

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 3
        assert expanded[0]["prompt"] == "red dog"  # Whitespace should be stripped
        assert expanded[1]["prompt"] == "blue dog"
        assert expanded[2]["prompt"] == "green dog"

    def test_subprompt_empty_parts(self, order_service):
        """Test sub-prompt handling with empty parts."""
        params = {"prompt": "A dog || || A cat"}

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 2  # Empty prompt should be filtered out
        assert expanded[0]["prompt"] == "A dog"
        assert expanded[1]["prompt"] == "A cat"

    def test_range_single_value(self, order_service):
        """Test range with same start and end."""
        params = {"steps": "20..20"}

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 1
        assert expanded[0]["steps"] == 20

    def test_non_string_values_ignored(self, order_service):
        """Test that non-string values are not expanded."""
        params = {
            "prompt": "A dog",
            "steps": 20,  # Integer, should not be expanded
            "options": {"nested": "dict"},  # Dict, should not be expanded
            "tags": ["tag1", "tag2"],  # List, should not be expanded
        }

        expanded = order_service.expand_parameters(params)

        assert len(expanded) == 1
        assert expanded[0] == params
