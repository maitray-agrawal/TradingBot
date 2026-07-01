"""Plotly interactive plotter facade and unified dashboard assembler for PrimeTrade AI.

Saves interactive HTML versions of all trading and sentiment charts,
and generates a combined dashboard report.
"""

from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import plotly.graph_objects as go

import config.paths
from analytics.visualization.correlation_plots import (
    plot_correlation_matrix_plotly,
    plot_sentiment_vs_pnl_plotly,
)
from analytics.visualization.distribution_plots import (
    plot_pnl_distribution_plotly,
    plot_sentiment_regime_plotly,
    plot_win_loss_pie_plotly,
)
from analytics.visualization.heatmaps import plot_hourly_activity_plotly
from analytics.visualization.leaderboards import (
    plot_coin_leaderboard_plotly,
    plot_trader_leaderboard_plotly,
)
from analytics.visualization.timeseries import (
    plot_cumulative_pnl_plotly,
    plot_daily_pnl_plotly,
)
from utils.logger import analytics_logger


def save_plotly_html(fig: go.Figure, base_name: str) -> str:
    """Saves a Plotly Figure as a standalone interactive HTML file.

    Args:
        fig: The Plotly Figure object to save.
        base_name: The file name without extension.

    Returns:
        str: Absolute path to the saved HTML file.
    """
    config.paths.CHARTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html_path = config.paths.CHARTS_OUTPUT_DIR / f"{base_name}.html"

    # Save with CDN script injection for smaller file sizes
    fig.write_html(str(html_path), include_plotlyjs="cdn", full_html=True)

    analytics_logger.info(f"Saved interactive plot: {html_path.name}")
    return str(html_path.resolve())


def generate_all_interactive_plots(df: pd.DataFrame) -> Dict[str, str]:
    """Generates and exports all interactive Plotly charts as HTML.

    Args:
        df: Merged/Processed DataFrame.

    Returns:
        Dict[str, str]: Map of chart keys to saved HTML file paths.
    """
    analytics_logger.info("Generating interactive Plotly charts...")
    manifest = {}

    plots_to_make = [
        ("cumulative_pnl", plot_cumulative_pnl_plotly),
        ("daily_pnl", plot_daily_pnl_plotly),
        ("pnl_distribution", plot_pnl_distribution_plotly),
        ("win_loss_pie", plot_win_loss_pie_plotly),
        ("sentiment_regime_pnl", plot_sentiment_regime_plotly),
        ("coin_leaderboard", plot_coin_leaderboard_plotly),
        ("trader_leaderboard", plot_trader_leaderboard_plotly),
        ("hourly_activity_heatmap", plot_hourly_activity_plotly),
        ("correlation_matrix", plot_correlation_matrix_plotly),
        ("sentiment_vs_pnl_scatter", plot_sentiment_vs_pnl_plotly),
    ]

    for key, plot_func in plots_to_make:
        try:
            fig = plot_func(df)
            if fig is not None:
                manifest[key] = save_plotly_html(fig, key)
            else:
                analytics_logger.warning(
                    f"Plotly function for '{key}' returned None. Skipping."
                )
        except Exception as e:
            analytics_logger.error(
                f"Failed to generate interactive plot '{key}': {e}", exc_info=True
            )

    return manifest


