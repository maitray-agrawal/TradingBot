"""Charts Page for the PrimeTrade AI dashboard."""

from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components import hero_banner
from analytics.ingestion.dataset_registry import DatasetRegistry

hero_banner(
    title="📈 Visual Analytics Deck",
    subtitle="Interactive Plotly charts mapping return distributions, asset performance, and cumulative performance.",
)

# Registry & active dataset selection
registry = DatasetRegistry()
datasets = registry.list_datasets()

if not datasets:
    st.warning("⚠️ No datasets are registered. Please upload a dataset first in the **Upload Dataset** page.")
else:
    active_name = st.session_state.active_dataset_name
    active_path = Path(st.session_state.active_dataset_path) if st.session_state.active_dataset_path else None
    
    if active_path and active_path.exists():
        try:
            df = pd.read_csv(active_path)
            
            # Check required columns
            required = ["closed_pnl", "timestamp", "symbol", "side"]
            if not all(col in df.columns for col in required):
                st.warning("⚠️ Active dataset is raw and lacks calculated metrics. Run Preprocessing on the **Analytics** page.")
                st.stop()
                
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            
            # Sidebar layout filters just for visual clarity
            st.markdown("### 📊 Interactive Visualizations")
            
            # Multi-select symbols
            symbols = sorted(df["symbol"].unique().tolist())
            selected_symbols = st.multiselect("Filter Charts by Symbol", options=symbols, default=symbols)
            
            df_filtered = df[df["symbol"].isin(selected_symbols)]
            
            if df_filtered.empty:
                st.warning("No data matches selected symbol filters.")
                st.stop()
                
            # Grid layout for charts
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            row3_col1, row3_col2 = st.columns(2)
            
            # 1. Cumulative PnL Curve
            with row1_col1:
                st.markdown("#### Cumulative PnL Over Time")
                # Re-calculate cumulative sum to be clean on filtered subset
                df_filtered = df_filtered.copy()
                df_filtered["cum_pnl_filtered"] = df_filtered["closed_pnl"].cumsum()
                fig_cum = px.line(
                    df_filtered,
                    x="timestamp",
                    y="cum_pnl_filtered",
                    title="Cumulative realized PnL ($)",
                    labels={"timestamp": "Execution Time", "cum_pnl_filtered": "Cumulative PnL ($)"},
                    template="plotly_dark",
                )
                fig_cum.update_traces(line=dict(color="#00bfff", width=2.5))
                st.plotly_chart(fig_cum, use_container_width=True)
                
            # 2. Return Distribution
            with row1_col2:
                st.markdown("#### Return Distribution")
                fig_dist = px.histogram(
                    df_filtered,
                    x="closed_pnl",
                    nbins=40,
                    title="Distribution of Closed PnL per Trade",
                    labels={"closed_pnl": "Trade Return ($)"},
                    template="plotly_dark",
                    opacity=0.8,
                    color_discrete_sequence=["#9f7aea"],
                )
                fig_dist.add_vline(x=0.0, line_dash="dash", line_color="red", annotation_text="Break-even")
                st.plotly_chart(fig_dist, use_container_width=True)
                
            # 3. Win/Loss Ratio
            with row2_col1:
                st.markdown("#### Win/Loss Ratio")
                wins = len(df_filtered[df_filtered["closed_pnl"] > 0])
                losses = len(df_filtered[df_filtered["closed_pnl"] < 0])
                flat = len(df_filtered[df_filtered["closed_pnl"] == 0])
                
                ratio_df = pd.DataFrame({
                    "Outcome": ["Win", "Loss", "Flat"],
                    "Count": [wins, losses, flat]
                })
                
                fig_pie = px.pie(
                    ratio_df,
                    names="Outcome",
                    values="Count",
                    hole=0.4,
                    title="Trade Outcomes Break-down",
                    color="Outcome",
                    color_discrete_map={"Win": "#48bb78", "Loss": "#e53e3e", "Flat": "#a0aec0"},
                    template="plotly_dark",
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
            # 4. Performance by Symbol
            with row2_col2:
                st.markdown("#### Asset Performance (PnL Rank)")
                asset_pnl = df_filtered.groupby("symbol")["closed_pnl"].sum().reset_index()
                asset_pnl = asset_pnl.sort_values("closed_pnl", ascending=False)
                
                fig_asset = px.bar(
                    asset_pnl,
                    x="symbol",
                    y="closed_pnl",
                    title="Total Closed PnL per Token",
                    labels={"symbol": "Trading Pair", "closed_pnl": "Total PnL ($)"},
                    color="closed_pnl",
                    color_continuous_scale=px.colors.diverging.RdYlGn,
                    template="plotly_dark",
                )
                st.plotly_chart(fig_asset, use_container_width=True)
                
            # 5. UTC Hourly Session Heatmap
            with row3_col1:
                st.markdown("#### Hourly Activity Patterns (UTC)")
                # Group by weekday and hour
                if "weekday" in df_filtered.columns and "hour" in df_filtered.columns:
                    heatmap_data = df_filtered.groupby(["weekday", "hour"])["closed_pnl"].count().unstack(fill_value=0)
                    
                    # Ensure all 24 hours and 7 days are represented
                    for h in range(24):
                        if h not in heatmap_data.columns:
                            heatmap_data[h] = 0
                    heatmap_data = heatmap_data.reindex(columns=range(24))
                    
                    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    # Map numerical weekday representation or string to index
                    # Let's map indexes 0-6
                    heatmap_data = heatmap_data.reindex(index=range(7), fill_value=0)
                    
                    fig_heat = go.Figure(data=go.Heatmap(
                        z=heatmap_data.values,
                        x=[f"{h:02d}:00" for h in range(24)],
                        y=weekdays,
                        colorscale="Blues",
                        texttemplate="%{z}",
                    ))
                    fig_heat.update_layout(
                        title="Trade Counts by Weekday & Hour",
                        template="plotly_dark",
                    )
                    st.plotly_chart(fig_heat, use_container_width=True)
                else:
                    st.info("Hourly details unavailable in the active dataset schema.")
                    
            # 6. Sentiment Index correlation scatter
            with row3_col2:
                st.markdown("#### Sentiment Index (Fear & Greed) vs. Closed PnL")
                if "fg_value" in df_filtered.columns:
                    fig_scatter = px.scatter(
                        df_filtered,
                        x="fg_value",
                        y="closed_pnl",
                        color="side",
                        hover_data=["symbol", "size"],
                        title="Trade Return vs Fear & Greed Value",
                        labels={"fg_value": "Fear & Greed Index", "closed_pnl": "Realized PnL ($)"},
                        template="plotly_dark",
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.info("Fear & Greed sentiment value features are not present in this dataset.")
                    
        except Exception as e:
            st.error(f"❌ Failed to generate charts: {e}")
    else:
        st.warning("⚠️ No active dataset has been selected or loaded. Go to the **Upload Dataset** page to load trading logs.")
