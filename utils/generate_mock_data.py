from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from config.settings import settings
from utils.logger import analytics_logger


def generate_mock_datasets():
    """
    Generates mock Fear & Greed and historical trader datasets and saves them in the data/ folder.
    """
    data_dir = settings.DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    # Define start date and count
    start_date = datetime(2026, 6, 1)
    days = 30

    # 1. Generate Fear & Greed Index (CSV format)
    # Target columns: classification, value, date, timestamp
    fg_records = []
    for i in range(days):
        dt = start_date + timedelta(days=i)
        val = int(np.random.randint(15, 90))
        if val <= 25:
            classification = "Extreme Fear"
        elif val <= 45:
            classification = "Fear"
        elif val <= 55:
            classification = "Neutral"
        elif val <= 75:
            classification = "Greed"
        else:
            classification = "Extreme Greed"

        fg_records.append(
            {
                "timestamp": int(dt.timestamp() * 1000),  # millisecond unix
                "date": dt.strftime("%Y-%m-%d"),
                "value": val,
                "classification": classification,
            }
        )

    fg_df = pd.DataFrame(fg_records)
    fg_path = data_dir / "mock_fear_greed_index.csv"
    fg_df.to_csv(fg_path, index=False)
    analytics_logger.info(
        f"Saved mock Fear & Greed index to {fg_path} ({len(fg_df)} rows)."
    )

    # 2. Generate Historical Trader Dataset (XLSX format)
    # Target columns: account, coin, symbol, price, execution price, closed pnl, side, size, timestamp
    # We will purposely use different names like 'execution price', 'closed pnl', 'coin', 'side', 'size', 'timestamp'
    trader_records = []
    np.random.seed(42)
    symbols = ["BTCUSDT", "ETHUSDT"]
    base_prices = {"BTCUSDT": 60000.0, "ETHUSDT": 3000.0}

    # Generate ~150 trades over the 30-day period
    for i in range(150):
        # Random time within the 30 days
        seconds_offset = np.random.randint(0, days * 24 * 60 * 60)
        dt = start_date + timedelta(seconds=seconds_offset)
        symbol = np.random.choice(symbols)
        side = np.random.choice(["BUY", "SELL", "LONG", "SHORT"])
        size = round(
            (
                np.random.uniform(0.01, 1.5)
                if symbol == "BTCUSDT"
                else np.random.uniform(0.1, 15.0)
            ),
            4,
        )

        # execution price fluctuated around base price
        pct_change = np.random.normal(0, 0.02)
        execution_price = round(base_prices[symbol] * (1 + pct_change), 2)

        # closed pnl: can be positive or negative
        closed_pnl = round(np.random.normal(5.0, 150.0) * size, 2)

        trader_records.append(
            {
                "Account": "SubAccount_1",
                "Coin": symbol.replace("USDT", ""),
                "Symbol": symbol,
                "Execution Price": execution_price,
                "Closed PnL": closed_pnl,
                "Side": side,
                "Size": size,
                "Timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),  # string timestamp
            }
        )

    trader_df = pd.DataFrame(trader_records)
    # Let's insert a couple of duplicate rows and null values to test the cleaner
    trader_df = pd.concat(
        [
            trader_df,
            trader_df.iloc[[5, 10]],
            pd.DataFrame(
                [
                    {
                        "Account": "SubAccount_1",
                        "Coin": "BTC",
                        "Symbol": "BTCUSDT",
                        "Execution Price": np.nan,  # invalid price
                        "Closed PnL": 0.0,
                        "Side": "BUY",
                        "Size": 0.5,
                        "Timestamp": "2026-06-15 12:00:00",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    trader_path = data_dir / "mock_trader_history.xlsx"
    trader_df.to_excel(trader_path, index=False)
    analytics_logger.info(
        f"Saved mock Trader History to {trader_path} ({len(trader_df)} rows)."
    )


if __name__ == "__main__":
    generate_mock_datasets()
