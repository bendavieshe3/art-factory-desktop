"""
Tests for factory validation utilities.
"""

import pytest

from app.factories.validation import ParameterValidator
from app.factories.base import ValidationResult


class TestParameterValidator:
    """Test ParameterValidator utilities."""

    def test_validate_token_expansion_success(self):
        """Test successful token expansion validation."""
        # Inline values
        values = ParameterValidator.validate_token_expansion("[red,blue,green] car")
        assert len(values) == 1  # Returns original for now

        # Lookup reference
        values = ParameterValidator.validate_token_expansion("[color] car")
        assert len(values) == 1

        # No tokens
        values = ParameterValidator.validate_token_expansion("simple prompt")
        assert values == ["simple prompt"]

    def test_validate_token_expansion_errors(self):
        """Test token expansion validation errors."""
        # Empty token value
        with pytest.raises(ValueError) as exc_info:
            ParameterValidator.validate_token_expansion("[red,,blue]")
        assert "Empty token value" in str(exc_info.value)

        # Invalid lookup name
        with pytest.raises(ValueError) as exc_info:
            ParameterValidator.validate_token_expansion("[123invalid]")
        assert "Invalid token name" in str(exc_info.value)

    def test_validate_range_interpolation_success(self):
        """Test successful range interpolation validation."""
        # Integer range
        values = ParameterValidator.validate_range_interpolation("steps:10..15")
        assert values == [10, 11, 12, 13, 14, 15]

        # Float range
        values = ParameterValidator.validate_range_interpolation(
            "guidance:7.5..8.5:0.5"
        )
        assert values == [7.5, 8.0, 8.5]

        # Not a range
        values = ParameterValidator.validate_range_interpolation("normal_value")
        assert values == ["normal_value"]

    def test_validate_range_interpolation_errors(self):
        """Test range interpolation validation errors."""
        # Start > end
        with pytest.raises(ValueError) as exc_info:
            ParameterValidator.validate_range_interpolation("steps:20..10")
        assert "start" in str(exc_info.value) and "greater than end" in str(
            exc_info.value
        )

        # Negative step
        with pytest.raises(ValueError) as exc_info:
            ParameterValidator.validate_range_interpolation("steps:10..20:-1")
        assert "step" in str(exc_info.value) and "positive" in str(exc_info.value)

        # Zero step
        with pytest.raises(ValueError) as exc_info:
            ParameterValidator.validate_range_interpolation("steps:10..20:0")
        assert "step" in str(exc_info.value) and "positive" in str(exc_info.value)

    def test_validate_subprompt_syntax_success(self):
        """Test successful sub-prompt validation."""
        # Multiple sub-prompts
        prompts = ParameterValidator.validate_subprompt_syntax("dog || cat || bird")
        assert prompts == ["dog", "cat", "bird"]

        # Single prompt (no expansion)
        prompts = ParameterValidator.validate_subprompt_syntax("single prompt")
        assert prompts == ["single prompt"]

        # Prompts with whitespace
        prompts = ParameterValidator.validate_subprompt_syntax(" dog  || cat ")
        assert prompts == ["dog", "cat"]

    def test_validate_subprompt_syntax_errors(self):
        """Test sub-prompt validation errors."""
        # Empty sub-prompt
        with pytest.raises(ValueError) as exc_info:
            ParameterValidator.validate_subprompt_syntax("dog || || cat")
        assert "Empty sub-prompt" in str(exc_info.value)

    def test_validate_expansion_syntax_combined(self):
        """Test validation of combined expansion syntax."""
        params = {
            "prompt": "[red,blue] car with steps:10..20",
            "guidance": "7.5..8.5:0.5",
            "negative": "bad || ugly",
            "normal": "regular parameter",
        }

        result = ParameterValidator.validate_expansion_syntax(params)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_expansion_syntax_errors(self):
        """Test expansion syntax validation with errors."""
        params = {
            "bad_token": "[red,,blue]",  # Empty token
            "bad_range": "steps:20..10",  # Invalid range
            "bad_subprompt": "dog || || cat",  # Empty sub-prompt
        }

        result = ParameterValidator.validate_expansion_syntax(params)
        assert not result.is_valid
        assert len(result.errors) == 3

    def test_estimate_expansion_count_simple(self):
        """Test expansion count estimation for simple cases."""
        # No expansion
        params = {"prompt": "simple prompt"}
        count = ParameterValidator.estimate_expansion_count(params)
        assert count == 1

        # Token expansion
        params = {"prompt": "[red,blue,green] car"}
        count = ParameterValidator.estimate_expansion_count(params)
        assert count == 3

        # Range expansion
        params = {"steps": "steps:10..12"}
        count = ParameterValidator.estimate_expansion_count(params)
        assert count == 3  # 10, 11, 12

    def test_estimate_expansion_count_combined(self):
        """Test expansion count estimation for combined expansions."""
        params = {
            "prompt": "[red,blue] car",  # 2 options
            "steps": "steps:10..11",  # 2 options
            "negative": "bad || ugly",  # 2 options
        }
        count = ParameterValidator.estimate_expansion_count(params)
        assert count == 8  # 2 * 2 * 2

    def test_validate_prompt_format(self):
        """Test prompt format validation."""
        result = ValidationResult(is_valid=True)

        # Valid prompt
        ParameterValidator.validate_prompt_format("A nice prompt", result)
        assert result.is_valid
        assert len(result.errors) == 0

        # Empty prompt
        result = ValidationResult(is_valid=True)
        ParameterValidator.validate_prompt_format("", result)
        assert not result.is_valid
        assert any("empty" in e.message.lower() for e in result.errors)

        # Unbalanced brackets
        result = ValidationResult(is_valid=True)
        ParameterValidator.validate_prompt_format("prompt with [unbalanced", result)
        assert not result.is_valid
        assert any("bracket" in e.message.lower() for e in result.errors)

        # Very long prompt
        result = ValidationResult(is_valid=True)
        long_prompt = "x" * 2500
        ParameterValidator.validate_prompt_format(long_prompt, result)
        assert result.is_valid  # Still valid but with warning
        assert len(result.warnings) > 0
        assert any("long" in w.message.lower() for w in result.warnings)

        # Many sub-prompts
        result = ValidationResult(is_valid=True)
        many_subprompts = " || ".join(["prompt"] * 15)
        ParameterValidator.validate_prompt_format(many_subprompts, result)
        assert result.is_valid  # Still valid but with warning
        assert len(result.warnings) > 0

    def test_validate_numeric_range(self):
        """Test numeric range validation."""
        # Valid range
        result = ParameterValidator.validate_numeric_range(50, "steps", 1, 100)
        assert result.is_valid

        # Below minimum
        result = ParameterValidator.validate_numeric_range(0, "steps", 1, 100)
        assert not result.is_valid
        assert "below minimum" in result.errors[0].message

        # Above maximum
        result = ParameterValidator.validate_numeric_range(150, "steps", 1, 100)
        assert not result.is_valid
        assert "above maximum" in result.errors[0].message

        # No constraints
        result = ParameterValidator.validate_numeric_range(999, "steps")
        assert result.is_valid

        # Add to existing result
        existing_result = ValidationResult(is_valid=True)
        result = ParameterValidator.validate_numeric_range(
            150, "steps", 1, 100, existing_result
        )
        assert result is existing_result
        assert not result.is_valid

    def test_non_string_parameters(self):
        """Test validation with non-string parameters."""
        # Should handle non-string values gracefully
        values = ParameterValidator.validate_token_expansion(123)
        assert values == ["123"]

        values = ParameterValidator.validate_range_interpolation(45.5)
        assert values == [45.5]

        prompts = ParameterValidator.validate_subprompt_syntax(None)
        assert prompts == ["None"]

    def test_complex_token_patterns(self):
        """Test complex token expansion patterns."""
        # Multiple tokens in one string
        text = "[red,blue] [car,truck] driving"
        # Should not crash (full expansion logic is in OrderService)
        values = ParameterValidator.validate_token_expansion(text)
        assert len(values) == 1

        # Nested brackets (should be invalid)
        with pytest.raises(ValueError):
            ParameterValidator.validate_token_expansion("[red,[blue,green]]")

    def test_edge_case_ranges(self):
        """Test edge cases for range interpolation."""
        # Single value range
        values = ParameterValidator.validate_range_interpolation("steps:10..10")
        assert values == [10]

        # Large step
        values = ParameterValidator.validate_range_interpolation("steps:10..20:15")
        assert values == [10]  # Only one value fits

        # Decimal precision
        values = ParameterValidator.validate_range_interpolation(
            "guidance:7.1..7.3:0.1"
        )
        expected = [7.1, 7.2, 7.3]
        assert len(values) == len(expected)
        # Use approximate comparison for floats
        for v, e in zip(values, expected):
            assert abs(v - e) < 0.01  # Allow for float precision
