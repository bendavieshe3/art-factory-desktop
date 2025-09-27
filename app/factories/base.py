"""
Base factory classes and data structures for AI provider integration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union
import logging


logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ParameterType(Enum):
    """Supported parameter types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ValidationIssue:
    """Represents a validation issue with a parameter."""

    severity: ValidationSeverity
    parameter: str
    message: str
    code: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.severity.value.upper()}: {self.parameter} - {self.message}"


@dataclass
class ValidationResult:
    """Result of parameter validation."""

    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    @property
    def infos(self) -> List[ValidationIssue]:
        """Get only info-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.INFO]

    def add_error(self, parameter: str, message: str, code: str = None):
        """Add an error to the validation result."""
        self.issues.append(
            ValidationIssue(ValidationSeverity.ERROR, parameter, message, code)
        )
        self.is_valid = False

    def add_warning(self, parameter: str, message: str, code: str = None):
        """Add a warning to the validation result."""
        self.issues.append(
            ValidationIssue(ValidationSeverity.WARNING, parameter, message, code)
        )

    def add_info(self, parameter: str, message: str, code: str = None):
        """Add an info message to the validation result."""
        self.issues.append(
            ValidationIssue(ValidationSeverity.INFO, parameter, message, code)
        )


@dataclass
class ParameterSpec:
    """Specification for a parameter supported by a factory."""

    name: str
    type: ParameterType
    required: bool = False
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    choices: Optional[List[Any]] = None
    description: Optional[str] = None

    def validate_value(self, value: Any) -> ValidationResult:
        """Validate a value against this parameter specification."""
        result = ValidationResult(is_valid=True)

        # Check if value is provided for required parameter
        if self.required and (value is None or value == ""):
            result.add_error(self.name, f"Parameter '{self.name}' is required")
            return result

        # If value is None and not required, that's fine
        if value is None:
            return result

        # Type validation
        if not self._validate_type(value):
            result.add_error(
                self.name,
                f"Parameter '{self.name}' must be of type {self.type.value}, got {type(value).__name__}",
            )
            return result

        # Range validation for numeric types
        if self.type in [ParameterType.INTEGER, ParameterType.FLOAT]:
            if self.min_value is not None and value < self.min_value:
                result.add_error(
                    self.name,
                    f"Parameter '{self.name}' must be >= {self.min_value}, got {value}",
                )
            if self.max_value is not None and value > self.max_value:
                result.add_error(
                    self.name,
                    f"Parameter '{self.name}' must be <= {self.max_value}, got {value}",
                )

        # Choice validation
        if self.choices is not None and value not in self.choices:
            result.add_error(
                self.name,
                f"Parameter '{self.name}' must be one of {self.choices}, got {value}",
            )

        return result

    def _validate_type(self, value: Any) -> bool:
        """Check if value matches the expected type."""
        if self.type == ParameterType.STRING:
            return isinstance(value, str)
        elif self.type == ParameterType.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)
        elif self.type == ParameterType.FLOAT:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif self.type == ParameterType.BOOLEAN:
            return isinstance(value, bool)
        elif self.type == ParameterType.ARRAY:
            return isinstance(value, list)
        elif self.type == ParameterType.OBJECT:
            return isinstance(value, dict)
        return False


@dataclass
class GenerationResult:
    """Result of a generation operation."""

    success: bool
    products: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    provider_request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseProductFactory(ABC):
    """Abstract base factory for all AI providers."""

    def __init__(self):
        self._parameter_specs: Optional[List[ParameterSpec]] = None
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @property
    def parameter_specs(self) -> List[ParameterSpec]:
        """Get cached parameter specifications."""
        if self._parameter_specs is None:
            self._parameter_specs = self._load_parameter_specs()
            self.logger.debug(f"Loaded {len(self._parameter_specs)} parameter specs")
        return self._parameter_specs

    @abstractmethod
    def _load_parameter_specs(self) -> List[ParameterSpec]:
        """Load parameter specifications (initially hardcoded, future: dynamic)."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name (e.g., 'replicate', 'fal')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name (e.g., 'stability-ai/sdxl')."""
        pass

    # Fast sync methods for UI responsiveness
    def validate_parameters_fast(self, params: Dict[str, Any]) -> ValidationResult:
        """Quick validation for immediate UI feedback.

        Performs basic type and constraint validation without expensive operations.
        """
        result = ValidationResult(is_valid=True)

        try:
            # Basic validation against parameter specs
            result = self._validate_against_specs(params)

            # Quick format checks
            if result.is_valid:
                self._validate_basic_formats(params, result)

        except Exception as e:
            self.logger.error(f"Fast validation failed: {e}")
            result.add_error("system", f"Validation system error: {str(e)}")

        return result

    def validate_parameters_complete(self, params: Dict[str, Any]) -> ValidationResult:
        """Comprehensive validation including provider-specific rules.

        Performs thorough validation that may include model-specific constraints.
        """
        result = self.validate_parameters_fast(params)

        if result.is_valid:
            try:
                # Additional comprehensive validation
                self._validate_provider_specific(params, result)
                self._validate_parameter_combinations(params, result)

            except Exception as e:
                self.logger.error(f"Complete validation failed: {e}")
                result.add_error("system", f"Validation system error: {str(e)}")

        return result

    async def validate_parameters_async(
        self, params: Dict[str, Any]
    ) -> ValidationResult:
        """Future: async validation with provider API checks."""
        # For now, defer to complete validation
        # Future: could include API calls to validate model availability, etc.
        return self.validate_parameters_complete(params)

    def _validate_against_specs(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate parameters against specifications."""
        result = ValidationResult(is_valid=True)

        # Create a set of provided parameters
        provided_params = set(params.keys())

        # Validate each spec
        for spec in self.parameter_specs:
            param_result = spec.validate_value(params.get(spec.name))
            result.issues.extend(param_result.issues)
            if not param_result.is_valid:
                result.is_valid = False

        # Check for unknown parameters
        spec_names = {spec.name for spec in self.parameter_specs}
        unknown_params = provided_params - spec_names
        for param in unknown_params:
            result.add_warning(param, f"Unknown parameter '{param}' will be ignored")

        return result

    def _validate_basic_formats(self, params: Dict[str, Any], result: ValidationResult):
        """Validate basic parameter formats (override in subclasses)."""
        pass

    def _validate_provider_specific(
        self, params: Dict[str, Any], result: ValidationResult
    ):
        """Validate provider-specific constraints (override in subclasses)."""
        pass

    def _validate_parameter_combinations(
        self, params: Dict[str, Any], result: ValidationResult
    ):
        """Validate parameter combinations and dependencies (override in subclasses)."""
        pass

    @abstractmethod
    def create_actual_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert generation parameters to provider API format.

        This method transforms the validated generation parameters into the exact
        format required by the provider's API.
        """
        pass

    @abstractmethod
    async def generate(self, params: Dict[str, Any]) -> GenerationResult:
        """Execute generation and return results.

        Args:
            params: Validated generation parameters

        Returns:
            GenerationResult with success status and product data

        Raises:
            ProviderAPIError: For API-level errors (network, auth, etc.)
            GenerationError: For system-level errors
        """
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.provider_name}/{self.model_name})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider='{self.provider_name}' model='{self.model_name}'>"
