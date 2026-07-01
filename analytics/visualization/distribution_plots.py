"""Distribution plotting helper for PrimeTrade AI.

Contains functions to plot histograms of PnLs, win/loss proportions,
and sentiment regime performance boxplots/violin plots.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

from utils.logger import analytics_logger


def plot_pnl_distribution_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static histogram with KDE showing PnL distribution.

    Args:
        df: Processed DataFrame containing 'closed_pnl'.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure, or None if column missing.
    """
    if "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'closed_pnl' for PnL distribution static plot.")
        return None

    # Filter out trades with no realized PnL (breakeven/unclosed)
    pnl_data = df["closed_pnl"].dropna()
    if pnl_data.empty:
        analytics_logger.warning("No closed PnL values available for distribution plot.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Render histogram and density curve
    sns.histplot(pnl_data, kde=True, color="#0052CC", ax=ax, bins=30, edgecolor="none", alpha=0.6)

    # Reference line at y=0
    ax.axvline(0, color="#EF4444", linestyle="--", linewidth=1.2, label="Breakeven (0)")

    ax.set_title("Distribution of Closed PnL", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("PnL (USDT)", fontsize=11, labelpad=10)
    ax.set_ylabel("Density / Count", fontsize=11, labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right")

    fig.tight_layout()
    return fig


def plot_pnl_distribution_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive histogram of PnL distributions.

    Args:
        df: Processed DataFrame containing 'closed_pnl'.

    Returns:
        Optional[go.Figure]: Plotly Figure, or None if column missing.
    """
    if "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'closed_pnl' for PnL distribution interactive plot.")
        return None

    pnl_data = df["closed_pnl"].dropna()
    if pnl_data.empty:
        analytics_logger.warning("No closed PnL values available for distribution plot.")
        return None

    fig = px.histogram(
        df,
        x="closed_pnl",
        nbins=30,
        title="Distribution of Closed PnL",
        color_discrete_sequence=["#0052CC"],
        labels={"closed_pnl": "PnL (USDT)"},
    )

    fig.update_layout(
        title=dict(
            text="Distribution of Closed PnL",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        xaxis=dict(title="PnL (USDT)", gridcolor="rgba(200, 200, 200, 0.15)"),
        yaxis=dict(title="Count", gridcolor="rgba(200, 200, 200, 0.15)"),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
    )
    return fig


def plot_win_loss_pie_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static pie chart representing win/loss/breakeven counts.

    Args:
        df: Processed DataFrame containing 'closed_pnl'.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure, or None if column missing.
    """
    if "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'closed_pnl' for win/loss pie static plot.")
        return None

    pnl = df["closed_pnl"].dropna()
    if pnl.empty:
        return None

    wins = np.sum(pnl > 0)
    losses = np.sum(pnl < 0)
    breakeven = np.sum(pnl == 0)

    labels = []
    sizes = []
    colors = []

    if wins > 0:
        labels.append(f"Wins ({wins})")
        sizes.append(wins)
        colors.append("#22C55E")
    if losses > 0:
        labels.append(f"Losses ({losses})")
        sizes.append(losses)
        colors.append("#EF4444")
    if breakeven > 0:
        labels.append(f"Breakeven ({breakeven})")
        sizes.append(breakeven)
        colors.append("#94A3B8")

    if not sizes:
        return None

    fig, ax = plt.subplots(figsize=(6, 6))

    # Render pie chart with clean aesthetics
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        textprops=dict(color="black", weight="bold"),
        wedgeprops=dict(width=0.4, edgecolor="white"),  # Donut format
    )

    # Modern legend positioning
    ax.legend(
        wedges,
        labels,
        title="Outcomes",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
    )
    ax.set_title("Global Trading Outcome Ratio", fontsize=14, fontweight="bold", pad=15)

    fig.tight_layout()
    return fig


def plot_win_loss_pie_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive pie chart representing win/loss/breakeven counts.

    Args:
        df: Processed DataFrame containing 'closed_pnl'.

    Returns:
        Optional[go.Figure]: Plotly Figure, or None if column missing.
    """
    if "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'closed_pnl' for win/loss pie interactive plot.")
        return None

    pnl = df["closed_pnl"].dropna()
    if pnl.empty:
        return None

    wins = np.sum(pnl > 0)
    losses = np.sum(pnl < 0)
    breakeven = np.sum(pnl == 0)

    labels = []
    values = []
    colors = []

    if wins > 0:
        labels.append("Wins")
        values.append(int(wins))
        colors.append("#22C55E")
    if losses > 0:
        labels.append("Losses")
        values.append(int(losses))
        colors.append("#EF4444")
    if breakeven > 0:
        labels.append("Breakeven")
        values.append(int(breakeven))
        colors.append("#94A3B8")

    if not values:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors, line=dict(color="#0F172A", width=2)),
            textinfo="percent+label",
            hovertemplate="<b>Outcome:</b> %{label}<br><b>Count:</b> %{value}<br><b>Percentage:</b> %{percent}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Global Trading Outcome Ratio",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
    )
    return fig


def plot_sentiment_regime_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static box/violin plot comparing returns across sentiment regimes.

    Args:
        df: Processed DataFrame.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure, or None if required columns missing.
    """
    data = df.copy()
    sentiment_col = (
        "fg_classification"
        if "fg_classification" in data.columns
        else ("classification" if "classification" in data.columns else None)
    )
    if not sentiment_col and "fg_value" in data.columns:
        data["fg_classification"] = data["fg_value"].apply(
            lambda val: "Fear" if val < 45 else ("Greed" if val > 55 else "Neutral")
        )
        sentiment_col = "fg_classification"

    if not sentiment_col or "closed_pnl" not in data.columns:
        analytics_logger.warning("Missing sentiment or closed PnL columns for regime plot.")
        return None

    # Exclude Unknown or NA values
    data = data[data[sentiment_col].notna() & (data[sentiment_col] != "Unknown")]
    if data.empty:
        return None

    # Reorder classifications logically if they fit standard names
    regime_order = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
    active_order = [r for r in regime_order if r in data[sentiment_col].unique()]
    if not active_order:
        active_order = list(data[sentiment_col].unique())

    fig, ax = plt.subplots(figsize=(10, 6))

    # Violin plot overlayed with box plot
    sns.violinplot(
        x=sentiment_col,
        y="closed_pnl",
        data=data,
        order=active_order,
        inner=None,
        hue=sentiment_col,
        legend=False,
        palette="Blues_d",
        ax=ax,
        linewidth=0.8,
    )
    sns.boxplot(
        x=sentiment_col,
        y="closed_pnl",
        data=data,
        order=active_order,
        width=0.15,
        color="white",
        ax=ax,
        boxprops=dict(zorder=3),
        showfliers=False,
    )

    # Reference line
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")

    ax.set_title(
        "PnL Distribution Across Sentiment Regimes",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Sentiment Classification", fontsize=11, labelpad=10)
    ax.set_ylabel("Realized PnL (USDT)", fontsize=11, labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.5, axis="y")

    fig.tight_layout()
    return fig


def plot_sentiment_regime_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive box/violin plot comparing returns across sentiment regimes.

    Args:
        df: Processed DataFrame.

    Returns:
        Optional[go.Figure]: Plotly Figure, or None if required columns missing.
    """
    data = df.copy()
    sentiment_col = (
        "fg_classification"
        if "fg_classification" in data.columns
        else ("classification" if "classification" in data.columns else None)
    )
    if not sentiment_col and "fg_value" in data.columns:
        data["fg_classification"] = data["fg_value"].apply(
            lambda val: "Fear" if val < 45 else ("Greed" if val > 55 else "Neutral")
        )
        sentiment_col = "fg_classification"

    if not sentiment_col or "closed_pnl" not in data.columns:
        analytics_logger.warning("Missing sentiment or closed PnL columns for regime plot.")
        return None

    data = data[data[sentiment_col].notna() & (data[sentiment_col] != "Unknown")]
    if data.empty:
        return None

    regime_order = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
    active_order = [r for r in regime_order if r in data[sentiment_col].unique()]
    if not active_order:
        active_order = list(data[sentiment_col].unique())

    fig = px.box(
        data,
        x=sentiment_col,
        y="closed_pnl",
        category_orders={sentiment_col: active_order},
        points="all",  # Show individual scatter points alongside box
        title="PnL Distribution Across Sentiment Regimes",
        color=sentiment_col,
        color_discrete_sequence=px.colors.qualitative.Safe,
        labels={"closed_pnl": "Realized PnL (USDT)", sentiment_col: "Regime"},
    )

    fig.update_layout(
        title=dict(
            text="PnL Distribution Across Sentiment Regimes",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        xaxis=dict(title="Sentiment Classification", gridcolor="rgba(200, 200, 200, 0.15)"),
        yaxis=dict(title="Realized PnL (USDT)", gridcolor="rgba(200, 200, 200, 0.15)"),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=40, r=40, t=60, b=40),
        height=600,
        showlegend=False,
    )
    return fig
