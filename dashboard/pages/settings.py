"""Settings Page for the PrimeTrade AI dashboard."""

import os
from pathlib import Path
import streamlit as st

from config import settings
from dashboard.components import hero_banner

hero_banner(
    title="⚙️ Configuration & Environment Settings",
    subtitle="Edit Binance credentials, logging severity levels, paths, and environment settings.",
)

env_path = Path(".env")

# Reads active environment configurations
env_vars = {}
if env_path.exists():
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    except Exception as e:
        st.error(f"Failed to read .env file: {e}")

st.subheader("🛠️ Environment Variable Editor (.env)")

binance_key = st.text_input(
    "BINANCE_API_KEY",
    value=env_vars.get("BINANCE_API_KEY", ""),
    type="password",
    help="Binance Futures Testnet API Key",
)
binance_secret = st.text_input(
    "BINANCE_SECRET_KEY",
    value=env_vars.get("BINANCE_SECRET_KEY", ""),
    type="password",
    help="Binance Futures Testnet Secret Key",
)
testnet_url = st.text_input(
    "TESTNET_URL",
    value=env_vars.get("TESTNET_URL", "https://testnet.binancefuture.com"),
    help="Base URL for Testnet trading endpoints",
)

project_env = st.selectbox(
    "PROJECT_ENV",
    options=["DEVELOPMENT", "PRODUCTION", "STAGING"],
    index=["DEVELOPMENT", "PRODUCTION", "STAGING"].index(env_vars.get("PROJECT_ENV", "DEVELOPMENT")),
)

log_level = st.selectbox(
    "LOG_LEVEL",
    options=["DEBUG", "INFO", "WARNING", "ERROR"],
    index=["DEBUG", "INFO", "WARNING", "ERROR"].index(env_vars.get("LOG_LEVEL", "INFO")),
)

data_dir = st.text_input(
    "DATA_DIRECTORY",
    value=env_vars.get("DATA_DIRECTORY", "data"),
    help="Local path to data archives storage",
)

if st.button("💾 Save Settings & Update Profile"):
    with st.spinner("Writing environment parameters to .env..."):
        try:
            # Reconstruct content
            lines = [
                "# PrimeTrade AI - Local Environment Configuration",
                f"BINANCE_API_KEY={binance_key}",
                f"BINANCE_SECRET_KEY={binance_secret}",
                f"TESTNET_URL={testnet_url}",
                f"PROJECT_ENV={project_env}",
                f"LOG_LEVEL={log_level}",
                f"DATA_DIRECTORY={data_dir}",
                "",
            ]
            
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
                
            st.success("✅ Configuration successfully saved! Please restart the application for all settings to take effect.")
            
            # Dynamically reload active settings in-memory
            settings.binance_api_key = binance_key
            settings.binance_secret_key = binance_secret
            settings.testnet_url = testnet_url
            settings.project_env = project_env
            settings.log_level = log_level
            settings.data_directory = data_dir
            
            # Check has credentials flag
            st.session_state.has_credentials = bool(binance_key and binance_secret)
            
        except Exception as e:
            st.error(f"❌ Failed to save configuration: {e}")
            
# Show paths configuration overview
st.markdown("---")
st.subheader("📂 Directory Locations Reference")
st.markdown(
    f"""
    - **Raw Uploads Directory**: `data/uploads/`
    - **Processed Store Directory**: `data/processed/`
    - **Analytics Output Directory**: `analytics/outputs/`
    - **Generated PDF/HTML Reports**: `analytics/reports/generated/`
    """
)
