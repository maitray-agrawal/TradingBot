"""Column standardization and normalization rules for datasets."""

from typing import Dict, List, Optional
from typing import Any, Optional

import pandas as pd

# Default mapping dictionary for column name standardization.
# The keys represent normalized lowercase versions of expected variations.
DEFAULT_COLUMN_MAP: Dict[str, str] = {
    # Execution price
    "executionprice": "execution_price",
    "execution_price": "execution_price",
    "execprice": "execution_price",
    "exec_price": "execution_price",
    "price": "execution_price",
    # Closed PnL
    "closedpnl": "closed_pnl",
    "closed_pnl": "closed_pnl",
    "realizedpnl": "closed_pnl",
    "realized_pnl": "closed_pnl",
    "profit": "closed_pnl",
    "pnl": "closed_pnl",
    "profit_loss": "closed_pnl",
    "profitloss": "closed_pnl",
    # Symbol
    "coin": "symbol",
    "symbol": "symbol",
    "asset": "symbol",
    "ticker": "symbol",
    # Timestamp
    "timestamp": "timestamp",
    "date": "timestamp",
    "time": "timestamp",
    "datetime": "timestamp",
    "time_stamp": "timestamp",
    # Size
    "size": "size",
    "amount": "size",
    "qty": "size",
    "quantity": "size",
    # Side
    "side": "side",
    "direction": "side",
    # Fee
    "fee": "fees",
    "fees": "fees",
    "commission": "fees",
    # Transaction Hash
    "txhash": "tx_hash",
    "tx_hash": "tx_hash",
    "transactionhash": "tx_hash",
    "transaction_hash": "tx_hash",
    "tx_id": "tx_hash",
    "txid": "tx_hash",
    # Trade ID
    "tradeid": "trade_id",
    "trade_id": "trade_id",
    "id": "trade_id",
    # Account
    "account": "account_id",
    "accountid": "account_id",
    "account_id": "account_id",
    # Classification (Fear & Greed)
    "classification": "classification",
    "sentiment": "classification",
    "sentiment_classification": "classification",
    # Value (Fear & Greed)
    "value": "value",
    "fear_greed_value": "value",
    "score": "value",
    # Fear component
    "fear": "fear",
    # Greed component
    "greed": "greed",
}


class SchemaMapper:
    """Manages header standardization and mapping dictionaries."""

    def __init__(self, mapping_dict: Optional[Dict[str, str]] = None) -> None:
        """Initializes the mapper with a standard or custom map.

        Args:
            mapping_dict: Custom replacement rules mapping raw strings to clean targets.
        """
        raw_map = mapping_dict if mapping_dict is not None else DEFAULT_COLUMN_MAP
        # Dynamically normalize the keys of the mapping dict to guarantee matching
        self.mapping_dict = {self._normalize_string(k): v for k, v in raw_map.items()}

    def _normalize_string(self, text: str) -> str:
        """Strips casing, spaces, underscores, and hyphens to create a lookup key.

        Args:
            text: Raw header name.

        Returns:
            Normalized lowercase lookup key.
        """
        return "".join(c for c in text.lower() if c.isalnum())

    def get_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """Generates a mapping from raw columns to standardized names.

        Args:
            columns: List of raw headers.

        Returns:
            Dictionary matching raw name to standard name.
        """
        mapping = {}
        seen_targets = set()
        for col in columns:
            normalized_key = self._normalize_string(col)
            if normalized_key in self.mapping_dict:
                target = self.mapping_dict[normalized_key]
            else:
                # If no mapping exists, convert to snake_case format
                clean_name = col.strip().lower().replace(" ", "_").replace("-", "_")
                target = "".join(c for c in clean_name if c.isalnum() or c == "_")

            # De-duplicate target names to guarantee uniqueness
            final_target = target
            counter = 1
            while final_target in seen_targets:
                final_target = f"{target}_{counter}"
                counter += 1
            seen_targets.add(final_target)
            mapping[col] = final_target
        return mapping

    def standardize_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, str]]:
        """Standardizes the headers of a DataFrame.

        Args:
            df: Raw input DataFrame.

        Returns:
            Tuple containing the standardized DataFrame and the mapping dictionary used.
        """
        mapping = self.get_column_mapping(list(df.columns))
        renamed_df = df.rename(columns=mapping)
        return renamed_df, mapping

    @staticmethod
    def normalize_trading_side(side_val: Any) -> Optional[str]:
        """Normalizes transaction side values to BUY or SELL.

        Args:
            side_val: Value representing order direction.

        Returns:
            Normalized side ('BUY', 'SELL') or None if unrecognized.
        """
        if pd.isna(side_val):
            return None
        val_str = str(side_val).strip().upper()
        if val_str in ("BUY", "LONG", "B", "1", "1.0", "L"):
            return "BUY"
        if val_str in ("SELL", "SHORT", "S", "-1", "-1.0", "SH"):
            return "SELL"
        return None
