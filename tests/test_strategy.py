"""Unit and integration tests for the Strategy Recommendation Engine."""

from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from analytics.strategy.base_strategy import BaseStrategy
from analytics.strategy.rule_based import RuleBasedStrategy, StrategyConfig, StrategyRecommendation
from analytics.strategy.strategy_engine import StrategyEngine
from config.enums import StrategyAction


# Concrete implementation of BaseStrategy for testing base helper methods
class DummyStrategy(BaseStrategy):
    """Dummy strategy implementation to test BaseStrategy helper methods."""

    def generate_recommendation(self, df: pd.DataFrame, current_sentiment_val: Optional[float] = None) -> dict:
        return {}


@pytest.fixture
def base_strategy():
    """Returns a dummy strategy for helper method testing."""
    return DummyStrategy(name="Dummy Strategy")


@pytest.fixture
def mock_trades_df():
    """Generates a standard mock trade history dataframe."""
    base_time = datetime(2026, 6, 20, 12, 0, 0)
    timestamps = [base_time + timedelta(hours=i) for i in range(20)]
    closed_pnls = [
        100.0,
        -50.0,
        200.0,
        -100.0,
        150.0,
        -50.0,
        50.0,
        -20.0,
        120.0,
        80.0,
        -30.0,
        110.0,
        90.0,
        -60.0,
        -40.0,
        200.0,
        150.0,
        -50.0,
        120.0,
        100.0,
    ]

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "closed_pnl": closed_pnls,
            "size": [0.1] * 20,
            "execution_price": [30000.0 + i * 100 for i in range(20)],
            "is_profit": [1 if p > 0 else 0 for p in closed_pnls],
            "value": [50.0] * 20,  # Neutral sentiment F&G
        }
    )
    df["cumulative_pnl"] = df["closed_pnl"].cumsum()
    return df


def test_base_strategy_helpers(base_strategy, mock_trades_df):
    """Verifies that the base strategy helper functions compute metrics correctly."""
    # 1. Test drawdown
    # Initial balance 10,000. Max cumulative PnL starts at 100, drops, rises to peak.
    # Cumulative PnL series: [100, 50, 250, 150, 300, 250, 300, 280, 400, 480, 450, 560, 650, 590, 550, 750, 900, 850, 970, 1070]
    # Let's check drawdown calculation
    dd_metrics = base_strategy.calculate_drawdown(mock_trades_df, initial_balance=10000.0)
    assert "current_drawdown" in dd_metrics
    assert "max_drawdown" in dd_metrics
    assert dd_metrics["current_drawdown"] == 0.0  # Ending at a peak PnL
    assert dd_metrics["max_drawdown"] > 0.0

    # 2. Test rolling win rate
    win_rate = base_strategy.calculate_rolling_win_rate(mock_trades_df, window=10)
    # Last 10 trades: -30, 110, 90, -60, -40, 200, 150, -50, 120, 100
    # Wins: 110, 90, 200, 150, 120, 100 (6 wins out of 10)
    assert win_rate == 0.60

    # 3. Test trade frequency
    # 20 trades over 20 hours = 24 trades per day
    freq = base_strategy.calculate_trade_frequency(mock_trades_df, window_days=1)
    assert freq > 0.0

    # 4. Test volatility
    vol = base_strategy.calculate_volatility(mock_trades_df, window=5)
    assert vol > 0.0


def test_rule_based_strategy_empty():
    """Verifies that an empty dataframe results in a HOLD action."""
    strategy = RuleBasedStrategy()
    empty_df = pd.DataFrame()
    rec = strategy.generate_recommendation(empty_df)
    assert rec["action"] == StrategyAction.HOLD
    assert rec["confidence_score"] == 0.50
    assert "No trade history available" in rec["explanations"][0]


def test_rule_based_strategy_hold(mock_trades_df):
    """Verifies standard neutral state produces a HOLD recommendation."""
    config = StrategyConfig(overtrading_frequency_limit=100.0)
    strategy = RuleBasedStrategy(config=config)
    rec = strategy.generate_recommendation(mock_trades_df, current_sentiment_val=40.0)
    assert rec["action"] == StrategyAction.HOLD
    assert rec["confidence_score"] == 0.60
    assert "neutral" in rec["explanations"][0].lower()


def test_rule_based_strategy_avoid_trading_drawdown(mock_trades_df):
    """Verifies that high drawdown triggers AVOID TRADING."""
    # Modify data to simulate a huge drawdown
    bad_df = mock_trades_df.copy()
    # Peak is at index 2 (cumulative = 250)
    # Introduce massive loss at index 3
    bad_df.loc[3:, "closed_pnl"] = -2000.0
    bad_df["cumulative_pnl"] = bad_df["closed_pnl"].cumsum()

    strategy = RuleBasedStrategy(config=StrategyConfig(max_drawdown_threshold=0.10, initial_balance=10000.0))
    rec = strategy.generate_recommendation(bad_df, current_sentiment_val=50.0)
    assert rec["action"] == StrategyAction.AVOID_TRADING
    assert any("drawdown" in exp.lower() for exp in rec["explanations"])


