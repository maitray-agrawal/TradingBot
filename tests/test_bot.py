"""Unit tests for the Binance Futures Testnet Trading Bot (Phase 10)."""

import json
import math
from pathlib import Path
import pytest
from binance.exceptions import BinanceAPIException

from config.enums import OrderType, TradingSide
from trading_bot.client.client import BinanceTestnetClient, retry_on_failure
from trading_bot.orders.orders import FuturesOrder
from trading_bot.order_manager import OrderManager
from trading_bot.risk_manager import RiskConfig, RiskManager
from trading_bot.validators.validators import OrderValidator
from utils.exceptions import APIError, NetworkError, ValidationError as BotValidationError


# ==============================================================================
# 1. Schema Validation Tests
# ==============================================================================

def test_futures_order_market_validation() -> None:
    """Verifies that MARKET orders don't require price inputs."""
    order = FuturesOrder(
        symbol="BTCUSDT",
        side=TradingSide.BUY,
        type=OrderType.MARKET,
        quantity=0.05,
    )
    assert order.symbol == "BTCUSDT"
    assert order.side == TradingSide.BUY
    assert order.type == OrderType.MARKET
    assert order.quantity == 0.05
    assert order.price is None
    assert order.stop_price is None


def test_futures_order_limit_validation() -> None:
    """Verifies that LIMIT orders require a price."""
    # Valid LIMIT order
    order = FuturesOrder(
        symbol="ETHUSDT",
        side=TradingSide.SELL,
        type=OrderType.LIMIT,
        quantity=1.2,
        price=3200.0,
    )
    assert order.price == 3200.0

    # Missing price LIMIT order
    with pytest.raises(ValueError, match="LIMIT orders require 'price'"):
        FuturesOrder(
            symbol="ETHUSDT",
            side=TradingSide.SELL,
            type=OrderType.LIMIT,
            quantity=1.2,
        )


def test_futures_order_stop_limit_validation() -> None:
    """Verifies that STOP_LIMIT orders require price and stop_price."""
    # Valid STOP_LIMIT order
    order = FuturesOrder(
        symbol="BTCUSDT",
        side=TradingSide.BUY,
        type=OrderType.STOP_LIMIT,
        quantity=0.1,
        price=60000.0,
        stop_price=59800.0,
    )
    assert order.price == 60000.0
    assert order.stop_price == 59800.0

    # Missing stop_price
    with pytest.raises(ValueError, match="STOP_LIMIT orders require 'stop_price'"):
        FuturesOrder(
            symbol="BTCUSDT",
            side=TradingSide.BUY,
            type=OrderType.STOP_LIMIT,
            quantity=0.1,
            price=60000.0,
        )


def test_futures_order_invalid_inputs() -> None:
    """Verifies invalid parameters raise Pydantic errors."""
    # Negative quantity
    with pytest.raises(ValueError):
        FuturesOrder(
            symbol="BTCUSDT",
            side=TradingSide.BUY,
            type=OrderType.MARKET,
            quantity=-0.05,
        )

    # Empty symbol
    with pytest.raises(ValueError):
        FuturesOrder(
            symbol="",
            side=TradingSide.BUY,
            type=OrderType.MARKET,
            quantity=0.05,
        )


# ==============================================================================
# 2. OrderValidator Tests
# ==============================================================================

def test_validator_leverage_bounds() -> None:
    """Verifies leverage boundaries limits."""
    validator = OrderValidator()
    # Good values
    validator.validate_leverage("BTCUSDT", 1)
    validator.validate_leverage("BTCUSDT", 20)
    validator.validate_leverage("BTCUSDT", 125)

    # Bad values
    with pytest.raises(BotValidationError, match="Must be an integer between 1 and 125"):
        validator.validate_leverage("BTCUSDT", 0)

    with pytest.raises(BotValidationError, match="Must be an integer between 1 and 125"):
        validator.validate_leverage("BTCUSDT", 126)


