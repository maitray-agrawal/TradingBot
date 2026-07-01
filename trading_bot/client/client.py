"""Binance Futures Testnet client wrapper for PrimeTrade AI.

Integrates with python-binance, providing automated error retries, detailed
request-response logging, and a robust Dry Run execution engine.
"""

import functools
import logging
import random
import time
from typing import Any, Dict, List

from binance.client import Client
from binance.exceptions import BinanceAPIException

from config.settings import settings
from utils.exceptions import APIError, ConfigurationError, NetworkError, TradingBotError

logger = logging.getLogger("bot")


def retry_on_failure(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """Decorator to retry failing Binance API operations with exponential backoff.

    Retries only on connection errors or transient/rate-limiting errors (HTTP 429/418).
    Immediate failure is raised for parameter, logic, or balance errors.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.dry_run:
                return func(self, *args, **kwargs)

            last_ex = None
            delay = base_delay
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except BinanceAPIException as e:
                    # HTTP 429/418 or code -1003 is too many requests (rate limited)
                    # HTTP >= 500 represents server errors
                    is_rate_limit = (e.status_code == 429) or (e.status_code == 418) or (e.code == -1003)
                    is_server_error = (e.status_code >= 500) if e.status_code else False

                    if not (is_rate_limit or is_server_error):
                        # Client-side validation/balance issues should not retry
                        logger.error(f"Binance API returned client-side error: {e.message} (code={e.code})")
                        raise APIError(
                            message=f"Binance API error: {e.message}",
                            status_code=e.status_code,
                            details={"code": e.code, "message": e.message},
                        )

                    last_ex = e
                    sleep_time = delay + random.uniform(0.1, 0.5)
                    logger.warning(
                        f"Temporary Binance API error (code={e.code}, status={e.status_code}) "
                        f"on attempt {attempt + 1}/{max_retries}. Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    delay = min(delay * 2, max_delay)
                except Exception as e:
                    # Connection reset, timeouts, connection refused
                    last_ex = e
                    sleep_time = delay + random.uniform(0.1, 0.5)
                    logger.warning(
                        f"Network connection error on attempt {attempt + 1}/{max_retries}. "
                        f"Retrying in {sleep_time:.2f}s... Error: {e}"
                    )
                    time.sleep(sleep_time)
                    delay = min(delay * 2, max_delay)

            # Max retries exceeded
            if isinstance(last_ex, BinanceAPIException):
                raise APIError(
                    message=f"Request failed after {max_retries} attempts: {last_ex.message}",
                    status_code=last_ex.status_code,
                    details={"code": last_ex.code, "message": last_ex.message},
                )
            else:
                raise NetworkError(
                    message=f"Network request failed after {max_retries} attempts: {str(last_ex)}",
                    details={"last_error": str(last_ex)},
                )

        return wrapper

    return decorator


class BinanceTestnetClient:
    """Production-ready client wrapper for Binance Futures Testnet operations."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        dry_run: bool = False,
    ) -> None:
        """Initializes the BinanceTestnetClient.

        Args:
            api_key: Binance Testnet API key.
            api_secret: Binance Testnet secret key.
            dry_run: If True, operates in Dry Run simulation mode.
        """
        self.dry_run = dry_run
        self.api_key = api_key or settings.binance_api_key
        self.api_secret = api_secret or settings.binance_secret_key
        self.client: Client | None = None

        if self.dry_run:
            logger.info("Initializing Binance Futures Client in [DRY RUN] mode.")
            # In-memory structures for simulation
            self.mock_balance = 10000.0
            self.mock_positions: Dict[str, Dict[str, Any]] = {}
            self.mock_open_orders: Dict[str, List[Dict[str, Any]]] = {}
        else:
            logger.info("Initializing Binance Futures Client in [LIVE TESTNET] mode.")
            if not self.api_key or not self.api_secret:
                raise ConfigurationError(
                    "Missing BINANCE_API_KEY or BINANCE_SECRET_KEY. "
                    "Keys must be configured in environment or .env for live Testnet execution."
                )
            try:
                # Setting testnet=True points python-binance client base endpoints to Testnet URLs
                self.client = Client(api_key=self.api_key, api_secret=self.api_secret, testnet=True)
                logger.info("Live Testnet API connection established.")
            except Exception as e:
                raise NetworkError(
                    message=f"Failed to connect to Binance Futures Testnet: {e}",
                    details={"error": str(e)},
                )

    @retry_on_failure()
    def get_balance(self, asset: str = "USDT") -> float:
        """Retrieves available wallet balance for the specified asset.

        Args:
            asset: Asset identifier, defaults to 'USDT'.

        Returns:
            Free available margin balance as a float.
        """
        logger.debug(f"Querying wallet balance for asset: {asset}")
        if self.dry_run:
            return float(self.mock_balance)

        try:
            balances = self.client.futures_account_balance()
            for bal in balances:
                if bal.get("asset") == asset:
                    return float(bal.get("withdrawAvailable", 0.0))
            return 0.0
        except Exception as e:
            if not isinstance(e, TradingBotError):
                raise NetworkError(f"Failed to fetch account balance: {e}")
            raise

    @retry_on_failure()
    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Fetches active position parameters for a given symbol.

        Args:
            symbol: Target symbol string (e.g. 'BTCUSDT').

        Returns:
            Dictionary containing position parameters.
        """
        logger.debug(f"Querying active position for symbol: {symbol}")
        symbol = symbol.upper()

        if self.dry_run:
            # Returns existing position or default empty state
            if symbol not in self.mock_positions:
                self.mock_positions[symbol] = {
                    "symbol": symbol,
                    "positionAmt": "0.0",
                    "entryPrice": "0.0",
                    "markPrice": "60000.0",
                    "liquidationPrice": "0.0",
                    "unRealizedProfit": "0.0",
                    "marginType": "cross",
                    "leverage": "10",
                }
            return self.mock_positions[symbol]

        try:
            positions = self.client.futures_position_information(symbol=symbol)
            for pos in positions:
                if pos.get("symbol") == symbol:
                    return pos
            # If not found, return empty-like structure
            return {
                "symbol": symbol,
                "positionAmt": "0.0",
                "entryPrice": "0.0",
                "markPrice": "0.0",
                "liquidationPrice": "0.0",
                "unRealizedProfit": "0.0",
                "marginType": "cross",
                "leverage": "10",
            }
        except Exception as e:
            if not isinstance(e, TradingBotError):
                raise NetworkError(f"Failed to fetch position information: {e}")
            raise

    @retry_on_failure()
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """Submits an order to the Binance Futures exchange.

        Args:
            symbol: Target symbol string (e.g. 'BTCUSDT').
            side: Execution direction ('BUY' or 'SELL').
            order_type: Order type ('MARKET', 'LIMIT', 'STOP_LIMIT').
            quantity: Trade execution size.
            price: Execution price (required for LIMIT / STOP_LIMIT).
            stop_price: Stop trigger price (required for STOP_LIMIT).
            time_in_force: Time-in-force option (e.g. 'GTC', 'IOC').

        Returns:
            Dictionary containing order execution receipt.
        """
        symbol = symbol.upper()
        side = side.upper()
        order_type = order_type.upper()
        time_in_force = time_in_force.upper()

        logger.info(
            f"Submitting order request -> Symbol: {symbol}, Side: {side}, Type: {order_type}, "
            f"Qty: {quantity}, Price: {price}, StopPrice: {stop_price}, TIF: {time_in_force}"
        )

        if self.dry_run:
            # Simulate order receipt
            order_id = random.randint(1000000, 9999999)
            exec_price = price if price else stop_price if stop_price else 60000.0

            receipt = {
                "orderId": order_id,
                "symbol": symbol,
                "status": "NEW" if order_type in ("LIMIT", "STOP_LIMIT") else "FILLED",
                "clientOrderId": f"dry_run_{random.randint(100000, 999999)}",
                "price": str(price) if price else "0.0",
                "origQty": str(quantity),
                "cumQty": str(quantity) if order_type == "MARKET" else "0.0",
                "cumQuote": str(quantity * exec_price) if order_type == "MARKET" else "0.0",
                "side": side,
                "type": order_type,
                "timeInForce": time_in_force,
                "stopPrice": str(stop_price) if stop_price else "0.0",
                "updateTime": int(time.time() * 1000),
            }

            # Update mock positions for MARKET orders immediately
            if order_type == "MARKET":
                pos = self.get_position(symbol)
                current_amt = float(pos.get("positionAmt", "0.0"))
                trade_qty = quantity if side == "BUY" else -quantity
                new_amt = current_amt + trade_qty

                # Recalculate average entry price (simplistic simulation)
                entry_p = float(pos.get("entryPrice", "0.0"))
                if new_amt != 0.0:
                    if current_amt == 0.0:
                        entry_p = exec_price
                    elif (current_amt > 0 and trade_qty > 0) or (current_amt < 0 and trade_qty < 0):
                        entry_p = ((current_amt * entry_p) + (trade_qty * exec_price)) / new_amt
                else:
                    entry_p = 0.0

                pos["positionAmt"] = f"{new_amt:.3f}"
                pos["entryPrice"] = f"{entry_p:.2f}"
                pos["markPrice"] = f"{exec_price:.2f}"
                self.mock_positions[symbol] = pos

            elif order_type in ("LIMIT", "STOP_LIMIT"):
                if symbol not in self.mock_open_orders:
                    self.mock_open_orders[symbol] = []
                self.mock_open_orders[symbol].append(receipt)

            logger.debug(f"Dry Run Order Receipt generated: {receipt}")
            return receipt

        # Live Testnet request construction
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force
        elif order_type == "STOP_LIMIT":
            params["price"] = price
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force

        try:
            receipt = self.client.futures_create_order(**params)
            logger.info(f"Order successfully filled/created. Exchange OrderID: {receipt.get('orderId')}")
            logger.debug(f"Full Binance response: {receipt}")
            return receipt
        except Exception as e:
            if not isinstance(e, TradingBotError):
                raise NetworkError(f"Network failure during order execution: {e}")
            raise

    @retry_on_failure()
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancels a pending limit or stop order.

        Args:
            symbol: Target asset symbol.
            order_id: Numeric exchange ID of the active order.

        Returns:
            Order cancellation response details.
        """
        symbol = symbol.upper()
        logger.info(f"Requesting cancellation for order: {order_id} on {symbol}")

        if self.dry_run:
            if symbol in self.mock_open_orders:
                orders = self.mock_open_orders[symbol]
                for idx, o in enumerate(orders):
                    if o.get("orderId") == order_id:
                        cancelled = orders.pop(idx)
                        cancelled["status"] = "CANCELED"
                        return cancelled
            raise APIError(
                message=f"Order {order_id} not found on symbol {symbol}",
                status_code=400,
                details={"code": -2011, "message": "Unknown order"},
            )

        try:
            receipt = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Order {order_id} successfully cancelled.")
            return receipt
        except Exception as e:
            if not isinstance(e, TradingBotError):
                raise NetworkError(f"Failed to cancel order: {e}")
            raise

    @retry_on_failure()
    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Queries all active open pending orders on the exchange for a symbol.

        Args:
            symbol: Target symbol string.

        Returns:
            List of open orders dictionary records.
        """
        symbol = symbol.upper()
        logger.debug(f"Querying open orders for symbol: {symbol}")

        if self.dry_run:
            return self.mock_open_orders.get(symbol, [])

        try:
            return self.client.futures_get_open_orders(symbol=symbol)
        except Exception as e:
            if not isinstance(e, TradingBotError):
                raise NetworkError(f"Failed to retrieve open orders: {e}")
            raise

    @retry_on_failure()
    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetches complete exchange specification rules and asset filters."""
        logger.debug("Requesting exchange details.")

        if self.dry_run:
            # Return high-fidelity mock info for BTCUSDT and ETHUSDT to support validators
            return {
                "timezone": "UTC",
                "serverTime": int(time.time() * 1000),
                "symbols": [
                    {
                        "symbol": "BTCUSDT",
                        "status": "TRADING",
                        "baseAsset": "BTC",
                        "quoteAsset": "USDT",
                        "pricePrecision": 2,
                        "quantityPrecision": 3,
                        "filters": [
                            {
                                "filterType": "PRICE_FILTER",
                                "minPrice": "0.10",
                                "maxPrice": "1000000.00",
                                "tickSize": "0.10",
                            },
                            {
                                "filterType": "LOT_SIZE",
                                "minQty": "0.001",
                                "maxQty": "1000.000",
                                "stepSize": "0.001",
                            },
                            {
                                "filterType": "MIN_NOTIONAL",
                                "notional": "5.00",
                            },
                        ],
                    },
                    {
                        "symbol": "ETHUSDT",
                        "status": "TRADING",
                        "baseAsset": "ETH",
                        "quoteAsset": "USDT",
                        "pricePrecision": 2,
                        "quantityPrecision": 2,
                        "filters": [
                            {
                                "filterType": "PRICE_FILTER",
                                "minPrice": "0.01",
                                "maxPrice": "100000.00",
                                "tickSize": "0.01",
                            },
                            {
                                "filterType": "LOT_SIZE",
                                "minQty": "0.01",
                                "maxQty": "10000.00",
                                "stepSize": "0.01",
                            },
                            {
                                "filterType": "MIN_NOTIONAL",
                                "notional": "5.00",
                            },
                        ],
                    },
                ],
            }

        try:
            return self.client.futures_exchange_info()
        except Exception as e:
            raise NetworkError(f"Failed to query Binance exchange info: {e}")

    @retry_on_failure()
    def change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Adjusts the target trading leverage on Binance Futures.

        Args:
            symbol: Target symbol.
            leverage: Leverage multiplier.

        Returns:
            Leverage adjustment response metadata.
        """
        symbol = symbol.upper()
        logger.info(f"Requesting leverage change for {symbol} to: {leverage}x")

        if self.dry_run:
            pos = self.get_position(symbol)
            pos["leverage"] = str(leverage)
            return {"symbol": symbol, "leverage": leverage, "maxQty": "1000"}

        try:
            return self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
        except Exception as e:
            if not isinstance(e, TradingBotError):
                raise NetworkError(f"Failed to change leverage: {e}")
            raise

    @retry_on_failure()
    def change_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """Configures the margin allocation logic ('ISOLATED' or 'CROSSED').

        Args:
            symbol: Target symbol.
            margin_type: Margin format ('ISOLATED' or 'CROSSED').

        Returns:
            Margin configuration receipt.
        """
        symbol = symbol.upper()
        margin_type = margin_type.upper()
        logger.info(f"Requesting margin type change for {symbol} to: {margin_type}")

        if self.dry_run:
            pos = self.get_position(symbol)
            pos["marginType"] = margin_type.lower()
            return {"code": 200, "msg": "success"}

        try:
            return self.client.futures_change_margin_type(symbol=symbol, marginType=margin_type)
        except Exception as e:
            # Binance raises code -4046 if margin type is already the target configuration. We catch it.
            if isinstance(e, BinanceAPIException) and e.code == -4046:
                logger.debug(f"Margin type is already configured as {margin_type}. Skipping adjustment.")
                return {"code": 200, "msg": "success (already set)"}
            if not isinstance(e, TradingBotError):
                raise NetworkError(f"Failed to change margin type: {e}")
            raise