def test_rule_based_strategy_avoid_trading_win_rate(mock_trades_df):
    """Verifies that critically low win rate triggers AVOID TRADING."""
    # Force consecutive losses in the last 10 rows
    bad_df = mock_trades_df.copy()
    bad_df.loc[10:, "closed_pnl"] = -5.0
    bad_df.loc[10:, "is_profit"] = 0
    bad_df["cumulative_pnl"] = bad_df["closed_pnl"].cumsum()

    strategy = RuleBasedStrategy(config=StrategyConfig(rolling_window=10))
    rec = strategy.generate_recommendation(bad_df, current_sentiment_val=50.0)
    assert rec["action"] == StrategyAction.AVOID_TRADING
    assert any("win rate" in exp.lower() for exp in rec["explanations"])


def test_rule_based_strategy_avoid_trading_frequency(mock_trades_df):
    """Verifies that overtrading frequency triggers AVOID TRADING."""
    # Create config with low frequency limit
    config = StrategyConfig(overtrading_frequency_limit=1.0, frequency_window_days=7)
    strategy = RuleBasedStrategy(config=config)
    # The mock trades df contains 20 trades in 20 hours (less than 1 day)
    rec = strategy.generate_recommendation(mock_trades_df, current_sentiment_val=50.0)
    assert rec["action"] == StrategyAction.AVOID_TRADING
    assert any("frequency" in exp.lower() or "overtrading" in exp.lower() for exp in rec["explanations"])


def test_rule_based_strategy_reduce_leverage(mock_trades_df):
    """Verifies that moderately low win rate or drawdown triggers REDUCE LEVERAGE."""
    # Set rolling win rate to 40% (4 wins in last 10)
    df = mock_trades_df.copy()
    df.loc[10:, "is_profit"] = [0, 0, 1, 0, 0, 1, 1, 0, 1, 0]
    df.loc[10:, "closed_pnl"] = [-10.0 if w == 0 else 10.0 for w in df.loc[10:, "is_profit"]]
    df["cumulative_pnl"] = df["closed_pnl"].cumsum()

    config = StrategyConfig(min_rolling_win_rate=0.45, rolling_window=10, overtrading_frequency_limit=100.0)
    strategy = RuleBasedStrategy(config=config)
    rec = strategy.generate_recommendation(df, current_sentiment_val=50.0)
    assert rec["action"] == StrategyAction.REDUCE_LEVERAGE
    assert any("win rate" in exp.lower() for exp in rec["explanations"])


def test_rule_based_strategy_buy_extreme_fear(mock_trades_df):
    """Verifies that Extreme Fear sentiment generates a BUY recommendation."""
    # Ensure trade frequency is high enough not to trigger overtrading check
    config = StrategyConfig(overtrading_frequency_limit=100.0)
    strategy = RuleBasedStrategy(config=config)
    rec = strategy.generate_recommendation(mock_trades_df, current_sentiment_val=15.0)
    assert rec["action"] == StrategyAction.BUY
    assert rec["confidence_score"] >= 0.70
    assert any("extreme fear" in exp.lower() for exp in rec["explanations"])


def test_rule_based_strategy_sell_extreme_greed(mock_trades_df):
    """Verifies that Extreme Greed sentiment generates a SELL recommendation."""
    config = StrategyConfig(overtrading_frequency_limit=100.0)
    strategy = RuleBasedStrategy(config=config)
    rec = strategy.generate_recommendation(mock_trades_df, current_sentiment_val=85.0)
    assert rec["action"] == StrategyAction.SELL
    assert rec["confidence_score"] >= 0.70
    assert any("extreme greed" in exp.lower() for exp in rec["explanations"])


def test_rule_based_strategy_increase_position(mock_trades_df):
    """Verifies that high win rate and low drawdown generates INCREASE POSITION SIZE recommendation."""
    # Ensure high win rate (last 10 trades all wins)
    df = mock_trades_df.copy()
    df.loc[10:, "is_profit"] = 1
    df.loc[10:, "closed_pnl"] = 50.0
    df["cumulative_pnl"] = df["closed_pnl"].cumsum()

    config = StrategyConfig(initial_balance=10000.0, overtrading_frequency_limit=100.0)
    strategy = RuleBasedStrategy(config=config)
    rec = strategy.generate_recommendation(df, current_sentiment_val=60.0)
    assert rec["action"] == StrategyAction.INCREASE_POSITION_SIZE
    assert rec["confidence_score"] == 0.85
    assert any("compound" in exp.lower() or "sizing" in exp.lower() for exp in rec["explanations"])


def test_strategy_engine_runs_and_exports(tmp_path, mock_trades_df):
    """Verifies that StrategyEngine executes strategies and successfully exports files."""
    # Mock output directory to pytest's tmp_path
    with patch("analytics.strategy.strategy_engine.STRATEGY_OUTPUT_DIR", tmp_path):
        config = StrategyConfig(overtrading_frequency_limit=100.0)
        engine = StrategyEngine(strategies=[RuleBasedStrategy(config=config)])

        # Run strategy analysis
        recommendations = engine.run_strategy_analysis(df=mock_trades_df, current_sentiment_val=40.0, export_outputs=True)

        assert "Rule-Based Sentiment & Risk Strategy" in recommendations

        # Verify exported files
        json_file = tmp_path / "recommendations.json"
        csv_file = tmp_path / "recommendations.csv"
        md_file = tmp_path / "recommendations.md"

        assert json_file.exists()
        assert csv_file.exists()
        assert md_file.exists()

        # Check JSON content
        import json

        with open(json_file, "r") as f:
            data = json.load(f)
            assert "Rule-Based Sentiment & Risk Strategy" in data
            assert data["Rule-Based Sentiment & Risk Strategy"]["action"] == "HOLD"
