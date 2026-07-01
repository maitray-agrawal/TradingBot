from typing import Optional

import numpy as np
import pandas as pd

from utils.logger import analytics_logger


class FeatureGenerator:
    """
    Applies feature engineering to the cleaned Historical Trader Dataset.
    Ensures data is sorted chronologically before computing rolling and cumulative features.
    """

    @staticmethod
    def generate_features(df: pd.DataFrame, rolling_window: int = 10) -> pd.DataFrame:
        """
        Generates trading and time-based features on the cleaned dataframe.

        Parameters:
            df (pd.DataFrame): Cleaned historical trader data.
            rolling_window (int): Window size for rolling statistics.

        Returns:
            pd.DataFrame: Dataframe with added engineered features.
        """
        if df.empty:
            analytics_logger.warning("Empty dataframe passed to FeatureGenerator.")
            return df

        # Ensure working copy and chronological sorting
        df = df.copy()
        df.sort_values(by="timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)

        analytics_logger.info(f"Generating features for {len(df)} trade records...")

        # 1. Time-based Features
        df["hour"] = df["timestamp"].dt.hour
        df["day"] = df["timestamp"].dt.day
        df["weekday"] = df["timestamp"].dt.weekday  # 0=Monday, 6=Sunday
        df["month"] = df["timestamp"].dt.month
        df["week"] = df["timestamp"].dt.isocalendar().week.astype(int)

        # 2. Trade Direction & Value
        # BUY = 1, SELL = -1
        df["trade_direction"] = df["side"].map({"BUY": 1, "SELL": -1}).fillna(0).astype(int)

        # trade_value = size * execution_price (notational value of trade in quote currency)
        df["trade_value"] = df["size"] * df["execution_price"]

        # position_size equals size (coin quantity)
        df["position_size"] = df["size"]

        # 3. Profitability Features
        df["is_profit"] = (df["closed_pnl"] > 0).astype(int)

        # profit_percentage = closed_pnl / trade_value (avoiding division by zero)
        df["profit_percentage"] = np.where(df["trade_value"] > 0, (df["closed_pnl"] / df["trade_value"]) * 100, 0.0)

        # 4. Rolling and Cumulative Metrics (Computed chronologically)
        df["cumulative_pnl"] = df["closed_pnl"].cumsum()

        # Rolling pnl and volume
        df["rolling_pnl"] = df["closed_pnl"].rolling(window=rolling_window, min_periods=1).sum()
        df["rolling_volume"] = df["trade_value"].rolling(window=rolling_window, min_periods=1).sum()

        # 5. Daily Realized PnL
        # realized PnL per calendar day (grouping by date)
        temp_date = df["timestamp"].dt.date
        daily_pnl_map = df.groupby(temp_date)["closed_pnl"].sum().to_dict()
        df["daily_pnl"] = temp_date.map(daily_pnl_map)

        analytics_logger.info("Successfully completed feature engineering.")
        return df
