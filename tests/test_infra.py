"""Unit tests for the PrimeTrade AI infrastructure (Phase 1)."""

from datetime import datetime

import pandas as pd
import pytest

from config import Environment, settings
from utils import (
    ValidationError,
    clean_column_names,
    parse_timestamp_to_datetime,
    validate_decimal_precision,
    validate_in_range,
    validate_is_positive,
)


def test_settings_loaded() -> None:
    """Verifies that default settings load with validated types."""
    assert settings.project_env in {
        Environment.DEVELOPMENT,
        Environment.STAGING,
        Environment.PRODUCTION,
    }
    assert settings.testnet_url.startswith("http")


def test_clean_column_names() -> None:
    """Verifies formatting logic of header cleaners."""
    df = pd.DataFrame(columns=["Closed PnL ($)", "Coin/Symbol", "QTY-1", "  spaced_col  "])
    cleaned_df = clean_column_names(df)
    assert list(cleaned_df.columns) == [
        "closed_pnl",
        "coinsymbol",
        "qty_1",
        "spaced_col",
    ]


def test_parse_timestamp_to_datetime() -> None:
    """Verifies parser conversions of unix values and ISO strings."""
    # Test Unix Seconds (int)
    dt1 = parse_timestamp_to_datetime(1688212800)
    assert isinstance(dt1, datetime)
    assert dt1.year == 2023

    # Test Unix Milliseconds (int)
    dt2 = parse_timestamp_to_datetime(1688212800000)
    assert isinstance(dt2, datetime)
    assert dt2.year == 2023

    # Test ISO String
    dt3 = parse_timestamp_to_datetime("2023-07-01T12:00:00")
    assert isinstance(dt3, datetime)
    assert dt3.hour == 12


def test_range_validation() -> None:
    """Verifies range checker raises errors on boundary breach."""
    # Should pass without issues
    validate_in_range(50, 0, 100)

    # Should raise error
    with pytest.raises(ValueError, match="must be between 0 and 100"):
        validate_in_range(150, 0, 100)


def test_is_positive_validation() -> None:
    """Verifies positive check raises errors on zero or negative values."""
    # Should pass
    validate_is_positive(0.01)

    # Should raise
    with pytest.raises(ValueError, match="must be strictly positive"):
        validate_is_positive(0)

    with pytest.raises(ValueError, match="must be strictly positive"):
        validate_is_positive(-10)


def test_decimal_precision() -> None:
    """Verifies decimal count scale limits."""
    assert validate_decimal_precision(1.2345, 4) is True
    assert validate_decimal_precision(1.23456, 4) is False
    assert validate_decimal_precision(100, 2) is True
