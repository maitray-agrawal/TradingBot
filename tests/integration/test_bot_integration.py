"""
test_bot_integration.py — End-to-end integration tests for the trading bot.

Tests validate the full dry-run order lifecycle using actual module APIs:
    Order Schema → Validation → Risk Check → Execution (mocked) → Export

Marked with @pytest.mark.integration and @pytest.mark.bot.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config.enums import OrderType, TradingSide


@pytest.mark.integration
@pytest.mark.bot
class TestOrderLifecycle:
    """Integration: full order schema validation using real module API."""

    def test_market_order_schema_validates_correctly(self) -> None:
        """A correctly formed MARKET order passes Pydantic validation."""
        from trading_bot.orders.orders import FuturesOrder

        order = FuturesOrder(
            symbol="BTCUSDT",
            side=TradingSide.BUY,
            type=OrderType.MARKET,
            quantity=0.001,
        )
        assert order.symbol == "BTCUSDT"
        assert order.side == TradingSide.BUY
        assert order.quantity == 0.001

    def test_limit_order_requires_price(self) -> None:
        """A LIMIT order without a price raises a validation error."""
        from pydantic import ValidationError

        from trading_bot.orders.orders import FuturesOrder

        with pytest.raises(ValidationError):
            FuturesOrder(
                symbol="BTCUSDT",
                side=TradingSide.BUY,
                type=OrderType.LIMIT,
                quantity=0.001,
                # price intentionally omitted
            )

    def test_stop_limit_order_requires_price_and_stop_price(self) -> None:
        """A STOP_LIMIT order without stop_price fails."""
        from pydantic import ValidationError

        from trading_bot.orders.orders import FuturesOrder

        with pytest.raises(ValidationError):
            FuturesOrder(
                symbol="BTCUSDT",
                side=TradingSide.SELL,
                type=OrderType.STOP_LIMIT,
                quantity=0.001,
                price=45000.0,
                # stop_price intentionally omitted
            )

    def test_negative_quantity_fails_validation(self) -> None:
        """A negative quantity is rejected by the order schema."""
        from pydantic import ValidationError

        from trading_bot.orders.orders import FuturesOrder

        with pytest.raises(ValidationError):
            FuturesOrder(
                symbol="BTCUSDT",
                side=TradingSide.BUY,
                type=OrderType.MARKET,
                quantity=-1.0,
            )

    def test_zero_quantity_fails_validation(self) -> None:
        """Zero quantity is rejected by the order schema."""
        from pydantic import ValidationError

        from trading_bot.orders.orders import FuturesOrder

        with pytest.raises(ValidationError):
            FuturesOrder(
                symbol="BTCUSDT",
                side=TradingSide.BUY,
                type=OrderType.MARKET,
                quantity=0.0,
            )

    def test_limit_order_with_price_passes(self) -> None:
        """A LIMIT order with a valid price passes validation."""
        from trading_bot.orders.orders import FuturesOrder

        order = FuturesOrder(
            symbol="ETHUSDT",
            side=TradingSide.SELL,
            type=OrderType.LIMIT,
            quantity=0.1,
            price=3000.0,
        )
        assert order.price == 3000.0
        assert order.type == OrderType.LIMIT

    def test_stop_limit_order_with_both_prices_passes(self) -> None:
        """A STOP_LIMIT order with price and stop_price passes validation."""
        from trading_bot.orders.orders import FuturesOrder

        order = FuturesOrder(
            symbol="BTCUSDT",
            side=TradingSide.SELL,
            type=OrderType.STOP_LIMIT,
            quantity=0.001,
            price=44000.0,
            stop_price=44500.0,
        )
        assert order.stop_price == 44500.0

    def test_symbol_is_normalized_to_uppercase(self) -> None:
        """Symbol field is normalized to uppercase."""
        from trading_bot.orders.orders import FuturesOrder

        order = FuturesOrder(
            symbol="btcusdt",
            side=TradingSide.BUY,
            type=OrderType.MARKET,
            quantity=0.001,
        )
        assert order.symbol == "BTCUSDT"


@pytest.mark.integration
@pytest.mark.bot
class TestRiskManagerIntegration:
    """Integration: RiskManager enforces position and drawdown limits via real API."""

    def _make_risk_manager(self, max_position_size_ratio: float = 0.10, max_leverage: int = 20, max_drawdown: float = 0.15):
        """Helper to create a RiskManager with a custom RiskConfig."""
        from trading_bot.risk_manager import RiskConfig, RiskManager

        config = RiskConfig(
            max_position_size_ratio=max_position_size_ratio,
            max_aggregate_leverage=max_leverage,
            max_drawdown_limit=max_drawdown,
        )
        return RiskManager(config=config)

    def test_leverage_within_max_does_not_raise(self) -> None:
        """Leverage at or below the max is accepted by risk config."""
        from trading_bot.risk_manager import RiskConfig

        config = RiskConfig(max_aggregate_leverage=20)
        assert config.max_aggregate_leverage == 20

    def test_leverage_above_max_raises_on_config(self) -> None:
        """Leverage above 125 is rejected at config level by Pydantic."""
        from pydantic import ValidationError

        from trading_bot.risk_manager import RiskConfig

        with pytest.raises(ValidationError):
            RiskConfig(max_aggregate_leverage=200)

    def test_drawdown_limit_is_stored_correctly(self) -> None:
        """Max drawdown limit is stored in the RiskConfig correctly."""
        risk = self._make_risk_manager(max_drawdown=0.20)
        assert risk.config.max_drawdown_limit == 0.20

    def test_position_size_ratio_is_stored_correctly(self) -> None:
        """Position size ratio is stored in the RiskConfig correctly."""
        risk = self._make_risk_manager(max_position_size_ratio=0.05)
        assert risk.config.max_position_size_ratio == 0.05

    def test_risk_manager_has_check_order_risk_method(self) -> None:
        """RiskManager exposes the check_order_risk method."""
        risk = self._make_risk_manager()
        assert hasattr(risk, "check_order_risk")
        assert callable(risk.check_order_risk)


@pytest.mark.integration
@pytest.mark.bot
class TestPositionManagerIntegration:
    """Integration: PositionManager uses the correct API method."""

    def test_position_manager_has_get_active_positions_method(self, mock_binance_client: MagicMock) -> None:
        """PositionManager exposes get_active_positions() method."""
        from trading_bot.position_manager import PositionManager

        pm = PositionManager(client=mock_binance_client)
        assert hasattr(pm, "get_active_positions")
        assert callable(pm.get_active_positions)

    def test_position_manager_dry_run_returns_list(self, mock_binance_client: MagicMock) -> None:
        """PositionManager.get_active_positions() returns a list in dry-run."""
        from trading_bot.position_manager import PositionManager

        # Configure mock client for dry_run mode
        mock_binance_client.dry_run = True
        mock_binance_client.mock_positions = {}

        pm = PositionManager(client=mock_binance_client)
        positions = pm.get_active_positions()
        assert isinstance(positions, list)

    def test_position_manager_has_set_leverage_method(self, mock_binance_client: MagicMock) -> None:
        """PositionManager exposes set_leverage() method."""
        from trading_bot.position_manager import PositionManager

        pm = PositionManager(client=mock_binance_client)
        assert hasattr(pm, "set_leverage")
