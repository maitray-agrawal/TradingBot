"""Unified configuration exports for PrimeTrade AI."""

from config.constants import (DATE_FORMAT, DATETIME_FORMAT, DECIMAL_PRECISION,
                              DEFAULT_LEVERAGE, DEFAULT_TESTNET_URL,
                              FEAR_GREED_MAX, FEAR_GREED_MIN, MAX_LEVERAGE,
                              MAX_RISK_PER_TRADE, MIN_ORDER_NOTIONAL,
                              SUPPORTED_SYMBOLS)
from config.enums import (DatasetType, Environment, OrderType, SentimentRegime,
                          TradingSide)
from config.paths import (ANALYTICS_DIR, ANALYTICS_OUTPUT_DIR, BOT_LOG_DIR,
                          CHARTS_OUTPUT_DIR, CONFIG_DIR, DASHBOARD_ASSETS_DIR,
                          DASHBOARD_COMPONENTS_DIR, DASHBOARD_DIR,
                          DASHBOARD_PAGES_DIR, DATA_DIR, DOCS_DIR,
                          EXPORTS_DATA_DIR, NOTEBOOKS_DIR, PROCESSED_DATA_DIR,
                          PROJECT_ROOT, RAW_DATA_DIR, REPORTS_OUTPUT_DIR,
                          REQUIRED_DIRECTORIES, SYSTEM_LOG_DIR, TESTS_DIR,
                          UPLOADS_DATA_DIR, ensure_directories_exist)
from config.settings import settings

__all__ = [
    # Paths
    "PROJECT_ROOT",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "UPLOADS_DATA_DIR",
    "EXPORTS_DATA_DIR",
    "SYSTEM_LOG_DIR",
    "BOT_LOG_DIR",
    "ANALYTICS_DIR",
    "ANALYTICS_OUTPUT_DIR",
    "CHARTS_OUTPUT_DIR",
    "REPORTS_OUTPUT_DIR",
    "NOTEBOOKS_DIR",
    "DASHBOARD_DIR",
    "DASHBOARD_PAGES_DIR",
    "DASHBOARD_COMPONENTS_DIR",
    "DASHBOARD_ASSETS_DIR",
    "DOCS_DIR",
    "TESTS_DIR",
    "CONFIG_DIR",
    "REQUIRED_DIRECTORIES",
    "ensure_directories_exist",
    # Enums
    "Environment",
    "TradingSide",
    "OrderType",
    "DatasetType",
    "SentimentRegime",
    # Constants
    "DEFAULT_TESTNET_URL",
    "DEFAULT_LEVERAGE",
    "MAX_LEVERAGE",
    "MIN_ORDER_NOTIONAL",
    "MAX_RISK_PER_TRADE",
    "FEAR_GREED_MIN",
    "FEAR_GREED_MAX",
    "DECIMAL_PRECISION",
    "DATE_FORMAT",
    "DATETIME_FORMAT",
    "SUPPORTED_SYMBOLS",
    # Settings
    "settings",
]
