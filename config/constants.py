"""Centralized constant values for PrimeTrade AI.

This module houses global constants including default trading bounds, API endpoints,
and display formats to avoid inline magic numbers.
"""

# API Defaults
DEFAULT_TESTNET_URL = "https://testnet.binancefuture.com"

# Risk & Order Limits
DEFAULT_LEVERAGE = 1
MAX_LEVERAGE = 25
MIN_ORDER_NOTIONAL = 5.0  # Binance Futures minimum trade amount in USDT
MAX_RISK_PER_TRADE = 0.05  # Maximum 5% of account balance risked per trade

# Sentiment Index Bounds
FEAR_GREED_MIN = 0
FEAR_GREED_MAX = 100

# Formatting
DECIMAL_PRECISION = 8
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Common tickers supported on Futures Testnet
SUPPORTED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"]
