"""
Order Management Service.

Handles Order and OrderItem creation, parameter expansion, and validation.
Implements two-phase approach:
- Phase 1: Basic order management (1:1 Order→OrderItem)
- Phase 2: Parameter expansion (token/range/subprompt expansion)
"""

import re
from typing import Dict, List, Any, Optional, Union, NamedTuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models import Order, OrderItem
from ..models.database import session_scope
from ..factories import factory_registry, FactoryNotFoundError, ValidationError
from ..factories.base import ValidationResult as FactoryValidationResult
from ..events import event_bus, Event, EventTypes, EventSeverity


class ValidationResult(NamedTuple):
    """Result of parameter validation (legacy - use FactoryValidationResult for new code)."""

    is_valid: bool
    errors: List[str]
    warnings: List[str] = []


class ExpansionPreview(NamedTuple):
    """Preview of parameter expansion results."""

    total_items: int
    has_tokens: bool
    has_ranges: bool
    has_subprompts: bool
    estimated_cost: Optional[float] = None


class OrderServiceError(Exception):
    """Base exception for OrderService errors."""

    pass


class ParameterValidationError(OrderServiceError):
    """Raised when parameter validation fails."""

    pass


class ExpansionError(OrderServiceError):
    """Raised when parameter expansion fails."""

    pass


