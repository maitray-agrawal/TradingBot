"""Generic value and data validator helpers for PrimeTrade AI.

Contains validation logic for numeric ranges, string states, and floating point
decimal precision scales.
"""

from typing import Any, Union


def validate_in_range(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    name: str = "Value",
) -> None:
    """Validates that a numeric value falls within a specific range.

    Args:
        value: Numeric value to check.
        min_val: Minimum allowed boundary.
        max_val: Maximum allowed boundary.
        name: Parameter name for error reference.

    Raises:
        ValueError: If value falls outside boundaries.
    """
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} must be between {min_val} and {max_val} (inclusive). Got: {value}")


def validate_is_positive(value: Union[int, float], name: str = "Value") -> None:
    """Validates that a numeric value is strictly positive (> 0).

    Args:
        value: Numeric value to check.
        name: Parameter name for error reference.

    Raises:
        ValueError: If value is zero or negative.
    """
    if value <= 0:
        raise ValueError(f"{name} must be strictly positive. Got: {value}")


def validate_decimal_precision(val: float, max_decimals: int) -> bool:
    """Verifies if a floating point value does not exceed a maximum decimal precision.

    Args:
        val: Float value to evaluate.
        max_decimals: Maximum allowed decimal places.

    Returns:
        True if within precision limits, False otherwise.
    """
    # Convert float to string representation to parse decimal places safely
    val_str = f"{val:.12f}".rstrip("0")
    if "." not in val_str:
        return True
    decimals = len(val_str.split(".")[1])
    return decimals <= max_decimals
