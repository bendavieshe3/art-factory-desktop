"""
Integration tests for factory system with OrderService.
"""

import pytest

from app.factories import factory_registry, FactoryNotFoundError
from app.factories.base import ParameterType
from .mock_factory import MockFactory


class TestFactoryIntegration:
    """Test integration between factories and other components."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear registry
        factory_registry.clear_cache()

        # Register test factory
        factory_registry.register_factory_class("mock", "test-model", MockFactory)

    def teardown_method(self):
        """Clean up after tests."""
        # Clear registry
        factory_registry.clear_cache()

    def test_factory_registration_and_retrieval(self):
        """Test that factories can be registered and retrieved."""
        factory = factory_registry.get_factory("mock", "test-model")
        assert isinstance(factory, MockFactory)
        assert factory.provider_name == "mock"
        assert factory.model_name == "test-model"

    def test_factory_parameter_validation_flow(self):
        """Test the complete parameter validation flow."""
        factory = factory_registry.get_factory("mock", "test-model")

        # Test valid parameters
        valid_params = {
            "prompt": "a beautiful landscape",
            "steps": 20,
            "guidance_scale": 7.5,
            "scheduler": "DPMSolverMultistep",
        }

        result = factory.validate_parameters_fast(valid_params)
        assert result.is_valid
        assert len(result.errors) == 0

        # Test invalid parameters
        invalid_params = {
            "prompt": "test prompt",
            "steps": 150,  # Above maximum
            "guidance_scale": "invalid",  # Wrong type
            "unknown_param": "value",  # Unknown parameter
        }

        result = factory.validate_parameters_fast(invalid_params)
        assert not result.is_valid
        assert len(result.errors) >= 2  # steps and guidance_scale errors
        assert len(result.warnings) >= 1  # unknown parameter warning

    def test_factory_parameter_conversion(self):
        """Test parameter conversion to API format."""
        factory = factory_registry.get_factory("mock", "test-model")

        params = {
            "prompt": "test prompt",
            "steps": 30,
            "guidance_scale": 8.0,
            "scheduler": "DDIM",
            "enhance_quality": True,
        }

        api_params = factory.create_actual_parameters(params)

        assert api_params["input"]["prompt"] == "test prompt"
        assert api_params["input"]["num_inference_steps"] == 30
        assert api_params["input"]["guidance_scale"] == 8.0
        assert api_params["input"]["scheduler"] == "DDIM"
        assert api_params["input"]["enhance"] is True

    def test_factory_not_found_handling(self):
        """Test handling when factory is not found."""
        with pytest.raises(FactoryNotFoundError):
            factory_registry.get_factory("nonexistent", "model")

    def test_factory_caching_behavior(self):
        """Test that factory instances are properly cached."""
        factory1 = factory_registry.get_factory("mock", "test-model")
        factory2 = factory_registry.get_factory("mock", "test-model")

        # Should be the same instance
        assert factory1 is factory2

        # Clear cache and get new instance
        factory_registry.clear_cache()
        factory3 = factory_registry.get_factory("mock", "test-model")

        # Should be different instance
        assert factory1 is not factory3
        assert isinstance(factory3, MockFactory)

    def test_parameter_specs_functionality(self):
        """Test parameter specifications functionality."""
        factory = factory_registry.get_factory("mock", "test-model")
        specs = factory.parameter_specs

        # Check that we have expected specs
        assert len(specs) == 7  # From MockFactory

        # Find specific specs
        prompt_spec = next((s for s in specs if s.name == "prompt"), None)
        assert prompt_spec is not None
        assert prompt_spec.required is True
        assert prompt_spec.type == ParameterType.STRING

        steps_spec = next((s for s in specs if s.name == "steps"), None)
        assert steps_spec is not None
        assert steps_spec.required is False
        assert steps_spec.type == ParameterType.INTEGER
        assert steps_spec.min_value == 1
        assert steps_spec.max_value == 100

    def test_validation_result_structure(self):
        """Test ValidationResult structure and functionality."""
        factory = factory_registry.get_factory("mock", "test-model")

        params = {
            "prompt": "",  # Empty required field
            "steps": -5,  # Below minimum
            "unknown": "value",  # Unknown parameter
        }

        result = factory.validate_parameters_fast(params)

        assert not result.is_valid
        assert len(result.errors) >= 2  # Empty prompt and negative steps
        assert len(result.warnings) >= 1  # Unknown parameter

        # Test error/warning separation
        errors = result.errors
        warnings = result.warnings

        assert all(issue.severity.value == "error" for issue in errors)
        assert all(issue.severity.value == "warning" for issue in warnings)

    def test_registry_stats_and_info(self):
        """Test registry statistics and information methods."""
        stats = factory_registry.get_registry_stats()

        assert stats["total_registered"] == 1
        assert stats["providers"] == 1
        assert "mock" in stats["provider_details"]
        assert stats["provider_details"]["mock"] == 1

        # Test factory info
        info = factory_registry.get_factory_info("mock", "test-model")
        assert info["provider"] == "mock"
        assert info["model"] == "test-model"
        assert info["factory_class"] == "MockFactory"

    def test_complete_vs_fast_validation(self):
        """Test difference between complete and fast validation."""
        factory = factory_registry.get_factory("mock", "test-model")

        params = {
            "prompt": "x"
            * 1500,  # Very long prompt (should trigger warning in complete)
            "steps": 5,
            "guidance_scale": 16.0,
        }

        # Fast validation should be quick and basic
        fast_result = factory.validate_parameters_fast(params)
        assert fast_result.is_valid

        # Complete validation should include provider-specific warnings
        complete_result = factory.validate_parameters_complete(params)
        assert complete_result.is_valid
        assert (
            len(complete_result.warnings) > 0
        )  # Should have warning about long prompt

    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation method."""
        factory = factory_registry.get_factory("mock", "test-model")

        params = {"prompt": "test prompt", "steps": 20}

        result = await factory.validate_parameters_async(params)
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_generation_flow(self):
        """Test the generation flow."""
        factory = factory_registry.get_factory("mock", "test-model")

        params = {"prompt": "test prompt", "steps": 20}

        # Validate first
        validation = factory.validate_parameters_fast(params)
        assert validation.is_valid

        # Convert to API format
        api_params = factory.create_actual_parameters(params)
        assert "input" in api_params

        # Generate
        result = await factory.generate(params)
        assert result.success
        assert len(result.products) == 1
        assert result.provider_request_id is not None
