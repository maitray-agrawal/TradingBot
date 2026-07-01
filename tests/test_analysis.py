"""Test suite for the Phase 4 Analytics Engine.

Verifies calculations, edge cases, and report exports for all analysis modules.
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analytics.analysis.analytics_engine import AnalyticsEngine
from analytics.analysis.coin_analysis import CoinAnalysis
from analytics.analysis.correlation_analysis import CorrelationAnalysis
from analytics.analysis.market_analysis import MarketAnalysis
from analytics.analysis.performance_analysis import PerformanceAnalysis
from analytics.analysis.risk_analysis import RiskAnalysis
from analytics.analysis.sentiment_analysis import SentimentAnalysis
from analytics.analysis.summary_generator import SummaryGenerator
from analytics.analysis.time_analysis import TimeAnalysis
from analytics.analysis.trader_analysis import TraderAnalysis


@pytest.fixture
def sample_trade_data() -> pd.DataFrame:
    """Generates a sample DataFrame containing processed trading records."""
    data = {
        "timestamp": pd.date_range(start="2026-06-01 00:00:00", periods=5, freq="6h"),
        "symbol": ["BTCUSDT", "ETHUSDT", "BTCUSDT", "SOLUSDT", "ETHUSDT"],
        "execution_price": [60000.0, 3000.0, 61000.0, 140.0, 3100.0],
        "side": ["BUY", "BUY", "SELL", "SELL", "SELL"],
        "size": [0.1, 1.0, 0.1, 10.0, 1.0],
        "closed_pnl": [
            0.0,
            0.0,
            100.0,
            -50.0,
            100.0,
        ],  # 2 wins, 1 loss, 2 breakeven/entry
        "account_id": ["BOT-ACC-1", "BOT-ACC-1", "BOT-ACC-1", "BOT-ACC-2", "BOT-ACC-2"],
        "fg_value": [40, 45, 50, 65, 80],
        "fg_classification": ["Fear", "Neutral", "Neutral", "Greed", "Extreme Greed"],
        "fees": [1.2, 0.9, 1.3, 0.4, 0.8],
    }
    df = pd.DataFrame(data)
    # Generate engineered columns that FeatureGenerator normally creates
    df["trade_value"] = df["size"] * df["execution_price"]
    df["position_size"] = df["size"]
    df["is_profit"] = (df["closed_pnl"] > 0).astype(int)
    df["profit_percentage"] = np.where(df["trade_value"] > 0, (df["closed_pnl"] / df["trade_value"]) * 100.0, 0.0)
    df["cumulative_pnl"] = df["closed_pnl"].cumsum()
    df["rolling_pnl"] = df["closed_pnl"].rolling(window=2, min_periods=1).sum()
    df["rolling_volume"] = df["trade_value"].rolling(window=2, min_periods=1).sum()
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.weekday
    df["week"] = df["timestamp"].dt.isocalendar().week.astype(int)
    df["month"] = df["timestamp"].dt.month
    df["quarter"] = df["timestamp"].dt.quarter
    return df


def test_trader_analysis(sample_trade_data):
    """Verifies leaderboards, frequencies, and risk scores computed per trader."""
    result = TraderAnalysis.calculate_metrics(sample_trade_data)

    assert result.total_traders == 2
    assert "BOT-ACC-1" in result.unique_traders
    assert "BOT-ACC-2" in result.unique_traders

    # BOT-ACC-1 trades: [0.0, 0.0, 100.0] -> sum = 100.0
    # BOT-ACC-2 trades: [-50.0, 100.0] -> sum = 50.0
    assert result.trader_metrics["BOT-ACC-1"]["total_pnl"] == 100.0
    assert result.trader_metrics["BOT-ACC-2"]["total_pnl"] == 50.0
    assert result.top_10_traders[0]["account_id"] == "BOT-ACC-1"
    assert result.bottom_10_traders[0]["account_id"] == "BOT-ACC-2"


def test_market_analysis(sample_trade_data):
    """Verifies symbol counts and side distributions."""
    result = MarketAnalysis.calculate_metrics(sample_trade_data)

    assert result.symbol_distribution["BTCUSDT"] == 2
    assert result.symbol_distribution["ETHUSDT"] == 2
    assert result.symbol_distribution["SOLUSDT"] == 1

    assert result.side_distribution["BUY"] == 2
    assert result.side_distribution["SELL"] == 3
    assert result.buy_sell_ratio == 2 / 3
    assert result.volume_concentration_hhi > 0.0


def test_sentiment_analysis(sample_trade_data):
    """Verifies grouping of trades under Fear & Greed regimes."""
    result = SentimentAnalysis.calculate_metrics(sample_trade_data)

    # 40 -> Fear
    # 45, 50 -> Neutral
    # 75 -> Greed
    # 80 -> Extreme Greed
    assert "Fear" in result.regimes
    assert "Neutral" in result.regimes
    assert "Greed" in result.regimes
    assert "Extreme Greed" in result.regimes

    # Neutral regime has 2 trades: 100 and 0.0 closed_pnl
    assert result.regimes["Neutral"]["trade_count"] == 2
    assert result.regimes["Neutral"]["average_pnl"] == 50.0


def test_coin_analysis(sample_trade_data):
    """Verifies coin metrics calculations and rankings."""
    result = CoinAnalysis.calculate_metrics(sample_trade_data)

    assert "BTCUSDT" in result.coins
    assert "ETHUSDT" in result.coins
    assert "SOLUSDT" in result.coins

    # BTCUSDT total pnl = 100.0, ETHUSDT total pnl = 100.0, SOLUSDT total pnl = -50.0
    assert result.best_performing_coin in ("BTCUSDT", "ETHUSDT")
    assert result.worst_performing_coin == "SOLUSDT"


def test_performance_analysis(sample_trade_data):
    """Verifies aggregate win/loss counters and profit factor."""
    result = PerformanceAnalysis.calculate_metrics(sample_trade_data)

    assert result.total_trades == 5
    assert result.winning_trades == 2  # 100, 100
    assert result.losing_trades == 1  # -50
    assert result.breakeven_trades == 2  # 0.0, 0.0

    assert result.win_rate == 0.4
    assert result.loss_rate == 0.2
    assert result.net_profit == 150.0
    assert result.gross_profit == 200.0
    assert result.gross_loss == -50.0
    assert result.profit_factor == 4.0  # 200 / 50


def test_risk_analysis(sample_trade_data):
    """Verifies drawdown and Value at Risk computations."""
    result = RiskAnalysis.calculate_metrics(sample_trade_data)

    # Cumulative PnL: [0.0, 0.0, 100.0, 50.0, 150.0]
    # Running peaks:   [0.0, 0.0, 100.0, 100.0, 150.0]
    # Drawdowns:       [0.0, 0.0, 0.0, 50.0, 0.0]
    assert result.max_drawdown == 50.0
    assert result.pnl_volatility > 0.0
    assert result.value_at_risk_95 < 0.0
    assert result.expected_shortfall_95 <= result.value_at_risk_95


def test_time_analysis(sample_trade_data):
    """Verifies session breakout statistics."""
    result = TimeAnalysis.calculate_metrics(sample_trade_data)

    # Hours: [0, 6, 12, 18, 0]
    # Sessions:
    # 0 -> Asia
    # 6 -> Asia
    # 12 -> Europe
    # 18 -> America
    assert "Asia" in result.session_metrics
    assert "Europe" in result.session_metrics
    assert "America" in result.session_metrics


def test_correlation_analysis(sample_trade_data):
    """Verifies Pearson and Spearman correlation calculation."""
    result = CorrelationAnalysis.calculate_metrics(sample_trade_data)

    assert "closed_pnl" in result.pearson_matrix
    assert "fg_value" in result.pearson_matrix
    assert result.sentiment_vs_pnl_pearson is not None


def test_summary_generator(sample_trade_data):
    """Verifies business insights and risk warning summaries."""
    trader_res = TraderAnalysis.calculate_metrics(sample_trade_data)
    market_res = MarketAnalysis.calculate_metrics(sample_trade_data)
    sentiment_res = SentimentAnalysis.calculate_metrics(sample_trade_data)
    coin_res = CoinAnalysis.calculate_metrics(sample_trade_data)
    performance_res = PerformanceAnalysis.calculate_metrics(sample_trade_data)
    risk_res = RiskAnalysis.calculate_metrics(sample_trade_data)
    time_res = TimeAnalysis.calculate_metrics(sample_trade_data)
    correlation_res = CorrelationAnalysis.calculate_metrics(sample_trade_data)

    summary = SummaryGenerator.generate_summary(
        trader_results=trader_res,
        market_results=market_res,
        sentiment_results=sentiment_res,
        coin_results=coin_res,
        performance_results=performance_res,
        risk_results=risk_res,
        time_results=time_res,
        correlation_results=correlation_res,
    )

    assert "executive_summary" in summary
    assert len(summary["top_insights"]) > 0
    assert len(summary["risk_warnings"]) > 0


def test_empty_dataframe_safety():
    """Confirms all sub-analysis classes handle empty input frames gracefully."""
    empty_df = pd.DataFrame()

    assert TraderAnalysis.calculate_metrics(empty_df).total_traders == 0
    assert MarketAnalysis.calculate_metrics(empty_df).symbol_distribution == {}
    assert SentimentAnalysis.calculate_metrics(empty_df).regimes == {}
    assert CoinAnalysis.calculate_metrics(empty_df).coins == {}
    assert PerformanceAnalysis.calculate_metrics(empty_df).total_trades == 0
    assert RiskAnalysis.calculate_metrics(empty_df).max_drawdown == 0.0
    assert TimeAnalysis.calculate_metrics(empty_df).hourly_metrics == {}
    assert CorrelationAnalysis.calculate_metrics(empty_df).pearson_matrix == {}


def test_analytics_engine_exports(sample_trade_data):
    """Verifies output reports and metrics are correctly written to directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock analytics output directory inside analytics_engine
        import analytics.analysis.analytics_engine as engine

        orig_out_dir = engine.ANALYTICS_OUTPUT_DIR
        engine.ANALYTICS_OUTPUT_DIR = Path(tmp_dir)

        try:
            AnalyticsEngine.run_analysis(df=sample_trade_data, export_outputs=True)

            assert (Path(tmp_dir) / "analytics_summary.json").exists()
            assert (Path(tmp_dir) / "analytics_summary.csv").exists()
            assert (Path(tmp_dir) / "leaderboards.csv").exists()
            assert (Path(tmp_dir) / "risk_metrics.csv").exists()
            assert (Path(tmp_dir) / "executive_summary.md").exists()
        finally:
            engine.ANALYTICS_OUTPUT_DIR = orig_out_dir
