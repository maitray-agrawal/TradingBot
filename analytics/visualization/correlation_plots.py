"""Correlation plotting helper for PrimeTrade AI.

Contains functions to plot correlation matrices and sentiment vs return scatter charts.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

from utils.logger import analytics_logger


def plot_correlation_matrix_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static correlation matrix heatmap for numeric variables.

    Args:
        df: Processed DataFrame.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure, or None if no numeric columns.
    """
    # Pick relevant numeric columns
    cols = ["closed_pnl", "execution_price", "size", "fg_value", "fees"]
    numeric_cols = [c for c in cols if c in df.columns]

    if len(numeric_cols) < 2:
        analytics_logger.warning("Insufficient numeric columns for correlation matrix.")
        return None

    corr_df = df[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))

    # Draw correlation heatmap
    sns.heatmap(
        corr_df,
        annot=True,
        cmap="coolwarm",
        vmin=-1.0,
        vmax=1.0,
        fmt=".2f",
        linewidths=0.5,
        ax=ax,
    )

    ax.set_title("Correlation Matrix Heatmap", fontsize=14, fontweight="bold", pad=15)
    fig.tight_layout()
    return fig


def plot_correlation_matrix_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive correlation matrix heatmap.

    Args:
        df: Processed DataFrame.

    Returns:
        Optional[go.Figure]: Plotly Figure, or None if insufficient columns.
    """
    cols = ["closed_pnl", "execution_price", "size", "fg_value", "fees"]
    numeric_cols = [c for c in cols if c in df.columns]

    if len(numeric_cols) < 2:
        return None

    corr_df = df[numeric_cols].corr()

    fig = go.Figure(
        data=go.Heatmap(
            z=corr_df.to_numpy(),
            x=corr_df.columns,
            y=corr_df.index,
            colorscale="RdBu",
            zmin=-1.0,
            zmax=1.0,
            zmid=0.0,
            text=np.round(corr_df.to_numpy(), 2),
            texttemplate="%{text}",
            hovertemplate="<b>Var 1:</b> %{x}<br><b>Var 2:</b> %{y}<br><b>Correlation:</b> %{z:.4f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Correlation Matrix Heatmap",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=80, r=40, t=60, b=40),
        height=500,
    )
    return fig


def plot_sentiment_vs_pnl_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static scatter plot of Fear & Greed index vs closed returns with regression line.

    Args:
        df: Processed DataFrame containing 'fg_value' and 'closed_pnl'.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure, or None if required columns missing.
    """
    if "fg_value" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'fg_value' or 'closed_pnl' for scatter plot.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Regplot includes confidence intervals for regression line
    sns.regplot(
        x="fg_value",
        y="closed_pnl",
        data=df,
        ax=ax,
        scatter_kws={"color": "#0052CC", "alpha": 0.5, "edgecolor": "none"},
        line_kws={"color": "#EF4444", "linewidth": 1.5},
    )

    # Reference line at y=0
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")

    ax.set_title(
        "Fear & Greed Sentiment vs realized PnL", fontsize=14, fontweight="bold", pad=15
    )
    ax.set_xlabel("Fear & Greed Index", fontsize=11, labelpad=10)
    ax.set_ylabel("Realized PnL (USDT)", fontsize=11, labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.5)

    fig.tight_layout()
    return fig


def plot_sentiment_vs_pnl_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive scatter plot of Fear & Greed Index vs realized PnL.

    Args:
        df: Processed DataFrame.

    Returns:
        Optional[go.Figure]: Plotly Figure, or None if required columns missing.
    """
    if "fg_value" not in df.columns or "closed_pnl" not in df.columns:
        return None

    # Sort so regression line overlays properly
    data = df.dropna(subset=["fg_value", "closed_pnl"]).copy()
    if data.empty:
        return None

    # Compute a simple regression line to display interactively
    x = data["fg_value"].to_numpy()
    y = data["closed_pnl"].to_numpy()

    slope, intercept = np.polyfit(x, y, 1) if len(x) > 1 else (0.0, 0.0)
    regression_line = slope * x + intercept

    fig = go.Figure()

    # Scatter points
    fig.add_trace(
        go.Scatter(
            x=data["fg_value"],
            y=data["closed_pnl"],
            mode="markers",
            name="Trade Outcomes",
            marker=dict(
                color="#0052CC",
                opacity=0.6,
                size=8,
                line=dict(color="#0F172A", width=1),
            ),
            hovertemplate="<b>Fear & Greed:</b> %{x}<br><b>PnL:</b> %{y:.2f} USDT<extra></extra>",
        )
    )

    # Trend line
    fig.add_trace(
        go.Scatter(
            x=data["fg_value"],
            y=regression_line,
            mode="lines",
            name=f"OLS Trendline (m={slope:.4f})",
            line=dict(color="#EF4444", width=2, dash="dash"),
        )
    )

    fig.update_layout(
        title=dict(
            text="Fear & Greed Sentiment vs realized PnL",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        xaxis=dict(title="Fear & Greed Index", gridcolor="rgba(200, 200, 200, 0.15)"),
        yaxis=dict(title="Realized PnL (USDT)", gridcolor="rgba(200, 200, 200, 0.15)"),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
    )
    return fig
