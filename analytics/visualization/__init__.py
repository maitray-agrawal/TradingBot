"""Visualization Engine Package for PrimeTrade AI.

Exposes plotting functions, static/interactive facades, and the orchestrator engine.
"""

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
from analytics.visualization.matplotlib_plots import generate_all_static_plots
from analytics.visualization.plotly_dashboard import (
    generate_all_interactive_plots,
    generate_unified_dashboard,
)
from analytics.visualization.timeseries import (
    plot_cumulative_pnl_matplotlib,
    plot_cumulative_pnl_plotly,
    plot_daily_pnl_matplotlib,
    plot_daily_pnl_plotly,
)
from analytics.visualization.visualization_engine import VisualizationEngine

__all__ = [
    # Engine
    "VisualizationEngine",
    # Facades
    "generate_all_static_plots",
    "generate_all_interactive_plots",
    "generate_unified_dashboard",
    # Timeseries
    "plot_cumulative_pnl_matplotlib",
    "plot_cumulative_pnl_plotly",
    "plot_daily_pnl_matplotlib",
    "plot_daily_pnl_plotly",
    # Distributions
    "plot_pnl_distribution_matplotlib",
    "plot_pnl_distribution_plotly",
    "plot_win_loss_pie_matplotlib",
    "plot_win_loss_pie_plotly",
    "plot_sentiment_regime_matplotlib",
    "plot_sentiment_regime_plotly",
    # Leaderboards
    "plot_coin_leaderboard_matplotlib",
    "plot_coin_leaderboard_plotly",
    "plot_trader_leaderboard_matplotlib",
    "plot_trader_leaderboard_plotly",
    # Heatmaps
    "plot_hourly_activity_matplotlib",
    "plot_hourly_activity_plotly",
    # Correlations
    "plot_correlation_matrix_matplotlib",
    "plot_correlation_matrix_plotly",
    "plot_sentiment_vs_pnl_matplotlib",
    "plot_sentiment_vs_pnl_plotly",
]
