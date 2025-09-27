"""
Parameter validation utilities for factories.
"""

import re
from typing import Dict, List, Any, Union, Optional
import logging

from .base import ValidationResult


logger = logging.getLogger(__name__)


class ParameterValidator:
    """Advanced parameter validation utilities."""

    # Token expansion pattern: [red,blue,green] or [color]
    TOKEN_PATTERN = re.compile(r"\[([^\[\]]+)\]")

    # Range interpolation pattern: steps:10..20 or guidance:7.5..12.5:0.5
    RANGE_PATTERN = re.compile(
        r"^(\w+):(-?\d+(?:\.\d+)?)\.\.(-?\d+(?:\.\d+)?)(?::(-?\d+(?:\.\d+)?))?$"
    )

    # Sub-prompt pattern: "prompt1 || prompt2"
    SUBPROMPT_PATTERN = re.compile(r"\|\|")

    @classmethod
    def validate_token_expansion(cls, value: str) -> List[str]:
        """Validate and extract token expansion values.

        Args:
            value: String that may contain [token] syntax

        Returns:
            List of possible expansion values

        Example:
            "[red,blue,green] car" -> ["red car", "blue car", "green car"]
        """
        if not isinstance(value, str):
            return [str(value)]

        # Find all token patterns
        tokens = cls.TOKEN_PATTERN.findall(value)
        if not tokens:
            return [value]

        # Check for nested brackets first
        bracket_depth = 0
        for char in value:
            if char == "[":
                bracket_depth += 1
                if bracket_depth > 1:
                    raise ValueError("Nested brackets are not allowed")
            elif char == "]":
                bracket_depth -= 1

        # For now, just validate the syntax and return original
        # Full expansion logic remains in OrderService
        for token in tokens:
            # Validate token format
            if "," in token:
                # Inline values: [red,blue,green]
                values = [v.strip() for v in token.split(",")]
                if not all(values):  # Check for empty values
                    raise ValueError(f"Empty token value in [{token}]")
            else:
                # Lookup reference: [color]
                # For now, just validate it's a valid identifier
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", token.strip()):
                    raise ValueError(f"Invalid token name: [{token}]")

        return [value]  # Return original for now

    @classmethod
    def validate_range_interpolation(cls, value: str) -> List[Union[int, float]]:
        """Validate and extract range interpolation values.

        Args:
            value: String in format "param:start..end" or "param:start..end:step"

        Returns:
            List of interpolated values

        Example:
            "steps:10..15" -> [10, 11, 12, 13, 14, 15]
            "guidance:7.5..8.5:0.5" -> [7.5, 8.0, 8.5]
        """
        if not isinstance(value, str):
            return [value]

        match = cls.RANGE_PATTERN.match(value.strip())
        if not match:
            return [value]  # Not a range pattern

        param_name, start_str, end_str, step_str = match.groups()

        try:
            # Determine if we're dealing with integers or floats
            if "." in start_str or "." in end_str or (step_str and "." in step_str):
                start = float(start_str)
                end = float(end_str)
                step = float(step_str) if step_str else 1.0
            else:
                start = int(start_str)
                end = int(end_str)
                step = int(step_str) if step_str else 1

            # Validate range
            if start > end:
                raise ValueError(
                    f"Range start ({start}) cannot be greater than end ({end})"
                )

            if step <= 0:
                raise ValueError(f"Range step ({step}) must be positive")

            # Generate values (for validation - actual expansion in OrderService)
            values = []
            current = start
            while current <= end:
                values.append(current)
                current += step

            return values

        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid range format '{value}': {e}")

    @classmethod
    def validate_subprompt_syntax(cls, prompt: str) -> List[str]:
        """Validate and extract sub-prompt values.

        Args:
            prompt: String that may contain "prompt1 || prompt2" syntax

        Returns:
            List of sub-prompts

        Example:
            "dog || cat" -> ["dog", "cat"]
        """
        if not isinstance(prompt, str):
            return [str(prompt)]

        if not cls.SUBPROMPT_PATTERN.search(prompt):
            return [prompt]

        # Split on || and clean up
        subprompts = [p.strip() for p in prompt.split("||")]

        # Validate that we don't have empty prompts
        if not all(subprompts):
            raise ValueError("Empty sub-prompt found in prompt expansion")

        return subprompts

    @classmethod
    def validate_expansion_syntax(cls, params: Dict[str, Any]) -> ValidationResult:
        """Validate expansion syntax in all string parameters.

        Args:
            params: Parameters to validate

        Returns:
            ValidationResult with any syntax errors
        """
        result = ValidationResult(is_valid=True)

        for key, value in params.items():
            if not isinstance(value, str):
                continue

            try:
                # Check token expansion syntax
                cls.validate_token_expansion(value)

                # Check range interpolation syntax
                cls.validate_range_interpolation(value)

                # Check sub-prompt syntax
                cls.validate_subprompt_syntax(value)

            except ValueError as e:
                result.add_error(key, f"Invalid expansion syntax: {e}")

        return result

    @classmethod
    def estimate_expansion_count(cls, params: Dict[str, Any]) -> int:
        """Estimate the number of items that would be created from expansion.

        Args:
            params: Parameters to analyze

        Returns:
            Estimated number of expanded items
        """
        total_count = 1

        for key, value in params.items():
            if not isinstance(value, str):
                continue

            param_multiplier = 1

            # Count token expansions
            tokens = cls.TOKEN_PATTERN.findall(value)
            for token in tokens:
                if "," in token:
                    # Inline values
                    token_count = len(
                        [v.strip() for v in token.split(",") if v.strip()]
                    )
                    param_multiplier *= token_count

            # Count range interpolations (only if it's the whole value)
            if cls.RANGE_PATTERN.match(value.strip()):
                try:
                    range_values = cls.validate_range_interpolation(value)
                    param_multiplier *= len(range_values)
                except ValueError:
                    pass  # Skip invalid ranges

            # Count sub-prompts
            if cls.SUBPROMPT_PATTERN.search(value):
                try:
                    subprompts = cls.validate_subprompt_syntax(value)
                    param_multiplier *= len(subprompts)
                except ValueError:
                    pass  # Skip invalid sub-prompts

            total_count *= param_multiplier

        return total_count

    @classmethod
    def validate_prompt_format(cls, prompt: str, result: ValidationResult) -> None:
        """Validate prompt format and add issues to result.

        Args:
            prompt: Prompt string to validate
            result: ValidationResult to add issues to
        """
        if not prompt or not prompt.strip():
            result.add_error("prompt", "Prompt cannot be empty")
            return

        # Check for balanced brackets
        bracket_count = prompt.count("[") - prompt.count("]")
        if bracket_count != 0:
            result.add_error("prompt", "Unbalanced brackets in prompt")

        # Check for extremely long prompts
        if len(prompt) > 2000:
            result.add_warning(
                "prompt", f"Prompt is very long ({len(prompt)} characters)"
            )

        # Check for suspicious patterns
        if prompt.count("||") > 10:
            result.add_warning(
                "prompt",
                "Many sub-prompts detected - this may create a large number of generations",
            )

    @classmethod
    def validate_numeric_range(
        cls,
        value: Union[int, float],
        param_name: str,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        result: ValidationResult = None,
    ) -> ValidationResult:
        """Validate a numeric value is within specified range.

        Args:
            value: Value to validate
            param_name: Parameter name for error messages
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            result: Existing ValidationResult to add to (creates new if None)

        Returns:
            ValidationResult with any range violations
        """
        if result is None:
            result = ValidationResult(is_valid=True)

        if min_val is not None and value < min_val:
            result.add_error(param_name, f"Value {value} is below minimum {min_val}")

        if max_val is not None and value > max_val:
            result.add_error(param_name, f"Value {value} is above maximum {max_val}")

        return result
