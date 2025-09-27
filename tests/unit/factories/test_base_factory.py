"""
Tests for BaseProductFactory and related classes.
"""

import pytest

from app.factories.base import (
    ParameterSpec,
    ParameterType,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)
from .mock_factory import MockFactory, MockFailingFactory


class TestParameterSpec:
    """Test ParameterSpec validation."""

    def test_string_parameter_validation(self):
        """Test string parameter validation."""
        spec = ParameterSpec(name="prompt", type=ParameterType.STRING, required=True)

        # Valid string
        result = spec.validate_value("test prompt")
        assert result.is_valid
        assert len(result.errors) == 0

        # Missing required parameter
        result = spec.validate_value(None)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "required" in result.errors[0].message

        # Wrong type
        result = spec.validate_value(123)
        assert not result.is_valid
        assert "must be of type string" in result.errors[0].message

    def test_integer_parameter_validation(self):
        """Test integer parameter validation."""
        spec = ParameterSpec(
            name="steps",
            type=ParameterType.INTEGER,
            required=False,
            min_value=1,
            max_value=100,
            default=20,
        )

        # Valid integer
        result = spec.validate_value(50)
        assert result.is_valid

        # Valid with None (not required)
        result = spec.validate_value(None)
        assert result.is_valid

        # Below minimum
        result = spec.validate_value(0)
        assert not result.is_valid
        assert "must be >=" in result.errors[0].message

        # Above maximum
        result = spec.validate_value(150)
        assert not result.is_valid
        assert "must be <=" in result.errors[0].message

        # Wrong type (boolean should not be accepted as integer)
        result = spec.validate_value(True)
        assert not result.is_valid

    def test_float_parameter_validation(self):
        """Test float parameter validation."""
        spec = ParameterSpec(
            name="guidance", type=ParameterType.FLOAT, min_value=1.0, max_value=20.0
        )

        # Valid float
        result = spec.validate_value(7.5)
        assert result.is_valid

        # Valid integer (should be accepted for float)
        result = spec.validate_value(10)
        assert result.is_valid

        # Out of range
        result = spec.validate_value(25.0)
        assert not result.is_valid

    def test_choice_parameter_validation(self):
        """Test parameter validation with choices."""
        spec = ParameterSpec(
            name="scheduler",
            type=ParameterType.STRING,
            choices=["DDIM", "PNDM", "DPMSolverMultistep"],
        )

        # Valid choice
        result = spec.validate_value("DDIM")
        assert result.is_valid

        # Invalid choice
        result = spec.validate_value("InvalidScheduler")
        assert not result.is_valid
        assert "must be one of" in result.errors[0].message

    def test_array_parameter_validation(self):
        """Test array parameter validation."""
        spec = ParameterSpec(name="seeds", type=ParameterType.ARRAY)

        # Valid array
        result = spec.validate_value([1, 2, 3])
        assert result.is_valid

        # Wrong type
        result = spec.validate_value("not an array")
        assert not result.is_valid

    def test_boolean_parameter_validation(self):
        """Test boolean parameter validation."""
        spec = ParameterSpec(name="enhance", type=ParameterType.BOOLEAN)

        # Valid boolean
        result = spec.validate_value(True)
        assert result.is_valid
        result = spec.validate_value(False)
        assert result.is_valid

        # Wrong type
        result = spec.validate_value("true")
        assert not result.is_valid


