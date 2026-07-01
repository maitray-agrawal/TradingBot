from typing import Literal

import pandas as pd

from utils.logger import analytics_logger


class DatasetMerger:
    """
    Merges Historical Trader Data and Fear & Greed Index Data.
    Supports multiple merge strategies: 'same_day', 'nearest', or 'backward' (to prevent lookahead bias).
    """

    @staticmethod
    def merge_datasets(
        trader_df: pd.DataFrame,
        fg_df: pd.DataFrame,
        strategy: Literal["same_day", "nearest", "backward"] = "nearest",
    ) -> pd.DataFrame:
        """
        Merges trader data with Fear & Greed Index data.

        Parameters:
            trader_df (pd.DataFrame): Cleaned and feature-engineered trader data.
            fg_df (pd.DataFrame): Cleaned Fear & Greed Index data.
            strategy (str): 'same_day', 'nearest', or 'backward'.

        Returns:
            pd.DataFrame: Combined dataset.
        """
        if trader_df.empty:
            analytics_logger.warning("Trader dataframe is empty. Merged output will be empty.")
            return trader_df.copy()

        if fg_df.empty:
            analytics_logger.warning("Fear & Greed dataframe is empty. Cannot merge. Returning trader data.")
            # Add null columns for alignment
            result = trader_df.copy()
            result["fg_value"] = None
            result["fg_classification"] = None
            return result

        # Ensure working copies and cast timestamps to identical precision (datetime64[ns])
        trader_df = trader_df.copy()
        fg_df = fg_df.copy()

        trader_df["timestamp"] = pd.to_datetime(trader_df["timestamp"]).dt.tz_localize(None).astype("datetime64[ns]")
        fg_df["timestamp"] = pd.to_datetime(fg_df["timestamp"]).dt.tz_localize(None).astype("datetime64[ns]")

        # Sort by timestamp
        trader_df.sort_values(by="timestamp", inplace=True)
        fg_df.sort_values(by="timestamp", inplace=True)

        # Prepare Fear & Greed dataset by renaming columns to prevent collision
        fg_cols_to_keep = ["timestamp", "value", "classification"]
        fg_df = fg_df[[c for c in fg_cols_to_keep if c in fg_df.columns]].copy()
        fg_df.rename(
            columns={"value": "fg_value", "classification": "fg_classification"},
            inplace=True,
        )

        analytics_logger.info(
            f"Merging trader data ({len(trader_df)} rows) with Fear & Greed data ({len(fg_df)} rows) using strategy: {strategy}..."
        )

        if strategy == "same_day":
            # Extract date for daily merging
            trader_df["temp_date"] = trader_df["timestamp"].dt.date
            fg_df["temp_date"] = fg_df["timestamp"].dt.date

            # Since Fear & Greed might have duplicate days, drop duplicates on temp_date first
            fg_df.drop_duplicates(subset=["temp_date"], keep="first", inplace=True)

            # Merge on temp_date
            merged_df = pd.merge(trader_df, fg_df.drop(columns=["timestamp"]), on="temp_date", how="left")
            merged_df.drop(columns=["temp_date"], inplace=True)

        elif strategy in ("nearest", "backward"):
            # Use pd.merge_asof
            # If 'backward', matches values where fg_timestamp <= trader_timestamp (no lookahead)
            # If 'nearest', matches closest fg_timestamp regardless of direction
            merged_df = pd.merge_asof(trader_df, fg_df, on="timestamp", direction=strategy)
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

        analytics_logger.info(f"Successfully merged datasets. Total rows: {len(merged_df)}")
        return merged_df
