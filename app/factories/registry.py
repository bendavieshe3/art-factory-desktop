"""
Factory registry for managing AI provider factories.
"""

from typing import Dict, List, Tuple, Type
import logging

from .base import BaseProductFactory
from .exceptions import FactoryNotFoundError


logger = logging.getLogger(__name__)


class FactoryRegistry:
    """Registry for managing factory instances with caching."""

    def __init__(self):
        self._factories: Dict[Tuple[str, str], BaseProductFactory] = {}
        self._factory_classes: Dict[Tuple[str, str], Type[BaseProductFactory]] = {}
        self._provider_models: Dict[str, List[str]] = {}

    def register_factory_class(
        self, provider: str, model: str, factory_class: Type[BaseProductFactory]
    ) -> None:
        """Register a factory class for a provider/model combination.

        Args:
            provider: Provider name (e.g., 'replicate', 'fal')
            model: Model name (e.g., 'stability-ai/sdxl')
            factory_class: Factory class to register

        Raises:
            ValueError: If provider or model is empty
        """
        if not provider or not model:
            raise ValueError("Provider and model names cannot be empty")

        key = (provider.lower(), model.lower())

        # Store the factory class
        self._factory_classes[key] = factory_class

        # Update provider-model mapping
        if provider not in self._provider_models:
            self._provider_models[provider] = []
        if model not in self._provider_models[provider]:
            self._provider_models[provider].append(model)

        logger.info(
            f"Registered factory class for {provider}/{model}: {factory_class.__name__}"
        )

        # If we already have an instance cached, remove it to force recreation
        if key in self._factories:
            del self._factories[key]
            logger.debug(f"Cleared cached factory instance for {provider}/{model}")

    def get_factory(self, provider: str, model: str) -> BaseProductFactory:
        """Get a factory instance for the provider/model combination.

        Factory instances are cached for performance.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            BaseProductFactory instance

        Raises:
            FactoryNotFoundError: If no factory is registered for the combination
        """
        if not provider or not model:
            raise ValueError("Provider and model names cannot be empty")

        key = (provider.lower(), model.lower())

        # Return cached instance if available
        if key in self._factories:
            return self._factories[key]

        # Create new instance if factory class is registered
        if key in self._factory_classes:
            factory_class = self._factory_classes[key]
            try:
                factory_instance = factory_class()
                self._factories[key] = factory_instance
                logger.debug(
                    f"Created and cached factory instance for {provider}/{model}"
                )
                return factory_instance
            except Exception as e:
                logger.error(
                    f"Failed to create factory instance for {provider}/{model}: {e}"
                )
                raise FactoryNotFoundError(
                    f"Failed to create factory for {provider}/{model}: {str(e)}"
                )

        # No factory found
        available = self.list_available_combinations()
        raise FactoryNotFoundError(
            f"No factory registered for {provider}/{model}. " f"Available: {available}"
        )

    def list_providers(self) -> List[str]:
        """Get list of all registered providers."""
        return list(self._provider_models.keys())

    def list_models(self, provider: str) -> List[str]:
        """Get list of models for a specific provider.

        Args:
            provider: Provider name

        Returns:
            List of model names for the provider

        Raises:
            ValueError: If provider is not registered
        """
        if provider not in self._provider_models:
            raise ValueError(f"Provider '{provider}' not registered")
        return self._provider_models[provider].copy()

    def list_available_combinations(self) -> List[Tuple[str, str]]:
        """Get list of all available provider/model combinations."""
        combinations = []
        for provider, models in self._provider_models.items():
            for model in models:
                combinations.append((provider, model))
        return combinations

    def is_registered(self, provider: str, model: str) -> bool:
        """Check if a factory is registered for the provider/model combination.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            True if factory is registered, False otherwise
        """
        key = (provider.lower(), model.lower())
        return key in self._factory_classes

    def unregister_factory(self, provider: str, model: str) -> bool:
        """Unregister a factory for the provider/model combination.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            True if factory was unregistered, False if it wasn't registered
        """
        key = (provider.lower(), model.lower())

        if key not in self._factory_classes:
            return False

        # Remove from factory classes
        del self._factory_classes[key]

        # Remove cached instance if it exists
        if key in self._factories:
            del self._factories[key]

        # Update provider-model mapping
        if provider in self._provider_models:
            if model in self._provider_models[provider]:
                self._provider_models[provider].remove(model)
            # Remove provider if no models left
            if not self._provider_models[provider]:
                del self._provider_models[provider]

        logger.info(f"Unregistered factory for {provider}/{model}")
        return True

    def clear_cache(self) -> None:
        """Clear all cached factory instances.

        Factory classes remain registered, but instances will be recreated on next access.
        """
        self._factories.clear()
        logger.info("Cleared all cached factory instances")

    def get_factory_info(self, provider: str, model: str) -> Dict[str, any]:
        """Get information about a registered factory.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            Dictionary with factory information

        Raises:
            FactoryNotFoundError: If factory is not registered
        """
        key = (provider.lower(), model.lower())

        if key not in self._factory_classes:
            raise FactoryNotFoundError(f"No factory registered for {provider}/{model}")

        factory_class = self._factory_classes[key]
        is_cached = key in self._factories

        info = {
            "provider": provider,
            "model": model,
            "factory_class": factory_class.__name__,
            "factory_module": factory_class.__module__,
            "is_cached": is_cached,
        }

        if is_cached:
            factory = self._factories[key]
            info["parameter_count"] = len(factory.parameter_specs)

        return info

    def get_registry_stats(self) -> Dict[str, any]:
        """Get overall registry statistics."""
        return {
            "total_registered": len(self._factory_classes),
            "total_cached": len(self._factories),
            "providers": len(self._provider_models),
            "provider_details": {
                provider: len(models)
                for provider, models in self._provider_models.items()
            },
        }

    def __str__(self) -> str:
        stats = self.get_registry_stats()
        return f"FactoryRegistry({stats['total_registered']} registered, {stats['total_cached']} cached)"

    def __repr__(self) -> str:
        return f"<FactoryRegistry providers={self.list_providers()}>"


# Global registry instance
factory_registry = FactoryRegistry()
