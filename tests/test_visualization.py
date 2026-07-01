"""Unit tests for the Visualization Engine of PrimeTrade AI."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import config.paths
from analytics.visualization.correlation_plots import (
    plot_correlation_matrix_matplotlib,
    plot_correlation_matrix_plotly,
    plot_sentiment_vs_pnl_matplotlib,
    plot_sentiment_vs_pnl_plotly,
)
from analytics.visualization.distribution_plots import (
    plot_pnl_distribution_matplotlib,
    plot_pnl_distribution_plotly,
    plot_sentiment_regime_matplotlib,
    plot_sentiment_regime_plotly,
    plot_win_loss_pie_matplotlib,
    plot_win_loss_pie_plotly,
)
from analytics.visualization.heatmaps import (
    plot_hourly_activity_matplotlib,
    plot_hourly_activity_plotly,
)
from analytics.visualization.leaderboards import (
    plot_coin_leaderboard_matplotlib,
    plot_coin_leaderboard_plotly,
    plot_trader_leaderboard_matplotlib,
    plot_trader_leaderboard_plotly,
)
from analytics.visualization.timeseries import (
    plot_cumulative_pnl_matplotlib,
    plot_cumulative_pnl_plotly,
    plot_daily_pnl_matplotlib,
    plot_daily_pnl_plotly,
)
from analytics.visualization.visualization_engine import VisualizationEngine


@pytest.fixture
def mock_visual_data():
    """Generates standard mock dataset containing all necessary columns for visualizations."""
    np.random.seed(42)
    n = 20
    timestamps = pd.date_range(start="2026-06-01", periods=n, freq="12h")

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "closed_pnl": np.random.normal(loc=10.0, scale=50.0, size=n),
            "symbol": np.random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT"], size=n),
            "account_id": np.random.choice(["trader_alpha", "trader_beta"], size=n),
            "execution_price": np.random.uniform(100.0, 60000.0, size=n),
            "size": np.random.uniform(0.1, 2.5, size=n),
            "fg_value": np.random.uniform(10.0, 90.0, size=n),
            "fg_classification": np.random.choice(["Fear", "Neutral", "Greed"], size=n),
            "fees": np.random.uniform(0.1, 5.0, size=n),
        }
    )


def test_empty_dataframe_handling():
    """Verifies visualization engine returns soft failure/skipped manifest for empty input."""
    engine = VisualizationEngine()
    empty_df = pd.DataFrame()
    result = engine.generate_and_save_visualizations(empty_df)

    assert result["status"] == "skipped"
    assert "message" in result
    assert result["unified_dashboard"] is None


def test_missing_columns_handling(mock_visual_data):
    """Verifies that plotting functions return None gracefully when critical columns are missing."""
    df_missing = mock_visual_data.drop(columns=["closed_pnl", "timestamp"])

    assert plot_cumulative_pnl_matplotlib(df_missing) is None
    assert plot_cumulative_pnl_plotly(df_missing) is None
    assert plot_daily_pnl_matplotlib(df_missing) is None
    assert plot_daily_pnl_plotly(df_missing) is None
    assert plot_pnl_distribution_matplotlib(df_missing) is None
    assert plot_pnl_distribution_plotly(df_missing) is None
    assert plot_win_loss_pie_matplotlib(df_missing) is None
    assert plot_win_loss_pie_plotly(df_missing) is None


def test_engine_visualizations_generation(mock_visual_data, monkeypatch, tmp_path):
    """Orchestrates visualization generation override testing to verify folder output."""
    # Patch output directories to a temporary test folder
    test_charts_dir = tmp_path / "charts"
    monkeypatch.setattr(config.paths, "CHARTS_OUTPUT_DIR", test_charts_dir)

    engine = VisualizationEngine()
    result = engine.generate_and_save_visualizations(mock_visual_data)

    assert result["status"] == "success"
    assert result["record_count"] == len(mock_visual_data)

    # Verify file structures created in temp directory
    assert test_charts_dir.exists()

    # Verify static exports exist
    for key, paths in result["static_plots"].items():
        assert Path(paths["png"]).exists()
        assert Path(paths["svg"]).exists()

    # Verify interactive HTML plots exist
    for key, path in result["interactive_plots"].items():
        assert Path(path).exists()

    # Verify unified dashboard assembled
    assert Path(result["unified_dashboard"]).exists()
    assert result["unified_dashboard"].endswith("unified_dashboard.html")