class TestValidationResult:
    """Test ValidationResult functionality."""

    def test_validation_result_creation(self):
        """Test creating and manipulating ValidationResult."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert len(result.issues) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_adding_issues(self):
        """Test adding different types of issues."""
        result = ValidationResult(is_valid=True)

        result.add_error("param1", "Error message")
        assert not result.is_valid
        assert len(result.errors) == 1
        assert len(result.warnings) == 0

        result.add_warning("param2", "Warning message")
        assert len(result.warnings) == 1
        # is_valid should still be False due to error

        result.add_info("param3", "Info message")
        assert len(result.infos) == 1

    def test_issue_filtering(self):
        """Test filtering issues by severity."""
        result = ValidationResult(is_valid=False)
        result.issues = [
            ValidationIssue(ValidationSeverity.ERROR, "p1", "error"),
            ValidationIssue(ValidationSeverity.WARNING, "p2", "warning"),
            ValidationIssue(ValidationSeverity.INFO, "p3", "info"),
            ValidationIssue(ValidationSeverity.ERROR, "p4", "another error"),
        ]

        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert len(result.infos) == 1


class TestMockFactory:
    """Test the mock factory implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = MockFactory()

    def test_factory_properties(self):
        """Test factory basic properties."""
        assert self.factory.provider_name == "mock"
        assert self.factory.model_name == "test-model"

    def test_parameter_specs_loading(self):
        """Test parameter specs are loaded correctly."""
        specs = self.factory.parameter_specs
        assert len(specs) == 7

        # Check required prompt parameter
        prompt_spec = next(s for s in specs if s.name == "prompt")
        assert prompt_spec.required
        assert prompt_spec.type == ParameterType.STRING

        # Check optional steps parameter with constraints
        steps_spec = next(s for s in specs if s.name == "steps")
        assert not steps_spec.required
        assert steps_spec.min_value == 1
        assert steps_spec.max_value == 100

    def test_fast_validation_success(self):
        """Test fast validation with valid parameters."""
        params = {"prompt": "test prompt", "steps": 25, "guidance_scale": 7.5}

        result = self.factory.validate_parameters_fast(params)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_fast_validation_errors(self):
        """Test fast validation with invalid parameters."""
        params = {
            "steps": 150,  # Above maximum
            "guidance_scale": "not a number",  # Wrong type
        }

        result = self.factory.validate_parameters_fast(params)
        assert not result.is_valid
        assert len(result.errors) >= 2

    def test_fast_validation_missing_required(self):
        """Test validation when required parameter is missing."""
        params = {
            "steps": 25
            # Missing required "prompt"
        }

        result = self.factory.validate_parameters_fast(params)
        assert not result.is_valid
        error_messages = [e.message for e in result.errors]
        assert any("required" in msg for msg in error_messages)

    def test_complete_validation_includes_warnings(self):
        """Test complete validation includes provider-specific warnings."""
        params = {"prompt": "x" * 1500, "steps": 25}  # Very long prompt

        result = self.factory.validate_parameters_complete(params)
        assert result.is_valid  # Should be valid but with warnings
        assert len(result.warnings) > 0
        assert any("long" in w.message for w in result.warnings)

    def test_unknown_parameters_warning(self):
        """Test that unknown parameters generate warnings."""
        params = {"prompt": "test", "unknown_param": "value"}

        result = self.factory.validate_parameters_fast(params)
        assert result.is_valid
        assert len(result.warnings) == 1
        assert "unknown" in result.warnings[0].message.lower()

    def test_create_actual_parameters(self):
        """Test conversion to API format."""
        params = {
            "prompt": "test prompt",
            "steps": 30,
            "guidance_scale": 8.0,
            "scheduler": "DDIM",
        }

        actual = self.factory.create_actual_parameters(params)
        assert actual["input"]["prompt"] == "test prompt"
        assert actual["input"]["num_inference_steps"] == 30
        assert actual["input"]["guidance_scale"] == 8.0
        assert actual["input"]["scheduler"] == "DDIM"

    @pytest.mark.asyncio
    async def test_successful_generation(self):
        """Test successful generation."""
        params = {"prompt": "test prompt"}

        result = await self.factory.generate(params)
        assert result.success
        assert len(result.products) == 1
        assert result.products[0]["type"] == "image"
        assert result.provider_request_id == "mock-123"

    @pytest.mark.asyncio
    async def test_failed_generation(self):
        """Test failed generation."""
        failing_factory = MockFailingFactory()
        params = {"prompt": "test prompt"}

        result = await failing_factory.generate(params)
        assert not result.success
        assert result.error_message == "Mock generation failure"
        assert len(result.products) == 0

    def test_parameter_specs_caching(self):
        """Test that parameter specs are cached."""
        # First access
        specs1 = self.factory.parameter_specs
        # Second access should return same object
        specs2 = self.factory.parameter_specs
        assert specs1 is specs2

    def test_factory_string_representation(self):
        """Test factory string representations."""
        factory_str = str(self.factory)
        assert "MockFactory" in factory_str
        assert "mock/test-model" in factory_str

        factory_repr = repr(self.factory)
        assert "MockFactory" in factory_repr
        assert "provider='mock'" in factory_repr
        assert "model='test-model'" in factory_repr