def test_validator_rounding_and_filters() -> None:
    """Verifies precision rounding and lot/notional boundary validations."""
    validator = OrderValidator()
    client = BinanceTestnetClient(dry_run=True)

    # Validate normal BTCUSDT parameters (precision 3 for quantity, 2 for price)
    # BTCUSDT minQty is 0.001, tickSize is 0.10, min_notional is 5.0
    res = validator.validate_notional_and_lot_size(
        client=client,
        symbol="BTCUSDT",
        quantity=0.12345,  # Should round to 0.123
        price=60500.567,   # Should round to 60500.50 or 60500.60 depending on tickSize 0.10
    )
    assert res["quantity"] == 0.123
    assert res["price"] == 60500.60

    # Validate lot size under minQty
    with pytest.raises(BotValidationError, match="violates LOT_SIZE minimum"):
        validator.validate_notional_and_lot_size(
            client=client,
            symbol="BTCUSDT",
            quantity=0.0005,
            price=60000.0,
        )

    # Validate lot size over maxQty
    with pytest.raises(BotValidationError, match="violates LOT_SIZE maximum"):
        validator.validate_notional_and_lot_size(
            client=client,
            symbol="BTCUSDT",
            quantity=5000.0,
            price=60000.0,
        )

    # Validate minimum notional limit check
    with pytest.raises(BotValidationError, match="below the MIN_NOTIONAL limit"):
        # 0.001 BTC * 1000 USDT = 1 USDT (notional < 5.0)
        validator.validate_notional_and_lot_size(
            client=client,
            symbol="BTCUSDT",
            quantity=0.001,
            price=1000.0,
        )


def test_validator_margin_requirements() -> None:
    """Verifies margin validations block orders if wallet balance is low."""
    validator = OrderValidator()
    client = BinanceTestnetClient(dry_run=True)

    # Set mock balance to 100 USDT
    client.mock_balance = 100.0

    # 1. Compliant Order: Buy 0.01 BTC at 60,000 USDT with 10x leverage
    # Notional = 600 USDT. Initial Margin = 600 / 10 = 60 USDT.
    # Wallet balance 100 >= 60. Should pass.
    order_ok = FuturesOrder(
        symbol="BTCUSDT",
        side=TradingSide.BUY,
        type=OrderType.LIMIT,
        quantity=0.01,
        price=60000.0,
    )
    validator.validate_margin_requirements(client, order_ok, leverage=10)

    # 2. Blocked Order: Initial Margin = 600 / 5 = 120 USDT.
    # Wallet balance 100 < 120. Should raise ValidationError.
    with pytest.raises(BotValidationError, match="Insufficient funds"):
        validator.validate_margin_requirements(client, order_ok, leverage=5)


# ==============================================================================
# 3. RiskManager Tests
# ==============================================================================

def test_risk_manager_leverage_limit() -> None:
    """Verifies RiskManager blocks leverage configurations above limits."""
    client = BinanceTestnetClient(dry_run=True)
    config = RiskConfig(max_aggregate_leverage=20)
    risk_m = RiskManager(config=config)

    # Use a small quantity (0.01 BTC instead of 0.05 BTC) to avoid violating the 10% position size ratio
    order = FuturesOrder(
        symbol="BTCUSDT", side=TradingSide.BUY, type=OrderType.MARKET, quantity=0.01
    )

    # Under limit
    risk_m.check_order_risk(client, order, leverage=10)

    # Over limit
    with pytest.raises(BotValidationError, match="exceeds the Risk Engine maximum"):
        risk_m.check_order_risk(client, order, leverage=25)


def test_risk_manager_position_size_limit() -> None:
    """Verifies RiskManager blocks orders exceeding max position size ratio (10% of wallet)."""
    client = BinanceTestnetClient(dry_run=True)
    client.mock_balance = 1000.0  # 10% is 100 USDT value

    # Max ratio is 10%. Max position value allowed is 100 USDT.
    config = RiskConfig(max_position_size_ratio=0.10)
    risk_m = RiskManager(config=config)
    risk_m._get_historical_peak = lambda balance: balance

    # 1. Long 0.001 BTC at 60,000 USDT = 60 USDT value (ok)
    order_ok = FuturesOrder(
        symbol="BTCUSDT", side=TradingSide.BUY, type=OrderType.LIMIT, quantity=0.001, price=60000.0
    )
    risk_m.check_order_risk(client, order_ok, leverage=10)

    # 2. Long 0.003 BTC at 60,000 USDT = 180 USDT value (violates 10% ratio)
    order_bad = FuturesOrder(
        symbol="BTCUSDT", side=TradingSide.BUY, type=OrderType.LIMIT, quantity=0.003, price=60000.0
    )
    with pytest.raises(BotValidationError, match="exceeds the maximum single position ratio"):
        risk_m.check_order_risk(client, order_bad, leverage=10)