def generate_unified_dashboard(df: pd.DataFrame) -> Optional[str]:
    """Assembles all interactive Plotly plots into a single, cohesive, responsive HTML dashboard.

    Args:
        df: Merged/Processed DataFrame.

    Returns:
        Optional[str]: Path to the generated unified dashboard, or None if failed.
    """
    analytics_logger.info("Assembling unified dark-mode dashboard...")
    try:
        # Calculate summary statistics to display in the header
        total_trades = len(df)
        if total_trades == 0:
            analytics_logger.warning("Empty DataFrame provided for unified dashboard.")
            return None

        pnl_col = df["closed_pnl"] if "closed_pnl" in df else pd.Series(dtype=float)
        net_profit = pnl_col.sum() if not pnl_col.empty else 0.0

        wins = pnl_col[pnl_col > 0]
        losses = pnl_col[pnl_col < 0]

        win_rate = (
            (len(wins) / len(pnl_col[pnl_col != 0]) * 100)
            if len(pnl_col[pnl_col != 0]) > 0
            else 0.0
        )

        gross_profit = wins.sum()
        gross_loss = abs(losses.sum())
        profit_factor = (
            (gross_profit / gross_loss)
            if gross_loss > 0
            else (gross_profit if gross_profit > 0 else 1.0)
        )

        # Generate figures
        fig_cum_pnl = plot_cumulative_pnl_plotly(df)
        fig_daily_pnl = plot_daily_pnl_plotly(df)
        fig_dist = plot_pnl_distribution_plotly(df)
        fig_pie = plot_win_loss_pie_plotly(df)
        fig_regime = plot_sentiment_regime_plotly(df)
        fig_coins = plot_coin_leaderboard_plotly(df)
        fig_traders = plot_trader_leaderboard_plotly(df)
        fig_heatmap = plot_hourly_activity_plotly(df)
        fig_corr = plot_correlation_matrix_plotly(df)
        fig_scatter = plot_sentiment_vs_pnl_plotly(df)

        # Get HTML snippets (without full page wrapper and without copying plotly.js library code repeatedly)
        def get_div(fig: Optional[go.Figure]) -> str:
            if fig is None:
                return "<div class='error-box'>Chart unavailable (missing columns or data)</div>"
            return fig.to_html(full_html=False, include_plotlyjs=False)

        # Build dashboard template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrimeTrade AI - Sentiment & Trading Analytics Dashboard</title>
    
    <!-- Modern Typography & Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    
    <!-- Plotly CDN -->
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>

    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: #131a2c;
            --card-border: rgba(255, 255, 255, 0.05);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-primary: #0052cc;
            --accent-green: #22c55e;
            --accent-red: #ef4444;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            padding: 24px;
            min-height: 100vh;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--card-border);
        }}

        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitle {{
            color: var(--text-muted);
            font-size: 14px;
            margin-top: 4px;
        }}

        /* Summary Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.1);
        }}

        .stat-label {{
            color: var(--text-muted);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 24px;
            font-weight: 700;
        }}

        .val-profit {{ color: var(--accent-green); }}
        .val-loss {{ color: var(--accent-red); }}
        .val-neutral {{ color: var(--text-main); }}

        /* Charts Layout */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 24px;
        }}

        /* Responsive adjustments for smaller screens */
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .chart-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .error-box {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 350px;
            color: var(--accent-red);
            font-size: 14px;
            background: rgba(239, 68, 68, 0.05);
            border: 1px dashed rgba(239, 68, 68, 0.2);
            border-radius: 8px;
        }}
    </style>
</head>
<body>

    <header>
        <div>
            <h1>PRIME-TRADE AI</h1>
            <div class="subtitle">Sentiment-Driven Crypto Trading Analytics & Performance Monitor</div>
        </div>
        <div style="text-align: right;">
            <div class="subtitle">Report Generated</div>
            <div style="font-weight: 600; font-size: 14px;">UTC Timestamp</div>
        </div>
    </header>

    <!-- Metrics Ribbon -->
    <section class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Total Executed Trades</div>
            <div class="stat-value val-neutral">{total_trades}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Net Performance</div>
            <div class="stat-value {'val-profit' if net_profit >= 0 else 'val-loss'}">{net_profit:+.2f} USDT</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Global Win Rate</div>
            <div class="stat-value val-neutral">{win_rate:.1f}%</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Profit Factor</div>
            <div class="stat-value val-neutral">{profit_factor:.2f}</div>
        </div>
    </section>

    <!-- Interactive Plots Section -->
    <section class="charts-grid">
        
        <!-- PnL Curves -->
        <div class="chart-card">
            {get_div(fig_cum_pnl)}
        </div>
        <div class="chart-card">
            {get_div(fig_daily_pnl)}
        </div>

        <!-- Distributions -->
        <div class="chart-card">
            {get_div(fig_dist)}
        </div>
        <div class="chart-card">
            {get_div(fig_pie)}
        </div>

        <!-- Sentiment Influence -->
        <div class="chart-card">
            {get_div(fig_regime)}
        </div>
        <div class="chart-card">
            {get_div(fig_scatter)}
        </div>

        <!-- Leaderboards -->
        <div class="chart-card">
            {get_div(fig_coins)}
        </div>
        <div class="chart-card">
            {get_div(fig_traders)}
        </div>

        <!-- Correlations and Heatmaps -->
        <div class="chart-card">
            {get_div(fig_heatmap)}
        </div>
        <div class="chart-card">
            {get_div(fig_corr)}
        </div>

    </section>

</body>
</html>
"""

        # Save to file
        config.paths.CHARTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        dashboard_path = config.paths.CHARTS_OUTPUT_DIR / "unified_dashboard.html"
        dashboard_path.write_text(html_template, encoding="utf-8")

        analytics_logger.info(
            f"Generated unified dashboard successfully at: {dashboard_path.name}"
        )
        return str(dashboard_path.resolve())

    except Exception as e:
        analytics_logger.error(
            f"Failed to generate unified dashboard: {e}", exc_info=True
        )
        return None
