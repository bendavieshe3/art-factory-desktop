"""
Factory system for AI provider integration.

This module provides the base factory pattern and registry for integrating
with various AI providers (Replicate, fal.ai, etc.).
"""

from .base import (
    BaseProductFactory,
    ParameterSpec,
    ValidationResult,
    ValidationIssue,
    GenerationResult,
)
from .registry import FactoryRegistry, factory_registry
from .exceptions import FactoryError, FactoryNotFoundError, ValidationError

__all__ = [
    "BaseProductFactory",
    "ParameterSpec",
    "ValidationResult",
    "ValidationIssue",
    "GenerationResult",
    "FactoryRegistry",
    "factory_registry",
    "FactoryError",
    "FactoryNotFoundError",
    "ValidationError",
]
