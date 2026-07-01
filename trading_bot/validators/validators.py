"""Pre-trade validation rules and filters for PrimeTrade AI.

Ensures that order parameters conform to Binance API filters (such as Lot Size,
Price Filters, and Min Notional bounds) and verifies wallet margin sufficiency.
"""

import logging
import math
from typing import Any, Dict

from config.enums import OrderType
from trading_bot.client.client import BinanceTestnetClient
from trading_bot.orders.orders import FuturesOrder
from utils.exceptions import ValidationError as BotValidationError

logger = logging.getLogger("bot")


class OrderValidator:
    """Pre-order verification and sanitization engine."""

    def __init__(self) -> None:
        """Initializes the validator."""
        pass

    def validate_leverage(self, symbol: str, leverage: int) -> None:
        """Ensures the selected leverage factor falls within acceptable bounds.

        Args:
            symbol: Target ticker symbol.
            leverage: Leverage multiplier.
        """
        if not (1 <= leverage <= 125):
            raise BotValidationError(
                f"Leverage '{leverage}' is out of bounds for symbol '{symbol}'. "
                "Must be an integer between 1 and 125."
            )

    def validate_notional_and_lot_size(
        self,
        client: BinanceTestnetClient,
        symbol: str,
        quantity: float,
        price: float | None = None,
    ) -> Dict[str, float]:
        """Validates and rounds price and quantity parameters against exchange rules.

        Checks symbol availability, LOT_SIZE filters, PRICE_FILTER filters, and
        MIN_NOTIONAL limits.

        Args:
            client: Instantiated BinanceTestnetClient.
            symbol: Target ticker symbol.
            quantity: Intended order size.
            price: Intended limit price (optional).

        Returns:
            Dictionary containing 'quantity' and 'price' formatted/rounded to
            exact tick size and step size precision limits.
        """
        symbol = symbol.upper()
        logger.debug(f"Validating lot size and filters for {symbol}")

        # Fetch exchange filters
        exchange_info = client.get_exchange_info()
        symbol_info = None
        for sym in exchange_info.get("symbols", []):
            if sym.get("symbol") == symbol:
                symbol_info = sym
                break

        if not symbol_info:
            raise BotValidationError(
                f"Symbol '{symbol}' is not supported by the exchange or testnet."
            )

        if symbol_info.get("status") != "TRADING":
            raise BotValidationError(
                f"Symbol '{symbol}' is currently offline (status: {symbol_info.get('status')})."
            )

        # Parse precision configuration
        qty_precision = int(symbol_info.get("quantityPrecision", 8))
        price_precision = int(symbol_info.get("pricePrecision", 8))

        # Default filter variables
        min_qty = 0.0
        max_qty = 9999999.0
        step_size = 10 ** (-qty_precision)

        min_price = 0.0
        max_price = 9999999.0
        tick_size = 10 ** (-price_precision)

        min_notional = 5.0  # Binance standard minimum notional for futures is typically 5-10 USDT

        # Parse filters list
        for filt in symbol_info.get("filters", []):
            f_type = filt.get("filterType")
            if f_type == "LOT_SIZE":
                min_qty = float(filt.get("minQty", 0.0))
                max_qty = float(filt.get("maxQty", 9999999.0))
                step_size = float(filt.get("stepSize", step_size))
            elif f_type == "PRICE_FILTER":
                min_price = float(filt.get("minPrice", 0.0))
                max_price = float(filt.get("maxPrice", 9999999.0))
                tick_size = float(filt.get("tickSize", tick_size))
            elif f_type == "MIN_NOTIONAL":
                min_notional = float(filt.get("notional", min_notional))

        # Helper: round value to specified step size precision
        def round_step(val: float, step: float) -> float:
            if not step:
                return val
            prec = max(0, int(-math.log10(step)))
            rounded = round(round(val / step) * step, prec)
            # Handle float epsilon
            return float(f"{rounded:.{prec}f}")

        # Round quantity
        rounded_qty = round_step(quantity, step_size)
        if rounded_qty < min_qty:
            raise BotValidationError(
                f"Order quantity {quantity} (rounded: {rounded_qty}) violates LOT_SIZE minimum of {min_qty} for {symbol}."
            )
        if rounded_qty > max_qty:
            raise BotValidationError(
                f"Order quantity {quantity} (rounded: {rounded_qty}) violates LOT_SIZE maximum of {max_qty} for {symbol}."
            )

        # Round price if provided
        rounded_price = None
        if price is not None:
            rounded_price = round_step(price, tick_size)
            if rounded_price < min_price:
                raise BotValidationError(
                    f"Order price {price} (rounded: {rounded_price}) violates PRICE_FILTER minimum of {min_price} for {symbol}."
                )
            if rounded_price > max_price:
                raise BotValidationError(
                    f"Order price {price} (rounded: {rounded_price}) violates PRICE_FILTER maximum of {max_price} for {symbol}."
                )

        # Evaluate Notional Value: qty * price
        eval_price = rounded_price
        if eval_price is None:
            # For market orders, fetch current mark price
            pos = client.get_position(symbol)
            eval_price = float(pos.get("markPrice", 0.0))
            if eval_price == 0.0:
                # Fallback if no markPrice available
                eval_price = 1.0

        notional_value = rounded_qty * eval_price
        if notional_value < min_notional:
            raise BotValidationError(
                f"Order value of {notional_value:.2f} USDT is below the MIN_NOTIONAL limit of {min_notional} USDT for {symbol}."
            )

        return {
            "quantity": rounded_qty,
            "price": rounded_price if rounded_price is not None else 0.0,
        }

    def validate_margin_requirements(
        self, client: BinanceTestnetClient, order: FuturesOrder, leverage: int
    ) -> None:
        """Verifies if wallet available balance satisfies the order initial margin requirement.

        Initial Margin = (Quantity * Price) / Leverage

        Args:
            client: Instantiated BinanceTestnetClient.
            order: Configured FuturesOrder.
            leverage: Active leverage factor.
        """
        logger.debug(f"Validating margin requirement for order: {order.symbol} at {leverage}x leverage.")

        # Query account balance
        available_balance = client.get_balance("USDT")

        # Estimate order cost price
        eval_price = order.price
        if eval_price is None:
            # If market order, fetch current mark price
            pos = client.get_position(order.symbol)
            eval_price = float(pos.get("markPrice", 0.0))
            if eval_price == 0.0:
                # If mark price cannot be fetched, throw error
                raise BotValidationError(
                    f"Unable to validate margin requirements. Mark price for '{order.symbol}' is not available."
                )

        required_margin = (order.quantity * eval_price) / leverage

        if available_balance < required_margin:
            raise BotValidationError(
                f"Insufficient funds for order. Required Margin: {required_margin:.2f} USDT. "
                f"Available Wallet Balance: {available_balance:.2f} USDT."
            )

        logger.debug(
            f"Margin check passed: Required: {required_margin:.2f} USDT, "
            f"Available: {available_balance:.2f} USDT."
        )
