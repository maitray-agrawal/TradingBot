import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from config.settings import settings
from utils.logger import analytics_logger

class DataNormalizer:
    """
    Loads, normalizes headers, cleans data anomalies, handles missing values,
    and converts data types for Fear & Greed Index and Historical Trader Data.
    """

    # Mapping from normalized file column name (no space/underscore, lower) to standard name
    COLUMN_MAPPINGS = {
        "timestamp": "timestamp",
        "date": "timestamp",
        "time": "timestamp",
        "datetime": "timestamp",
        "coin": "symbol",
        "symbol": "symbol",
        "asset": "symbol",
        "executionprice": "execution_price",
        "price": "execution_price",
        "execprice": "execution_price",
        "closedpnl": "closed_pnl",
        "pnl": "closed_pnl",
        "profit": "closed_pnl",
        "profitloss": "closed_pnl",
        "side": "side",
        "direction": "side",
        "size": "size",
        "amount": "size",
        "qty": "size",
        "quantity": "size",
        "account": "account",
        "classification": "classification",
        "value": "value"
    }

    @classmethod
    def normalize_headers(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Maps dataframe columns to standard names using COLUMN_MAPPINGS.
        Intelligently resolves naming conflicts where multiple source columns
        normalize to the same target name.
        """
        df = df.copy()
        
        # Build mapping of original_col -> target_col
        rename_map = {}
        for col in df.columns:
            norm_col = str(col).strip().lower().replace("_", "").replace(" ", "")
            if norm_col in cls.COLUMN_MAPPINGS:
                rename_map[col] = cls.COLUMN_MAPPINGS[norm_col]

        # Group original columns by their normalized target name
        target_to_orig = {}
        for orig, target in rename_map.items():
            target_to_orig.setdefault(target, []).append(orig)

        final_rename = {}
        cols_to_drop = []

        for target, origs in target_to_orig.items():
            if len(origs) == 1:
                final_rename[origs[0]] = target
            else:
                # Resolve conflict by prioritizing specific patterns
                analytics_logger.warning(f"Column normalization conflict for '{target}': multiple source columns {origs}")
                prioritized = None
                
                if target == "symbol":
                    # Prioritize exact 'Symbol' match over 'Coin' or 'Asset'
                    for orig in origs:
                        if "symbol" in orig.lower():
                            prioritized = orig
                            break
                elif target == "execution_price":
                    # Prioritize 'execution price' over 'price'
                    for orig in origs:
                        if "execution" in orig.lower():
                            prioritized = orig
                            break

                # Fallback to the first item if no specific priority was found
                if prioritized is None:
                    prioritized = origs[0]

                final_rename[prioritized] = target
                # Mark other conflicting source columns for deletion
                for orig in origs:
                    if orig != prioritized:
                        cols_to_drop.append(orig)

        # Drop duplicate/conflicting source columns
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)
            analytics_logger.info(f"Dropped conflicting source columns to resolve standardization: {cols_to_drop}")

        df.rename(columns=final_rename, inplace=True)
        analytics_logger.info(f"Normalized columns. Renamed: {final_rename}")
        return df

    @staticmethod
    def load_file(file_path: Path) -> pd.DataFrame:
        """Load data file based on its file format."""
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(file_path)
        elif suffix == ".xlsx":
            return pd.read_excel(file_path)
        elif suffix == ".json":
            return pd.read_json(file_path)
        elif suffix == ".parquet":
            return pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def convert_timestamp(series: pd.Series) -> pd.Series:
        """
        Convert series to datetime series. Supports timestamps (seconds/milliseconds)
        as well as date string formats.
        """
        # Try numeric conversion (unix timestamps)
        try:
            # Check if values look like unix timestamps (e.g. > 1e9)
            numeric_series = pd.to_numeric(series, errors='coerce')
            if not numeric_series.isna().all():
                # Detect seconds vs milliseconds
                # e.g., year 2020 in seconds is 1.57e9, in ms it is 1.57e12
                # If median is > 1e11, it is likely milliseconds
                median_val = numeric_series.dropna().median()
                if median_val > 1e11:
                    return pd.to_datetime(numeric_series, unit='ms', errors='coerce')
                else:
                    return pd.to_datetime(numeric_series, unit='s', errors='coerce')
        except Exception:
            pass

        # Fallback to standard string parsing
        return pd.to_datetime(series, errors='coerce')

    def clean_trader_data(self, file_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Cleans and standardizes Historical Trader Data.
        """
        df = self.load_file(file_path)
        initial_rows = len(df)
        
        # 1. Normalize headers
        df = self.normalize_headers(df)
        
        # 2. Check for required columns
        required_cols = {"timestamp", "symbol", "execution_price", "closed_pnl", "side", "size"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            analytics_logger.warning(f"Trader dataset {file_path.name} is missing columns: {missing_cols}. Will try to clean anyway.")

        # 3. Remove duplicates
        df.drop_duplicates(inplace=True)
        dup_rows_removed = initial_rows - len(df)
        
        # 4. Handle missing values in key columns
        df.dropna(subset=[col for col in required_cols if col in df.columns], inplace=True)
        null_rows_removed = initial_rows - dup_rows_removed - len(df)

        # 5. Fix datatypes and convert timestamps
        if "timestamp" in df.columns:
            df["timestamp"] = self.convert_timestamp(df["timestamp"])
            # Remove rows where timestamp couldn't be parsed
            df.dropna(subset=["timestamp"], inplace=True)
        
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
            
        for float_col in ["execution_price", "closed_pnl", "size"]:
            if float_col in df.columns:
                df[float_col] = pd.to_numeric(df[float_col], errors='coerce')
        
        # 6. Normalize trade sides
        if "side" in df.columns:
            df["side"] = df["side"].astype(str).str.upper().str.strip()
            # Map buy/sell alternatives
            side_map = {
                "BUY": "BUY", "LONG": "BUY", "L": "BUY", "B": "BUY",
                "SELL": "SELL", "SHORT": "SELL", "S": "SELL"
            }
            df["side"] = df["side"].map(side_map)
            df.dropna(subset=["side"], inplace=True)

        # 7. Remove impossible values (e.g. execution_price <= 0 or size <= 0)
        invalid_values_removed = 0
        if "execution_price" in df.columns:
            valid_price_mask = df["execution_price"] > 0
            invalid_values_removed += len(df) - df[valid_price_mask].shape[0]
            df = df[valid_price_mask]
            
        if "size" in df.columns:
            valid_size_mask = df["size"] > 0
            invalid_values_removed += len(df) - df[valid_size_mask].shape[0]
            df = df[valid_size_mask]

        final_rows = len(df)
        cleaning_summary = {
            "initial_rows": initial_rows,
            "final_rows": final_rows,
            "duplicates_removed": dup_rows_removed,
            "null_rows_removed": null_rows_removed,
            "invalid_values_removed": invalid_values_removed
        }
        
        analytics_logger.info(f"Trader Data Cleaning Summary: {cleaning_summary}")
        return df.reset_index(drop=True), cleaning_summary

    def clean_fear_greed_data(self, file_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Cleans and standardizes Fear & Greed Index data.
        """
        df = self.load_file(file_path)
        initial_rows = len(df)

        # 1. Normalize headers
        df = self.normalize_headers(df)

        # 2. Check required columns
        required_cols = {"timestamp", "value", "classification"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            analytics_logger.warning(f"Fear & Greed dataset {file_path.name} is missing columns: {missing_cols}")

        # 3. Remove duplicates
        df.drop_duplicates(inplace=True)
        dup_rows_removed = initial_rows - len(df)

        # 4. Handle missing values
        df.dropna(subset=[col for col in required_cols if col in df.columns], inplace=True)
        null_rows_removed = initial_rows - dup_rows_removed - len(df)

        # 5. Fix timestamps and value ranges
        if "timestamp" in df.columns:
            df["timestamp"] = self.convert_timestamp(df["timestamp"])
            # Strip time component if we only want dates, but keeping full timestamp is more flexible.
            # We'll normalize to date format for standard index merging.
            df.dropna(subset=["timestamp"], inplace=True)
            
        if "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors='coerce')
            df.dropna(subset=["value"], inplace=True)
            df["value"] = df["value"].astype(int)
            
            # Fear & Greed Index is always between 0 and 100
            valid_val_mask = (df["value"] >= 0) & (df["value"] <= 100)
            df = df[valid_val_mask]

        if "classification" in df.columns:
            df["classification"] = df["classification"].astype(str).str.strip().str.title()

        final_rows = len(df)
        cleaning_summary = {
            "initial_rows": initial_rows,
            "final_rows": final_rows,
            "duplicates_removed": dup_rows_removed,
            "null_rows_removed": null_rows_removed,
            "invalid_values_removed": initial_rows - dup_rows_removed - null_rows_removed - final_rows
        }

        analytics_logger.info(f"Fear & Greed Cleaning Summary: {cleaning_summary}")
        return df.reset_index(drop=True), cleaning_summary