def test_risk_manager_drawdown_limit() -> None:
    """Verifies RiskManager blocks trading if peak drawdown is exceeded."""
    client = BinanceTestnetClient(dry_run=True)
    client.mock_balance = 800.0  # Peak is simulated at 1000 in local files or mock checks

    config = RiskConfig(max_drawdown_limit=0.15)  # Max drawdown is 15%
    risk_m = RiskManager(config=config)

    # Force peak balance check to be 1000 USDT
    # 800 balance vs 1000 peak represents a 20% drawdown. Since 20% > 15%, new orders are blocked.
    def mock_peak(balance):
        return 1000.0

    risk_m._get_historical_peak = mock_peak

    order = FuturesOrder(
        symbol="BTCUSDT", side=TradingSide.BUY, type=OrderType.LIMIT, quantity=0.001, price=60000.0
    )
    with pytest.raises(BotValidationError, match="Account drawdown.*exceeds the risk limit"):
        risk_m.check_order_risk(client, order, leverage=10)


# ==============================================================================
# 4. Client Retry Logic Tests
# ==============================================================================

class DummyClient:
    """Helper to test retry_on_failure decorator."""

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.calls = 0

    @retry_on_failure(max_retries=3, base_delay=0.01, max_delay=0.05)
    def call_api(self, exception_to_raise=None):
        self.calls += 1
        if exception_to_raise:
            raise exception_to_raise
        return "success"


def test_retry_decorator_success() -> None:
    """Verifies retry decorator returns value immediately if no errors are raised."""
    dummy = DummyClient()
    res = dummy.call_api()
    assert res == "success"
    assert dummy.calls == 1


def test_retry_decorator_rate_limit() -> None:
    """Verifies retry decorator retries on 429 and eventually raises if unsuccessful."""
    # Raise a retryable error (HTTP 429 Rate Limit) using JSON string format for 'text' parameter
    ex = BinanceAPIException(None, 429, '{"code": -1003, "msg": "Too many requests"}')
    dummy = DummyClient()
    with pytest.raises(APIError, match="Too many requests"):
        dummy.call_api(exception_to_raise=ex)

    # Should have retried 3 times
    assert dummy.calls == 3


def test_retry_decorator_immediate_fail() -> None:
    """Verifies decorator fails immediately on client parameters error (HTTP 400)."""
    # Raise a non-retryable error (HTTP 400 Bad Request) using JSON string format for 'text' parameter
    ex = BinanceAPIException(None, 400, '{"code": -1111, "msg": "Invalid quantity"}')
    dummy = DummyClient()
    with pytest.raises(APIError, match="Invalid quantity"):
        dummy.call_api(exception_to_raise=ex)

    # Should fail on first attempt without retrying
    assert dummy.calls == 1


# ==============================================================================
# 5. Dry Run Integration Tests
# ==============================================================================

def test_dry_run_placement_updates_positions(tmp_path: Path) -> None:
    """Verifies dry run mode places orders, updates positions, and writes log history files."""
    client = BinanceTestnetClient(dry_run=True)
    client.mock_balance = 5000.0

    # Inject temporary output folders to prevent test pollution
    # Temporarily redirect files
    json_path = tmp_path / "order_history.json"
    csv_path = tmp_path / "order_history.csv"

    # Setup managers
    validator = OrderValidator()
    risk_m = RiskManager()
    # Redirect paths
    risk_m.history_path = json_path
    
    manager = OrderManager(client, validator, risk_m)
    manager.json_history = json_path
    manager.csv_history = csv_path

    # Place MARKET order: Buy 0.005 BTC (notional is 300.0 USDT, below 10% of 5000 balance limit)
    receipt = manager.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.005,
        leverage=10,
    )

    assert receipt["status"] == "FILLED"
    assert receipt["symbol"] == "BTCUSDT"
    assert receipt["origQty"] == "0.005"

    # Verify positions dictionary updated in client
    pos = client.get_position("BTCUSDT")
    assert pos["symbol"] == "BTCUSDT"
    assert float(pos["positionAmt"]) == 0.005

    # Verify order history file is written
    assert json_path.exists()
    assert csv_path.exists()

    # Load and check history content
    with open(json_path, "r", encoding="utf-8") as f:
        history = json.load(f)
    
    assert len(history) == 1
    assert history[0]["symbol"] == "BTCUSDT"
    assert history[0]["side"] == "BUY"
    assert history[0]["quantity"] == 0.005
    assert history[0]["mode"] == "DRY_RUN"
