"""Analytics Page for the PrimeTrade AI dashboard."""

from pathlib import Path
import streamlit as st
import pandas as pd

from config import settings
from dashboard.components import hero_banner, glass_card
from analytics.ingestion.dataset_registry import DatasetRegistry
from analytics.analysis.analytics_engine import AnalyticsEngine

hero_banner(
    title="📊 Data Analytics Desk",
    subtitle="Configure interactive filters, inspect key trading metrics, and download processed datasets.",
)

# Registry & active dataset selection
registry = DatasetRegistry()
datasets = registry.list_datasets()

if not datasets:
    st.warning("⚠️ No datasets are registered. Please upload a dataset first in the **Upload Dataset** page.")
else:
    # Select dataset
    dataset_names = [d["name"] for d in datasets]
    dataset_lookup = {d["name"]: d["file_path"] for d in datasets}
    default_index = 0
    if st.session_state.active_dataset_name in dataset_names:
        default_index = dataset_names.index(st.session_state.active_dataset_name)
        
    selected_name = st.selectbox(
        "Select Dataset for Analysis",
        options=dataset_names,
        index=default_index,
    )
    
    # Update active selection if changed
    if selected_name != st.session_state.active_dataset_name:
        st.session_state.active_dataset_name = selected_name
        st.session_state.active_dataset_path = dataset_lookup[selected_name]
        st.rerun()

    active_path = Path(st.session_state.active_dataset_path)
    
    if active_path.exists():
        # Load dataset
        try:
            # Let's load the dataset
            df_raw = pd.read_csv(active_path)
            
            # Check if columns matching processed data are present.
            # If not, let's offer preprocessing run.
            required_cols = ["closed_pnl", "timestamp", "symbol", "side"]
            has_required = all(col in df_raw.columns for col in required_cols)
            
            if not has_required:
                st.warning(
                    f"⚠️ The selected dataset `{selected_name}` appears to be raw. "
                    "You need to run the Preprocessing & Feature Engineering pipeline to generate trading metrics."
                )
                if st.button("⚡ Run Preprocessing Pipeline"):
                    with st.spinner("Processing dataset..."):
                        # Running run_analysis will generate the master processed_data.csv
                        AnalyticsEngine.run_analysis()
                        # Direct state to processed_data.csv
                        processed_file = Path(settings.data_directory) / "processed" / "processed_data.csv"
                        if processed_file.exists():
                            st.session_state.active_dataset_name = "processed_data.csv"
                            st.session_state.active_dataset_path = str(processed_file)
                            # Register processed file if not in registry
                            from analytics.ingestion import IngestionEngine
                            IngestionEngine().load_dataset(str(processed_file))
                            st.success("Preprocessing completed successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to generate processed file.")
                st.stop()
                
            # If it has the columns, proceed with interactive filtering
            # Ensure timestamp is datetime
            df_raw["timestamp"] = pd.to_datetime(df_raw["timestamp"])
            
            st.markdown("### 🔍 Filters")
            col1, col2, col3, col4 = st.columns(4)
            
            # Date Range
            min_date = df_raw["timestamp"].min().date()
            max_date = df_raw["timestamp"].max().date()
            with col1:
                date_range = st.date_input(
                    "Select Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )
            
            # Symbol filter
            symbols = sorted(df_raw["symbol"].unique().tolist())
            with col2:
                selected_symbols = st.multiselect(
                    "Select Symbols",
                    options=symbols,
                    default=symbols,
                )
                
            # Side filter
            sides = ["ALL"] + sorted(df_raw["side"].unique().tolist())
            with col3:
                selected_side = st.selectbox(
                    "Select Order Side",
                    options=sides,
                    index=0,
                )
                
            # Notional/Size filter
            min_size = float(df_raw["size"].min())
            max_size = float(df_raw["size"].max())
            with col4:
                selected_size_range = st.slider(
                    "Filter by Trade Size",
                    min_value=min_size,
                    max_value=max_size,
                    value=(min_size, max_size),
                )
                
            # Apply filters
            df_filtered = df_raw.copy()
            
            # Date filter
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_dt = pd.to_datetime(date_range[0])
                end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                df_filtered = df_filtered[
                    (df_filtered["timestamp"] >= start_dt) & (df_filtered["timestamp"] <= end_dt)
                ]
                
            # Symbol filter
            if selected_symbols:
                df_filtered = df_filtered[df_filtered["symbol"].isin(selected_symbols)]
                
            # Side filter
            if selected_side != "ALL":
                df_filtered = df_filtered[df_filtered["side"] == selected_side]
                
            # Size filter
            df_filtered = df_filtered[
                (df_filtered["size"] >= selected_size_range[0]) & (df_filtered["size"] <= selected_size_range[1])
            ]
            
            # Display KPIs
            st.markdown("### 📈 Key Performance Indicators")
            kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
            
            total_trades = len(df_filtered)
            realized_pnl = df_filtered["closed_pnl"].sum() if total_trades > 0 else 0.0
            
            # Calculate win rate
            wins_df = df_filtered[df_filtered["closed_pnl"] > 0]
            win_rate = (len(wins_df) / total_trades * 100) if total_trades > 0 else 0.0
            
            # Profit factor
            profits = df_filtered[df_filtered["closed_pnl"] > 0]["closed_pnl"].sum()
            losses = abs(df_filtered[df_filtered["closed_pnl"] < 0]["closed_pnl"].sum())
            profit_factor = profits / losses if losses > 0 else (float("inf") if profits > 0 else 1.0)
            
            # Avg trade size
            avg_size = df_filtered["size"].mean() if total_trades > 0 else 0.0
            
            with kpi_col1:
                st.metric("Total Trades", f"{total_trades}")
            with kpi_col2:
                st.metric(
                    "Realized PnL",
                    f"${realized_pnl:,.2f}",
                    delta=f"${realized_pnl:,.2f}" if realized_pnl != 0 else None,
                    delta_color="normal" if realized_pnl >= 0 else "inverse",
                )
            with kpi_col3:
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with kpi_col4:
                pf_str = f"{profit_factor:.2f}" if profit_factor != float("inf") else "∞"
                st.metric("Profit Factor", pf_str)
            with kpi_col5:
                st.metric("Avg Trade Size", f"{avg_size:.4f}")
                
            # Filtered Table View
            st.markdown("### 📋 Filtered Records")
            st.dataframe(df_filtered, use_container_width=True)
            
            # Downloads Section
            csv_data = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Filtered Processed Dataset (CSV)",
                data=csv_data,
                file_name="filtered_processed_dataset.csv",
                mime="text/csv",
                use_container_width=True,
            )
            
        except Exception as e:
            st.error(f"Error processing dataset filters: {e}")
    else:
        st.error(f"Active file path does not exist: `{active_path}`")
