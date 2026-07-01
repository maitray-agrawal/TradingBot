"""Streamlit dashboard entry point for PrimeTrade AI."""

import os
import sys
from pathlib import Path
import streamlit as st

# Add project root to path for relative imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories_exist, settings
from dashboard.components import inject_custom_styles
from trading_bot.client.client import BinanceTestnetClient
from analytics.ingestion.dataset_registry import DatasetRegistry

# Page Config (MUST be first Streamlit call)
st.set_page_config(
    page_title="PrimeTrade AI Systems",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize paths and registry
ensure_directories_exist()
registry = DatasetRegistry()

# Initialize Global Session State
if "active_dataset_name" not in st.session_state:
    # Set default dataset if available
    registered_datasets = registry.list_datasets()
    if registered_datasets:
        first_item = registered_datasets[0]
        st.session_state.active_dataset_name = first_item["name"]
        st.session_state.active_dataset_path = first_item["file_path"]
    else:
        st.session_state.active_dataset_name = None
        st.session_state.active_dataset_path = None

if "bot_live_mode" not in st.session_state:
    st.session_state.bot_live_mode = False

if "binance_client" not in st.session_state:
    # Initialize mock/real client
    api_key = settings.binance_api_key
    api_secret = settings.binance_secret_key
    # Check if credentials exist for live mode activation
    has_creds = bool(api_key and api_secret)
    
    st.session_state.has_credentials = has_creds
    # Default to Dry Run mode
    st.session_state.binance_client = BinanceTestnetClient(dry_run=True)

# Register Pages
home_page = st.Page("pages/home.py", title="Home", icon="🏠")
upload_page = st.Page("pages/upload.py", title="Upload Dataset", icon="📤")
analytics_page = st.Page("pages/analytics.py", title="Analytics", icon="📊")
charts_page = st.Page("pages/charts.py", title="Charts", icon="📈")
statistics_page = st.Page("pages/statistics.py", title="Statistics", icon="🧮")
reports_page = st.Page("pages/reports.py", title="Reports", icon="📋")
strategy_page = st.Page("pages/strategy.py", title="Strategy", icon="🧠")
trading_bot_page = st.Page("pages/trading_bot.py", title="Trading Bot", icon="🤖")
logs_page = st.Page("pages/logs.py", title="Logs", icon="📜")
settings_page = st.Page("pages/settings.py", title="Settings", icon="⚙️")

# Build Navigation Menu
pg = st.navigation(
    {
        "Overview": [home_page, upload_page, logs_page, settings_page],
        "Analytics & Reports": [analytics_page, charts_page, statistics_page, reports_page],
        "Trading Desk": [strategy_page, trading_bot_page],
    }
)

# Run Custom styles injection
inject_custom_styles()

# Render Active Sidebar Info Panel
st.sidebar.markdown("---")
st.sidebar.subheader("⚡ System Profiles")

# Display loaded dataset
active_name = st.session_state.active_dataset_name
if active_name:
    st.sidebar.info(f"📂 **Active File**:\n`{active_name}`")
else:
    st.sidebar.warning("📂 No dataset active")

# Display bot connection status
mode_str = "🟢 Live Testnet" if st.session_state.bot_live_mode else "🟡 Dry Run (Sim)"
st.sidebar.info(f"🤖 **Bot Mode**: {mode_str}")

# Add copyright footer
st.sidebar.markdown(
    """
    <div style='text-align: center; color: #718096; font-size: 0.75rem; margin-top: 50px;'>
        PrimeTrade AI v1.1.0<br>© 2026 Google DeepMind Team
    </div>
    """,
    unsafe_allow_html=True,
)

# Render selected page content
pg.run()
