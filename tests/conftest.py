"""
conftest.py — Shared pytest fixtures for PrimeTrade AI test suite.

Provides reusable mock objects, DataFrames, and directory helpers used
across unit and integration tests. Import via pytest's automatic fixture
discovery (no explicit import needed in test files).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Directory Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture()
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory tree mirroring the real one."""
    (tmp_path / "raw").mkdir()
    (tmp_path / "processed").mkdir()
    (tmp_path / "uploads").mkdir()
    (tmp_path / "exports").mkdir()
    return tmp_path


@pytest.fixture()
def tmp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary outputs directory for charts/reports."""
    (tmp_path / "charts").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "strategy").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# Sample DataFrames
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_trader_df() -> pd.DataFrame:
    """Return a minimal, clean trader history DataFrame."""
    np.random.seed(42)
    n = 100
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    sides = ["BUY", "SELL"]

    df = pd.DataFrame(
        {
            "account": [f"ACC_{i:03d}" for i in range(n)],
            "symbol": np.random.choice(symbols, n),
            "side": np.random.choice(sides, n),
            "size": np.round(np.random.uniform(0.01, 5.0, n), 4),
            "execution_price": np.round(np.random.uniform(20_000, 70_000, n), 2),
            "closed_pnl": np.round(np.random.uniform(-500, 1000, n), 4),
            "timestamp": pd.date_range(start="2024-01-01", periods=n, freq="6h"),
        }
    )
    df["trade_value"] = df["size"] * df["execution_price"]
    df["is_profit"] = df["closed_pnl"] > 0
    df["cumulative_pnl"] = df["closed_pnl"].cumsum()
    df["direction"] = df["side"].map({"BUY": 1, "SELL": -1})
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.day
    df["weekday"] = df["timestamp"].dt.weekday
    df["month"] = df["timestamp"].dt.month
    df["week"] = df["timestamp"].dt.isocalendar().week.astype(int)
    return df


@pytest.fixture()
def sample_fear_greed_df() -> pd.DataFrame:
    """Return a minimal, clean Fear & Greed Index DataFrame."""
    np.random.seed(0)
    dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
    values = np.random.randint(0, 100, len(dates))

    def classify(v: int) -> str:
        if v <= 24:
            return "Extreme Fear"
        elif v <= 44:
            return "Fear"
        elif v <= 55:
            return "Neutral"
        elif v <= 74:
            return "Greed"
        return "Extreme Greed"

    return pd.DataFrame(
        {
            "timestamp": dates,
            "value": values,
            "classification": [classify(v) for v in values],
        }
    )


@pytest.fixture()
def sample_merged_df(sample_trader_df: pd.DataFrame, sample_fear_greed_df: pd.DataFrame) -> pd.DataFrame:
    """Return a merged trader + sentiment DataFrame."""
    fg = sample_fear_greed_df.copy()
    fg["date"] = fg["timestamp"].dt.normalize()
    trader = sample_trader_df.copy()
    trader["date"] = trader["timestamp"].dt.normalize()
    merged = pd.merge_asof(
        trader.sort_values("date"),
        fg[["date", "value", "classification"]].sort_values("date"),
        on="date",
        direction="nearest",
    )
    return merged.rename(columns={"value": "fg_value", "classification": "fg_classification"})


# ---------------------------------------------------------------------------
# CSV / File Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def trader_csv_file(tmp_data_dir: Path, sample_trader_df: pd.DataFrame) -> Path:
    """Write a trader CSV to the temp raw directory and return its path."""
    path = tmp_data_dir / "raw" / "historical_data.csv"
    sample_trader_df.to_csv(path, index=False)
    return path


@pytest.fixture()
def fear_greed_csv_file(tmp_data_dir: Path, sample_fear_greed_df: pd.DataFrame) -> Path:
    """Write a fear & greed CSV to the temp raw directory and return its path."""
    path = tmp_data_dir / "raw" / "fear_greed_index.csv"
    sample_fear_greed_df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Mock Binance Client
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_binance_client() -> MagicMock:
    """Return a fully configured mock Binance Futures client."""
    client = MagicMock()

    # Account & balance
    client.futures_account_balance.return_value = [{"asset": "USDT", "balance": "10000.00", "withdrawAvailable": "8500.00"}]
    client.futures_account.return_value = {
        "totalWalletBalance": "10000.00",
        "totalUnrealizedProfit": "150.00",
        "maxWithdrawAmount": "8500.00",
    }

    # Exchange info
    client.futures_exchange_info.return_value = {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.10"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.001", "minQty": "0.001"},
                    {"filterType": "MIN_NOTIONAL", "notional": "5.0"},
                ],
            }
        ]
    }

    # Leverage
    client.futures_change_leverage.return_value = {
        "symbol": "BTCUSDT",
        "leverage": 10,
        "maxNotionalValue": "1000000",
    }

    # Order submission
    client.futures_create_order.return_value = {
        "orderId": 99999,
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "executedQty": "0.001",
        "cumQuote": "45.00",
        "avgPrice": "45000.00",
        "side": "BUY",
        "type": "MARKET",
        "timeInForce": "GTC",
        "updateTime": 1700000000000,
    }

    # Open orders & positions
    client.futures_get_open_orders.return_value = []
    client.futures_position_information.return_value = [
        {
            "symbol": "BTCUSDT",
            "positionAmt": "0.001",
            "entryPrice": "45000.00",
            "markPrice": "45100.00",
            "unRealizedProfit": "0.10",
            "liquidationPrice": "22500.00",
            "leverage": "10",
            "marginType": "cross",
            "isolatedMargin": "0.00",
            "maintMargin": "0.54",
        }
    ]
    client.futures_cancel_order.return_value = {"orderId": 99999, "status": "CANCELED"}

    return client


# ---------------------------------------------------------------------------
# Environment Variable Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=False)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch environment variables for testing without real credentials."""
    monkeypatch.setenv("BINANCE_API_KEY", "test_api_key_123")
    monkeypatch.setenv("BINANCE_SECRET_KEY", "test_secret_key_456")
    monkeypatch.setenv("PROJECT_ENV", "DEVELOPMENT")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("DEFAULT_LEVERAGE", "10")
    monkeypatch.setenv("MAX_LEVERAGE", "20")
    monkeypatch.setenv("MAX_DRAWDOWN_PCT", "15.0")
    monkeypatch.setenv("MAX_CAPITAL_AT_RISK_PCT", "50.0")
    monkeypatch.setenv("MAX_SINGLE_TRADE_PCT", "10.0")