class OrderService:
    """
    Service for Order and OrderItem management with parameter expansion.

    Provides both basic order management and advanced parameter expansion
    including token expansion, range interpolation, and sub-prompt handling.
    """

    # Configuration
    DEFAULT_MAX_ITEMS = 100
    REQUIRED_FIELDS = ["prompt"]  # Basic required parameters

    def __init__(self, max_items: int = DEFAULT_MAX_ITEMS):
        """Initialize OrderService with configuration."""
        self.max_items = max_items

    # Phase 1: Basic Order Management

    def create_order_items(
        self, order: Order, session: Optional[Session] = None
    ) -> List[OrderItem]:
        """
        Create OrderItems from Order with parameter expansion support.

        Args:
            order: Order instance to process
            session: Optional database session (will create if not provided)

        Returns:
            List of created OrderItem instances

        Raises:
            ParameterValidationError: If base parameters are invalid
            ExpansionError: If parameter expansion fails
            OrderServiceError: For other service-level errors
        """
        if session is None:
            with session_scope() as session:
                return self._create_order_items_with_session(order, session)
        else:
            return self._create_order_items_with_session(order, session)

    def _create_order_items_with_session(self, order: Order, session: Session) -> List[OrderItem]:
        """Internal implementation with guaranteed session."""
        try:
            # Validate base parameters
            validation = self.validate_base_parameters(order.base_parameter_set or {})
            if not validation.is_valid:
                # Emit validation failed event
                event_bus.publish(Event(
                    type=EventTypes.VALIDATION_FAILED,
                    source="order_service",
                    severity=EventSeverity.ERROR,
                    order_id=order.id,
                    data={
                        "validation_errors": validation.errors,
                        "validation_warnings": validation.warnings
                    }
                ))
                raise ParameterValidationError(
                    f"Invalid parameters: {', '.join(validation.errors)}"
                )

            # Check if expansion is needed
            expanded_params = self.expand_parameters(order.base_parameter_set or {})

            # Emit parameter expansion event
            event_bus.publish(Event(
                type=EventTypes.PARAMETER_EXPANSION,
                source="order_service",
                order_id=order.id,
                data={
                    "base_parameters": order.base_parameter_set,
                    "expanded_count": len(expanded_params),
                    "expansion_types": self._analyze_expansion_types(order.base_parameter_set or {})
                }
            ))

            # Validate expansion limits
            if len(expanded_params) > self.max_items:
                # Emit expansion limit exceeded event
                event_bus.publish(Event(
                    type=EventTypes.EXPANSION_LIMIT_EXCEEDED,
                    source="order_service",
                    severity=EventSeverity.ERROR,
                    order_id=order.id,
                    data={
                        "expanded_count": len(expanded_params),
                        "max_limit": self.max_items
                    }
                ))
                raise ExpansionError(
                    f"Parameter expansion would create {len(expanded_params)} "
                    f"OrderItems, which exceeds the limit of {self.max_items}"
                )

            # Create OrderItems
            order_items = []
            for i, params in enumerate(expanded_params):
                order_item = OrderItem(
                    order_id=order.id,
                    sequence_number=i + 1,
                    generation_parameter_set=params,
                    status="pending",
                )
                order_items.append(order_item)
                session.add(order_item)

            # Update order counts and status
            order.expanded_count = len(order_items)
            order.status = "processing" if order_items else "pending"

            session.commit()

            # Emit order items created event
            event_bus.publish(Event(
                type=EventTypes.ORDER_ITEMS_CREATED,
                source="order_service",
                order_id=order.id,
                data={
                    "order_item_count": len(order_items),
                    "expansion_result": {
                        "total_items": len(expanded_params),
                        "expanded_from_base": len(expanded_params) > 1
                    }
                }
            ))

            return order_items

        except SQLAlchemyError as e:
            session.rollback()
            raise OrderServiceError(f"Database error creating order items: {str(e)}")
        except Exception as e:
            session.rollback()
            raise OrderServiceError(f"Unexpected error creating order items: {str(e)}")

    def validate_base_parameters(self, params: Dict[str, Any]) -> ValidationResult:
        """
        Validate base parameters for type safety and required fields.

        Args:
            params: Parameter dictionary to validate

        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        warnings = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in params or not params[field]:
                errors.append(f"Required field '{field}' is missing or empty")

        # Type validation
        if "prompt" in params and not isinstance(params["prompt"], str):
            errors.append("'prompt' must be a string")

        if "negative_prompt" in params and not isinstance(params["negative_prompt"], str):
            errors.append("'negative_prompt' must be a string")

        if "steps" in params:
            if isinstance(params["steps"], str):
                # Check if it's a valid range/expansion syntax
                if not self._is_valid_range_syntax(params["steps"]):
                    errors.append(f"'steps' has invalid range syntax: {params['steps']}")
            elif not isinstance(params["steps"], (int, float)):
                errors.append("'steps' must be a number or valid range string")
            elif isinstance(params["steps"], (int, float)) and params["steps"] <= 0:
                errors.append("'steps' must be positive")

        if "guidance_scale" in params:
            if isinstance(params["guidance_scale"], str):
                if not self._is_valid_range_syntax(params["guidance_scale"]):
                    errors.append(
                        f"'guidance_scale' has invalid range syntax: " f"{params['guidance_scale']}"
                    )
            elif not isinstance(params["guidance_scale"], (int, float)):
                errors.append("'guidance_scale' must be a number or valid range string")

        # Check for potential expansion syntax issues
        for key, value in params.items():
            if isinstance(value, str):
                if "[" in value and "]" in value:
                    if not self._is_valid_token_syntax(value):
                        errors.append(f"'{key}' has invalid token expansion syntax")
                if ".." in value:
                    if not self._is_valid_range_syntax(value):
                        errors.append(f"'{key}' has invalid range expansion syntax")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_with_factory(
        self, params: Dict[str, Any], provider: str, model: str
    ) -> FactoryValidationResult:
        """
        Validate parameters using factory-specific validation.

        Args:
            params: Parameters to validate
            provider: Provider name (e.g., 'replicate', 'fal')
            model: Model name (e.g., 'stability-ai/sdxl')

        Returns:
            FactoryValidationResult with detailed validation information

        Raises:
            FactoryNotFoundError: If no factory is registered for provider/model
        """
        try:
            # Get factory for validation
            factory = factory_registry.get_factory(provider, model)

            # Use factory's comprehensive validation
            return factory.validate_parameters_complete(params)

        except FactoryNotFoundError:
            # If no factory found, fall back to basic validation
            basic_result = self.validate_base_parameters(params)

            # Convert to FactoryValidationResult format
            factory_result = FactoryValidationResult(is_valid=basic_result.is_valid)

            for error in basic_result.errors:
                factory_result.add_error("parameter", error)

            for warning in basic_result.warnings:
                factory_result.add_warning("parameter", warning)

            # Add info about missing factory
            factory_result.add_info(
                "factory",
                f"No factory found for {provider}/{model}, using basic validation"
            )

            return factory_result

    def validate_with_factory_fast(
        self, params: Dict[str, Any], provider: str, model: str
    ) -> FactoryValidationResult:
        """
        Fast factory-based validation for UI responsiveness.

        Args:
            params: Parameters to validate
            provider: Provider name
            model: Model name

        Returns:
            FactoryValidationResult with basic validation results
        """
        try:
            factory = factory_registry.get_factory(provider, model)
            return factory.validate_parameters_fast(params)
        except FactoryNotFoundError:
            # Fall back to basic validation
            basic_result = self.validate_base_parameters(params)
            factory_result = FactoryValidationResult(is_valid=basic_result.is_valid)

            for error in basic_result.errors:
                factory_result.add_error("parameter", error)

            return factory_result

    def preview_expansion_with_factory(
        self, params: Dict[str, Any], provider: str = None, model: str = None
    ) -> ExpansionPreview:
        """
        Preview expansion with optional factory validation.

        Args:
            params: Base parameters to analyze
            provider: Optional provider name for factory validation
            model: Optional model name for factory validation

        Returns:
            ExpansionPreview with expansion statistics
        """
        try:
            # If factory info provided, validate first
            if provider and model:
                try:
                    factory = factory_registry.get_factory(provider, model)
                    validation_result = factory.validate_parameters_fast(params)

                    if not validation_result.is_valid:
                        # Still preview, but note validation issues
                        pass

                except FactoryNotFoundError:
                    # Continue without factory validation
                    pass

            # Use existing expansion logic
            return self.preview_expansion(params)

        except Exception as e:
            raise ExpansionError(f"Failed to preview expansion: {str(e)}")

    def update_order_status(self, order_id: str, session: Optional[Session] = None) -> None:
        """
        Update order status based on OrderItem statuses.

        Args:
            order_id: ID of order to update
            session: Optional database session
        """
        if session is None:
            with session_scope() as session:
                self._update_order_status_with_session(order_id, session)
        else:
            self._update_order_status_with_session(order_id, session)

    def _update_order_status_with_session(self, order_id: str, session: Session) -> None:
        """Internal implementation with guaranteed session."""
        try:
            order = session.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise OrderServiceError(f"Order {order_id} not found")

            # Count statuses
            completed_count = sum(1 for item in order.order_items if item.status == "complete")
            failed_count = sum(1 for item in order.order_items if item.status == "failed")

            # Update counts
            order.completed_count = completed_count
            order.failed_count = failed_count

            # Update status using existing model logic
            order.update_status()

            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            raise OrderServiceError(f"Database error updating order status: {str(e)}")

    # Phase 2: Parameter Expansion

    def preview_expansion(self, params: Dict[str, Any]) -> ExpansionPreview:
        """
        Preview how many OrderItems would be generated from parameter expansion.

        Args:
            params: Base parameters to analyze

        Returns:
            ExpansionPreview with expansion statistics
        """
        try:
            expanded = self.expand_parameters(params)

            # Analyze what types of expansion were found
            has_tokens = any("[" in str(v) and "]" in str(v) for v in params.values())
            has_ranges = any(".." in str(v) for v in params.values())
            has_subprompts = "||" in params.get("prompt", "") or "||" in params.get(
                "negative_prompt", ""
            )

            return ExpansionPreview(
                total_items=len(expanded),
                has_tokens=has_tokens,
                has_ranges=has_ranges,
                has_subprompts=has_subprompts,
            )
        except Exception as e:
            raise ExpansionError(f"Failed to preview expansion: {str(e)}")

    def expand_parameters(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Core parameter expansion logic.

        Handles token expansion, range interpolation, and sub-prompts.
        Returns list of parameter dictionaries for OrderItem creation.

        Args:
            params: Base parameters to expand

        Returns:
            List of expanded parameter dictionaries

        Raises:
            ExpansionError: If expansion syntax is invalid
        """
        try:
            # Start with base parameters
            result_list = [params.copy()]

            # Handle sub-prompts first (for prompt and negative_prompt only)
            for prompt_field in ["prompt", "negative_prompt"]:
                if prompt_field in params and "||" in params[prompt_field]:
                    new_result_list = []
                    for param_set in result_list:
                        sub_prompts = self._expand_subprompts(param_set[prompt_field])
                        for sub_prompt in sub_prompts:
                            new_param_set = param_set.copy()
                            new_param_set[prompt_field] = sub_prompt
                            new_result_list.append(new_param_set)
                    result_list = new_result_list

            # Handle token and range expansion for all parameters
            # We need to process all parameters for each result set
            all_param_keys = list(params.keys())
            for key in all_param_keys:
                if key not in result_list[0]:  # Skip if key doesn't exist in results
                    continue

                sample_value = result_list[0][key]
                if not isinstance(sample_value, str):
                    continue

                # Don't skip - we need to process tokens even after sub-prompt expansion

                # Check for token expansion [red,blue,green]
                if "[" in str(sample_value) and "]" in str(sample_value):
                    new_result_list = []
                    for param_set in result_list:
                        if key in param_set and isinstance(param_set[key], str):
                            expanded_values = self._expand_tokens(param_set[key])
                            for expanded_value in expanded_values:
                                new_param_set = param_set.copy()
                                new_param_set[key] = expanded_value
                                new_result_list.append(new_param_set)
                                # Check expansion limits
                                if len(new_result_list) > self.max_items:
                                    raise ExpansionError(
                                        f"Parameter expansion would create more than "
                                        f"{self.max_items} OrderItems"
                                    )
                    result_list = new_result_list

                # Check for range expansion 10..20
                elif ".." in str(sample_value):
                    new_result_list = []
                    for param_set in result_list:
                        if key in param_set and isinstance(param_set[key], str):
                            expanded_values = self._expand_ranges(param_set[key])
                            for expanded_value in expanded_values:
                                new_param_set = param_set.copy()
                                new_param_set[key] = expanded_value
                                new_result_list.append(new_param_set)
                                # Check expansion limits
                                if len(new_result_list) > self.max_items:
                                    raise ExpansionError(
                                        f"Parameter expansion would create more than "
                                        f"{self.max_items} OrderItems"
                                    )
                    result_list = new_result_list

            # Final check for limits
            if len(result_list) > self.max_items:
                raise ExpansionError(
                    f"Parameter expansion would create {len(result_list)} "
                    f"OrderItems, which exceeds the limit of {self.max_items}"
                )

            return result_list

        except ExpansionError:
            raise
        except Exception as e:
            raise ExpansionError(f"Parameter expansion failed: {str(e)}")

    def _expand_tokens(self, value: str) -> List[str]:
        """
        Expand [red,blue,green] syntax into individual values.

        Args:
            value: String potentially containing token syntax

        Returns:
            List of expanded strings

        Raises:
            ExpansionError: If token syntax is invalid
        """
        # Find all token patterns [...]
        pattern = r"\[([^\]]*)\]"  # Allow empty content for better error handling
        matches = re.findall(pattern, value)

        if not matches:
            return [value]

        # For multiple token groups, we need to handle combinations
        # For now, expand the first token group found
        # TODO: Future enhancement could handle multiple token groups

        token_content = matches[0]

        # Handle empty tokens
        if not token_content or not token_content.strip():
            raise ExpansionError(f"Empty token expansion in: {value}")

        token_values = [v.strip() for v in token_content.split(",")]

        # Filter out empty values and validate
        token_values = [v for v in token_values if v]
        if not token_values:
            raise ExpansionError(f"Empty token expansion in: {value}")

        # Replace the first token group with each value
        full_pattern = r"\[" + re.escape(token_content) + r"\]"
        result = []
        for token_value in token_values:
            expanded = re.sub(full_pattern, token_value, value, count=1)
            result.append(expanded)

        return result

    def _expand_ranges(self, value: str) -> List[Union[int, float, str]]:
        """
        Expand 10..20 syntax with step size 1.

        Args:
            value: String potentially containing range syntax

        Returns:
            List of expanded values

        Raises:
            ExpansionError: If range syntax is invalid
        """
        # Check if the entire value is a range
        range_pattern = r"^(\d+(?:\.\d+)?)\.\.(\d+(?:\.\d+)?)$"
        match = re.match(range_pattern, value.strip())

        if not match:
            return [value]  # Not a range, return as-is

        start_str, end_str = match.groups()

        try:
            # Determine if we're dealing with integers or floats
            if "." in start_str or "." in end_str:
                start = float(start_str)
                end = float(end_str)
                step = 1.0
            else:
                start = int(start_str)
                end = int(end_str)
                step = 1

            if start > end:
                raise ExpansionError(f"Invalid range: start ({start}) > end ({end})")

            # Generate range with step size 1
            result = []
            current = start
            while current <= end:
                if isinstance(current, float):
                    result.append(current)
                    current += step
                else:
                    result.append(current)
                    current += step

            return result

        except ValueError as e:
            raise ExpansionError(f"Invalid range values in: {value} ({str(e)})")

    def _expand_subprompts(self, prompt: str) -> List[str]:
        """
        Split prompt on || delimiter for sub-prompt expansion.

        Args:
            prompt: Prompt string potentially containing || delimiters

        Returns:
            List of individual prompts
        """
        if "||" not in prompt:
            return [prompt]

        sub_prompts = [p.strip() for p in prompt.split("||")]
        return [p for p in sub_prompts if p]  # Remove empty prompts

    # Validation helpers

    def _is_valid_token_syntax(self, value: str) -> bool:
        """Check if token expansion syntax is valid."""
        pattern = r"\[[^\]]+\]"
        matches = re.findall(pattern, value)

        for match in matches:
            # Remove brackets and check content
            content = match[1:-1]
            if not content or not content.strip():
                return False
            # Check that it contains comma-separated values
            values = [v.strip() for v in content.split(",")]
            if len(values) < 2:  # Must have at least 2 values
                return False

        return True

    def _is_valid_range_syntax(self, value: str) -> bool:
        """Check if range expansion syntax is valid."""
        pattern = r"^\d+(?:\.\d+)?\.\.(\d+(?:\.\d+)?)$"
        return bool(re.match(pattern, value.strip()))

    def _analyze_expansion_types(self, params: Dict[str, Any]) -> Dict[str, bool]:
        """Analyze what types of expansion are present in parameters."""
        has_tokens = any("[" in str(v) and "]" in str(v) for v in params.values())
        has_ranges = any(".." in str(v) for v in params.values())
        has_subprompts = "||" in params.get("prompt", "") or "||" in params.get("negative_prompt", "")

        return {
            "has_tokens": has_tokens,
            "has_ranges": has_ranges,
            "has_subprompts": has_subprompts
        }
