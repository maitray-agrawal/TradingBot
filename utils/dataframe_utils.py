"""Generic DataFrame utility helpers for PrimeTrade AI.

Contains operations for column cleaning, missing value profiling, and outlier 
detection based on interquartile ranges.
"""

from typing import Dict, List, Union
import numpy as np
import pandas as pd


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes DataFrame column headers by removing casing, spaces, and punctuation.

    Converts names to snake_case. For example, "Closed PnL ($)" -> "closed_pnl".

    Args:
        df: Input pandas DataFrame.

    Returns:
        DataFrame with standardized column names.
    """
    df_copy = df.copy()
    new_cols = []
    for col in df_copy.columns:
        col_str = str(col).strip().lower()
        # Replace spaces, hyphens, and underscores with single underscores
        col_str = col_str.replace(" ", "_").replace("-", "_")
        # Strip other special characters
        cleaned = "".join(c for c in col_str if c.isalnum() or c == "_")
        # Remove multiple consecutive underscores
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        new_cols.append(cleaned.strip("_"))

    df_copy.columns = new_cols
    return df_copy


def get_missing_value_report(df: pd.DataFrame) -> Dict[str, Dict[str, Union[int, float]]]:
    """Generates a summary of missing values in each column of the DataFrame.

    Args:
        df: Input pandas DataFrame.

    Returns:
        Dictionary mapping column names to missing counts and percentages.
    """
    total_rows = len(df)
    if total_rows == 0:
        return {}

    missing_info = {}
    null_counts = df.isnull().sum()

    for col in df.columns:
        count = int(null_counts[col])
        if count > 0:
            missing_info[col] = {
                "missing_count": count,
                "missing_percentage": round((count / total_rows) * 100.0, 2),
            }
    return missing_info


def detect_outliers_iqr(df: pd.DataFrame, column: str, k: float = 1.5) -> pd.Series:
    """Generates a boolean Series indicating where values are outliers using IQR.

    Args:
        df: Input pandas DataFrame.
        column: Name of the column to evaluate.
        k: Threshold multiplier (default 1.5).

    Returns:
        Boolean Series where True indicates an outlier.
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' does not exist in DataFrame.")

    col_data = df[column].dropna()
    if len(col_data) == 0:
        return pd.Series(False, index=df.index)

    q25 = np.percentile(col_data, 25)
    q75 = np.percentile(col_data, 75)
    iqr = q75 - q25

    lower_bound = q25 - (k * iqr)
    upper_bound = q75 + (k * iqr)

    return (df[column] < lower_bound) | (df[column] > upper_bound)
