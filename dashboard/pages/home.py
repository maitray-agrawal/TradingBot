"""Home Landing Page for the PrimeTrade AI dashboard."""

from pathlib import Path
import streamlit as st
import pandas as pd

from config import settings
from dashboard.components import hero_banner, glass_card
from analytics.ingestion.dataset_registry import DatasetRegistry

# Render Hero Banner
hero_banner(
    title="⚡ PrimeTrade AI Systems",
    subtitle="Sentiment-Driven Cryptographic Asset Analytics & Binance Futures Testnet Trading Desk",
)

# Registry reference
registry = DatasetRegistry()
datasets = registry.list_datasets()

# Columns layout for status panels
st.subheader("🛠️ System Status Control Panel")
col1, col2, col3, col4 = st.columns(4)

with col1:
    ingested_count = len(datasets)
    glass_card(
        title="📥 Ingestion Engine",
        content="🟢 Online & Verified",
        subtitle=f"{ingested_count} datasets currently registered",
    )

with col2:
    processed_count = 0
    processed_dir = Path(settings.data_directory) / "processed"
    if processed_dir.is_dir():
        processed_count = len(list(processed_dir.glob("*.csv")))
    glass_card(
        title="⚙️ Preprocessing Engine",
        content="🟢 Operational",
        subtitle=f"{processed_count} preprocessed/merged profiles",
    )

with col3:
    glass_card(
        title="🧠 Strategy Recommendations",
        content="🟢 Rules Loaded",
        subtitle="Evaluating win-rates, drawdown & F&G regimes",
    )

with col4:
    bot_mode = "🟢 Live Testnet" if st.session_state.bot_live_mode else "🟡 Dry Run (Sim)"
    creds_str = "Credentials loaded" if st.session_state.has_credentials else "Keys missing (Dry-Run only)"
    glass_card(
        title="🤖 Trading Bot Engine",
        content=bot_mode,
        subtitle=creds_str,
    )

# Selected Dataset Details
st.markdown("---")
st.subheader("📂 Loaded Dataset Status")

active_name = st.session_state.active_dataset_name
active_path = st.session_state.active_dataset_path

if active_name and active_path and Path(active_path).is_file():
    # Load metadata properties
    ds_meta = registry.get(active_name) or {}
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(
            f"""
            <div style="background-color:rgba(30,41,59,0.5); padding:20px; border-radius:10px; border:1px solid rgba(255,255,255,0.05);">
                <h4>Active Dataset Metadata</h4>
                <p><b>Name:</b> {active_name}</p>
                <p><b>Type:</b> <span class="badge badge-info">{ds_meta.get('dataset_type', 'UNKNOWN')}</span></p>
                <p><b>Disk Size:</b> {ds_meta.get('file_size_bytes', 0) / 1024:.2f} KB</p>
                <p><b>Row Count:</b> {ds_meta.get('rows', 'N/A')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.info(
            "💡 **Dataset Ready for Action**: This file is selected as the default data input. "
            "Navigate to the **Analytics**, **Charts**, or **Statistics** pages to run statistical tests, "
            "visualize trading distributions, and compile executive PDF reports."
        )
else:
    st.warning("⚠️ No active dataset has been selected or loaded. Go to the **Upload Dataset** page to load trading logs.")

# Interactive Walkthrough
st.markdown("---")
st.subheader("📚 Platform Navigation Guide")
with st.expander("🔍 Click to view step-by-step walkthrough"):
    st.markdown(
        """
        1. **Ingest Raw Data**: Go to the **Upload Dataset** tab and upload your historical CSV/Excel trading logs. The system will automatically map the headers and analyze file quality.
        2. **Analyze Sentiment Interactions**: Go to the **Analytics** page to check basic metrics like win rates, average PnLs, and profit-to-loss ratios. Open **Charts** for graphical models.
        3. **Establish Significance**: Go to the **Statistics** page. It runs parametric T-Tests, Mann-Whitney U, and ANOVA analyses to prove if Fear & Greed sentiment significantly affects execution outcomes.
        4. **Generate Strategy Signals**: Go to the **Strategy** desk. Set parameter thresholds to calculate recommendation triggers (BUY, SELL, HOLD, REDUCE_LEVERAGE, AVOID_TRADING).
        5. **Execute Trades**: Use the **Trading Bot** console to place orders on the Binance Futures Testnet, complete with real-time margin and risk limits validation.
        """
    )
