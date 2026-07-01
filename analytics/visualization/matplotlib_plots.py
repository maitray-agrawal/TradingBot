"""Matplotlib and Seaborn static plotter facade for PrimeTrade AI.

Saves high-quality PNG and SVG versions of all trading and sentiment charts.
"""

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

import config.paths
from analytics.visualization.correlation_plots import (
    plot_correlation_matrix_matplotlib,
    plot_sentiment_vs_pnl_matplotlib,
)
from analytics.visualization.distribution_plots import (
    plot_pnl_distribution_matplotlib,
    plot_sentiment_regime_matplotlib,
    plot_win_loss_pie_matplotlib,
)
from analytics.visualization.heatmaps import plot_hourly_activity_matplotlib
from analytics.visualization.leaderboards import (
    plot_coin_leaderboard_matplotlib,
    plot_trader_leaderboard_matplotlib,
)
from analytics.visualization.timeseries import (
    plot_cumulative_pnl_matplotlib,
    plot_daily_pnl_matplotlib,
)
from utils.logger import analytics_logger


def save_figure(fig: plt.Figure, base_name: str) -> Dict[str, str]:
    """Helper to save a Matplotlib figure as both PNG and SVG.

    Args:
        fig: The Matplotlib Figure object to save.
        base_name: The file name without extension (e.g., 'cumulative_pnl').

    Returns:
        Dict[str, str]: Mappings of file types to their saved string paths.
    """
    config.paths.CHARTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    png_path = config.paths.CHARTS_OUTPUT_DIR / f"{base_name}.png"
    svg_path = config.paths.CHARTS_OUTPUT_DIR / f"{base_name}.svg"

    # Save PNG
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    # Save SVG
    fig.savefig(svg_path, format="svg", bbox_inches="tight")

    # Close figure to free up memory
    plt.close(fig)

    analytics_logger.info(f"Saved static plots: {png_path.name} and {svg_path.name}")
    return {
        "png": str(png_path.resolve()),
        "svg": str(svg_path.resolve()),
    }


def generate_all_static_plots(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """Generates and exports all static plots from the input DataFrame.

    Args:
        df: Merged/Processed DataFrame.

    Returns:
        Dict[str, Dict[str, str]]: Map of chart keys to dictionaries containing
                                   their png/svg file paths.
    """
    analytics_logger.info("Generating static Matplotlib/Seaborn plots...")
    manifest = {}

    # Define plotting calls
    plots_to_make = [
        ("cumulative_pnl", plot_cumulative_pnl_matplotlib),
        ("daily_pnl", plot_daily_pnl_matplotlib),
        ("pnl_distribution", plot_pnl_distribution_matplotlib),
        ("win_loss_pie", plot_win_loss_pie_matplotlib),
        ("sentiment_regime_pnl", plot_sentiment_regime_matplotlib),
        ("coin_leaderboard", plot_coin_leaderboard_matplotlib),
        ("trader_leaderboard", plot_trader_leaderboard_matplotlib),
        ("hourly_activity_heatmap", plot_hourly_activity_matplotlib),
        ("correlation_matrix", plot_correlation_matrix_matplotlib),
        ("sentiment_vs_pnl_scatter", plot_sentiment_vs_pnl_matplotlib),
    ]

    for key, plot_func in plots_to_make:
        try:
            fig = plot_func(df)
            if fig is not None:
                manifest[key] = save_figure(fig, key)
            else:
                analytics_logger.warning(
                    f"Plot function for '{key}' returned None. Skipping."
                )
        except Exception as e:
            analytics_logger.error(
                f"Failed to generate static plot '{key}': {e}", exc_info=True
            )

    return manifest
