"""Position tracker and margin controller for PrimeTrade AI.

Monitors active derivatives exposures, tracks liquidation boundaries, and adjusts
contract leverage/margin modes.
"""

import logging
from typing import Any, Dict, List

from trading_bot.client.client import BinanceTestnetClient

logger = logging.getLogger("bot")


class PositionManager:
    """Derivatives position manager class."""

    def __init__(self, client: BinanceTestnetClient) -> None:
        """Initializes PositionManager with a client.

        Args:
            client: Instantiated BinanceTestnetClient.
        """
        self.client = client

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Queries and returns all open positions (size > 0).

        Returns:
            List of normalized active position profiles.
        """
        logger.debug("Retrieving active exchange positions.")

        active_positions: List[Dict[str, Any]] = []

        if self.client.dry_run:
            # Gather in-memory simulated positions
            for symbol, pos in self.client.mock_positions.items():
                amt = float(pos.get("positionAmt", "0.0"))
                if amt != 0.0:
                    active_positions.append(self._normalize_position(pos))
            return active_positions

        try:
            # Query all symbol positions
            all_positions = self.client.client.futures_position_information()
            for pos in all_positions:
                amt = float(pos.get("positionAmt", "0.0"))
                if amt != 0.0:
                    active_positions.append(self._normalize_position(pos))
            return active_positions
        except Exception as e:
            logger.error(f"Failed to query active positions from Testnet: {e}")
            return []

    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Adjusts the contract leverage settings for a symbol.

        Args:
            symbol: Target ticker symbol.
            leverage: Leverage multiplier.

        Returns:
            Binance response metadata.
        """
        symbol = symbol.upper()
        logger.info(f"Setting leverage to {leverage}x on {symbol}")
        return self.client.change_leverage(symbol, leverage)

    def set_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """Adjusts the margin allocation mode (CROSSED or ISOLATED) for a symbol.

        Args:
            symbol: Target ticker symbol.
            margin_type: Target mode ('ISOLATED' or 'CROSS').

        Returns:
            Binance response metadata.
        """
        symbol = symbol.upper()
        # Standardize "CROSS" to "CROSSED" for Binance API
        api_type = "CROSSED" if margin_type.strip().upper() in ("CROSS", "CROSSED") else "ISOLATED"
        logger.info(f"Setting margin allocation model to {api_type} on {symbol}")
        return self.client.change_margin_type(symbol, api_type)

    def _normalize_position(self, raw_pos: Dict[str, Any]) -> Dict[str, Any]:
        """Converts raw API position dictionaries into a standard format.

        Args:
            raw_pos: Raw exchange response position dictionary.

        Returns:
            Normalized dictionary profile.
        """
        amt = float(raw_pos.get("positionAmt", 0.0))
        direction = "LONG" if amt > 0.0 else "SHORT"

        return {
            "symbol": raw_pos.get("symbol", "").upper(),
            "size": abs(amt),
            "raw_size": amt,
            "direction": direction,
            "entry_price": float(raw_pos.get("entryPrice", 0.0)),
            "mark_price": float(raw_pos.get("markPrice", 0.0)),
            "liquidation_price": float(raw_pos.get("liquidationPrice", 0.0)),
            "unrealized_pnl": float(raw_pos.get("unRealizedProfit", 0.0)),
            "leverage": int(raw_pos.get("leverage", 10)),
            "margin_type": raw_pos.get("marginType", "cross").upper(),
        }
