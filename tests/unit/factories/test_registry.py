"""
Tests for FactoryRegistry.
"""

import pytest

from app.factories.registry import FactoryRegistry
from app.factories.exceptions import FactoryNotFoundError
from .mock_factory import MockFactory, MockFailingFactory


class TestFactoryRegistry:
    """Test FactoryRegistry functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = FactoryRegistry()

    def test_registry_initialization(self):
        """Test registry starts empty."""
        assert len(self.registry.list_providers()) == 0
        assert self.registry.get_registry_stats()["total_registered"] == 0

    def test_register_factory_class(self):
        """Test registering a factory class."""
        self.registry.register_factory_class("mock", "test-model", MockFactory)

        assert "mock" in self.registry.list_providers()
        assert "test-model" in self.registry.list_models("mock")
        assert self.registry.is_registered("mock", "test-model")

    def test_register_multiple_models(self):
        """Test registering multiple models for same provider."""
        self.registry.register_factory_class("mock", "model1", MockFactory)
        self.registry.register_factory_class("mock", "model2", MockFailingFactory)

        models = self.registry.list_models("mock")
        assert len(models) == 2
        assert "model1" in models
        assert "model2" in models

    def test_register_multiple_providers(self):
        """Test registering multiple providers."""
        self.registry.register_factory_class("provider1", "model1", MockFactory)
        self.registry.register_factory_class("provider2", "model2", MockFactory)

        providers = self.registry.list_providers()
        assert len(providers) == 2
        assert "provider1" in providers
        assert "provider2" in providers

    def test_case_insensitive_registration(self):
        """Test that provider/model names are case insensitive."""
        self.registry.register_factory_class("MOCK", "Test-Model", MockFactory)

        # Should be able to retrieve with different cases
        factory = self.registry.get_factory("mock", "test-model")
        assert factory is not None
        assert isinstance(factory, MockFactory)

    def test_get_factory_success(self):
        """Test getting a factory instance."""
        self.registry.register_factory_class("mock", "test-model", MockFactory)

        factory = self.registry.get_factory("mock", "test-model")
        assert isinstance(factory, MockFactory)
        assert factory.provider_name == "mock"
        assert factory.model_name == "test-model"

    def test_get_factory_caching(self):
        """Test that factory instances are cached."""
        self.registry.register_factory_class("mock", "test-model", MockFactory)

        factory1 = self.registry.get_factory("mock", "test-model")
        factory2 = self.registry.get_factory("mock", "test-model")

        # Should be the same instance
        assert factory1 is factory2

    def test_get_factory_not_found(self):
        """Test getting factory that doesn't exist."""
        with pytest.raises(FactoryNotFoundError) as exc_info:
            self.registry.get_factory("nonexistent", "model")

        assert "No factory registered" in str(exc_info.value)

    def test_get_factory_invalid_params(self):
        """Test getting factory with invalid parameters."""
        with pytest.raises(ValueError):
            self.registry.get_factory("", "model")

        with pytest.raises(ValueError):
            self.registry.get_factory("provider", "")

    def test_unregister_factory(self):
        """Test unregistering a factory."""
        self.registry.register_factory_class("mock", "test-model", MockFactory)
        assert self.registry.is_registered("mock", "test-model")

        # Unregister
        result = self.registry.unregister_factory("mock", "test-model")
        assert result is True
        assert not self.registry.is_registered("mock", "test-model")

        # Try to unregister again
        result = self.registry.unregister_factory("mock", "test-model")
        assert result is False

    def test_unregister_provider_cleanup(self):
        """Test that providers are cleaned up when all models are unregistered."""
        self.registry.register_factory_class("mock", "model1", MockFactory)
        self.registry.register_factory_class("mock", "model2", MockFactory)

        assert "mock" in self.registry.list_providers()

        # Unregister first model
        self.registry.unregister_factory("mock", "model1")
        assert "mock" in self.registry.list_providers()  # Still has model2

        # Unregister second model
        self.registry.unregister_factory("mock", "model2")
        assert "mock" not in self.registry.list_providers()  # Provider removed

    def test_clear_cache(self):
        """Test clearing cached factory instances."""
        self.registry.register_factory_class("mock", "test-model", MockFactory)

        # Get factory to create cached instance
        factory1 = self.registry.get_factory("mock", "test-model")

        # Clear cache
        self.registry.clear_cache()

        # Get factory again - should be new instance
        factory2 = self.registry.get_factory("mock", "test-model")
        assert factory1 is not factory2

    def test_list_available_combinations(self):
        """Test listing all available combinations."""
        self.registry.register_factory_class("provider1", "model1", MockFactory)
        self.registry.register_factory_class("provider1", "model2", MockFactory)
        self.registry.register_factory_class("provider2", "model3", MockFactory)

        combinations = self.registry.list_available_combinations()
        assert len(combinations) == 3
        assert ("provider1", "model1") in combinations
        assert ("provider1", "model2") in combinations
        assert ("provider2", "model3") in combinations

    def test_get_factory_info(self):
        """Test getting factory information."""
        self.registry.register_factory_class("mock", "test-model", MockFactory)

        # Before caching
        info = self.registry.get_factory_info("mock", "test-model")
        assert info["provider"] == "mock"
        assert info["model"] == "test-model"
        assert info["factory_class"] == "MockFactory"
        assert not info["is_cached"]

        # After caching
        self.registry.get_factory("mock", "test-model")  # Create cached instance
        info = self.registry.get_factory_info("mock", "test-model")
        assert info["is_cached"]
        assert "parameter_count" in info

    def test_get_factory_info_not_found(self):
        """Test getting info for non-existent factory."""
        with pytest.raises(FactoryNotFoundError):
            self.registry.get_factory_info("nonexistent", "model")

    def test_get_registry_stats(self):
        """Test getting registry statistics."""
        stats = self.registry.get_registry_stats()
        assert stats["total_registered"] == 0
        assert stats["total_cached"] == 0
        assert stats["providers"] == 0

        # Add some factories
        self.registry.register_factory_class("provider1", "model1", MockFactory)
        self.registry.register_factory_class("provider1", "model2", MockFactory)
        self.registry.register_factory_class("provider2", "model3", MockFactory)

        # Cache one factory
        self.registry.get_factory("provider1", "model1")

        stats = self.registry.get_registry_stats()
        assert stats["total_registered"] == 3
        assert stats["total_cached"] == 1
        assert stats["providers"] == 2
        assert stats["provider_details"]["provider1"] == 2
        assert stats["provider_details"]["provider2"] == 1

    def test_list_models_invalid_provider(self):
        """Test listing models for non-existent provider."""
        with pytest.raises(ValueError) as exc_info:
            self.registry.list_models("nonexistent")

        assert "not registered" in str(exc_info.value)

    def test_registry_string_representation(self):
        """Test registry string representations."""
        self.registry.register_factory_class("mock", "test-model", MockFactory)

        registry_str = str(self.registry)
        assert "FactoryRegistry" in registry_str
        assert "1 registered" in registry_str

        registry_repr = repr(self.registry)
        assert "FactoryRegistry" in registry_repr
        assert "mock" in registry_repr

    def test_registration_replaces_existing(self):
        """Test that re-registering a factory replaces the existing one."""
        self.registry.register_factory_class("mock", "test-model", MockFactory)

        # Get factory to cache it
        factory1 = self.registry.get_factory("mock", "test-model")

        # Re-register with different class
        self.registry.register_factory_class("mock", "test-model", MockFailingFactory)

        # Should get new instance of new class
        factory2 = self.registry.get_factory("mock", "test-model")
        assert factory1 is not factory2
        assert isinstance(factory2, MockFailingFactory)

    def test_register_empty_names(self):
        """Test registering with empty provider or model names."""
        with pytest.raises(ValueError):
            self.registry.register_factory_class("", "model", MockFactory)

        with pytest.raises(ValueError):
            self.registry.register_factory_class("provider", "", MockFactory)
