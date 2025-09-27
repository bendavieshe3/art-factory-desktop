"""
Factory-specific exceptions.
"""


class FactoryError(Exception):
    """Base exception for factory-related errors."""

    pass


class FactoryNotFoundError(FactoryError):
    """Raised when a factory is not found for a provider/model combination."""

    pass


class ValidationError(FactoryError):
    """Raised when parameter validation fails at the system level."""

    pass


class GenerationError(FactoryError):
    """Raised when generation fails at the system level."""

    pass


class ProviderAPIError(GenerationError):
    """Raised when provider API returns an error."""

    def __init__(
        self, message: str, status_code: int = None, provider_error: str = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.provider_error = provider_error
