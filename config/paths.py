"""Centralized path management for PrimeTrade AI.

All paths are handled as pathlib.Path objects relative to the project root directory.
"""

from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
UPLOADS_DATA_DIR = DATA_DIR / "uploads"
EXPORTS_DATA_DIR = DATA_DIR / "exports"

# Logging Directories
SYSTEM_LOG_DIR = PROJECT_ROOT / "logs"
BOT_LOG_DIR = PROJECT_ROOT / "trading_bot" / "logs"

# Analytics Directories
ANALYTICS_DIR = PROJECT_ROOT / "analytics"
ANALYTICS_OUTPUT_DIR = ANALYTICS_DIR / "outputs"
CHARTS_OUTPUT_DIR = ANALYTICS_OUTPUT_DIR / "charts"
REPORTS_OUTPUT_DIR = ANALYTICS_DIR / "reports" / "generated"
NOTEBOOKS_DIR = ANALYTICS_DIR / "notebooks"

# Dashboard Directories
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DASHBOARD_PAGES_DIR = DASHBOARD_DIR / "pages"
DASHBOARD_COMPONENTS_DIR = DASHBOARD_DIR / "components"
DASHBOARD_ASSETS_DIR = DASHBOARD_DIR / "assets"

# Docs and Tests
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"

# Config directory
CONFIG_DIR = PROJECT_ROOT / "config"

# List of all directories that must exist at runtime
REQUIRED_DIRECTORIES = [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    UPLOADS_DATA_DIR,
    EXPORTS_DATA_DIR,
    SYSTEM_LOG_DIR,
    BOT_LOG_DIR,
    ANALYTICS_OUTPUT_DIR,
    CHARTS_OUTPUT_DIR,
    REPORTS_OUTPUT_DIR,
    NOTEBOOKS_DIR,
    DASHBOARD_PAGES_DIR,
    DASHBOARD_COMPONENTS_DIR,
    DASHBOARD_ASSETS_DIR,
    DOCS_DIR,
    TESTS_DIR,
]


def ensure_directories_exist() -> None:
    """Creates all required directories in the project structure if they do not exist."""
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
