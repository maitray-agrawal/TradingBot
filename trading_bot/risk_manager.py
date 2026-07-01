"""Risk management and capital preservation controls for PrimeTrade AI.

Monitors wallet exposure, leverage levels, and peak drawdowns to prevent
excessive capital losses and maintain trading compliance.
"""

import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from config.paths import EXPORTS_DATA_DIR
from trading_bot.client.client import BinanceTestnetClient
from trading_bot.orders.orders import FuturesOrder
from utils.exceptions import ValidationError as BotValidationError

logger = logging.getLogger("bot")


class RiskConfig(BaseModel):
    """Pydantic model defining risk exposure limits."""

    max_position_size_ratio: float = Field(
        default=0.10, ge=0.01, le=1.0, description="Max exposure value per symbol (ratio of wallet balance)."
    )
    max_aggregate_leverage: int = Field(default=20, ge=1, le=125, description="Maximum permitted leverage multiplier.")
    max_capital_at_risk: float = Field(
        default=0.50, ge=0.05, le=1.0, description="Maximum total margin allocation (ratio of wallet balance)."
    )
    max_drawdown_limit: float = Field(
        default=0.15, ge=0.01, le=0.99, description="Maximum drawdown from peak balance allowed before stopping."
    )


class RiskManager:
    """Risk check executor for futures trading."""

    def __init__(self, config: RiskConfig | None = None) -> None:
        """Initializes RiskManager with configurations.

        Args:
            config: RiskConfig settings model.
        """
        self.config = config or RiskConfig()
        self.history_path = EXPORTS_DATA_DIR / "order_history.json"

    def check_order_risk(self, client: BinanceTestnetClient, order: FuturesOrder, leverage: int) -> None:
        """Runs compliance risk evaluations before placing the order.

        Args:
            client: Instantiated BinanceTestnetClient.
            order: Proposed FuturesOrder.
            leverage: Active leverage factor.
        """
        logger.info(f"Evaluating risk controls for order on '{order.symbol}'")

        # 1. Leverage capping check
        if leverage > self.config.max_aggregate_leverage:
            raise BotValidationError(
                f"Requested leverage of {leverage}x exceeds the Risk Engine maximum "
                f"allowable limit of {self.config.max_aggregate_leverage}x."
            )

        # Retrieve wallet parameters
        wallet_balance = client.get_balance("USDT")
        if wallet_balance <= 0.0:
            raise BotValidationError("Current wallet balance is zero or negative. Order blocked.")

        # 2. Drawdown from peak balance check
        peak_balance = self._get_historical_peak(wallet_balance)
        if peak_balance > wallet_balance:
            drawdown = (peak_balance - wallet_balance) / peak_balance
            if drawdown > self.config.max_drawdown_limit:
                raise BotValidationError(
                    f"Account drawdown ({drawdown * 100:.2f}%) exceeds the risk limit of "
                    f"{self.config.max_drawdown_limit * 100:.2f}%. Trading is locked to preserve capital."
                )

        # Estimate order value (notional size)
        price = order.price
        if price is None:
            pos = client.get_position(order.symbol)
            price = float(pos.get("markPrice", 0.0))
            if price == 0.0:
                price = 1.0  # Fallback

        order_notional = order.quantity * price
        order_margin = order_notional / leverage

        # 3. Position Size limit check: order value cannot exceed max ratio of balance
        max_notional_allowed = wallet_balance * self.config.max_position_size_ratio
        if order_notional > max_notional_allowed:
            raise BotValidationError(
                f"Order notional value of {order_notional:.2f} USDT exceeds the maximum "
                f"single position ratio limit of {self.config.max_position_size_ratio * 100:.1f}% "
                f"({max_notional_allowed:.2f} USDT allowed) of your wallet balance."
            )

        # 4. Total Capital at Risk check
        # Sum margins of existing positions (for simulation, query mock positions or count existing)
        # Note: In dry run mode, we sum mock positions. In live mode, we scan active positions.
        active_margin_sum = 0.0
        if client.dry_run:
            for s, pos in client.mock_positions.items():
                pos_amt = abs(float(pos.get("positionAmt", "0.0")))
                if pos_amt > 0:
                    pos_price = float(pos.get("markPrice", "0.0"))
                    pos_leverage = int(pos.get("leverage", "10"))
                    active_margin_sum += (pos_amt * pos_price) / pos_leverage
        else:
            # query live position information from account details
            try:
                acct = client.client.futures_account()
                # Initial margin of open positions
                active_margin_sum = float(acct.get("totalInitialMargin", 0.0))
            except Exception as e:
                logger.warning(f"Unable to read live initial margin; falling back to 0.0. Error: {e}")
                active_margin_sum = 0.0

        projected_margin_sum = active_margin_sum + order_margin
        max_risk_allowed = wallet_balance * self.config.max_capital_at_risk
        if projected_margin_sum > max_risk_allowed:
            raise BotValidationError(
                f"Projected total margin allocation of {projected_margin_sum:.2f} USDT "
                f"exceeds the maximum capital at risk threshold of {self.config.max_capital_at_risk * 100:.1f}% "
                f"({max_risk_allowed:.2f} USDT allowed) of your wallet balance."
            )

        logger.info(f"Risk checks passed. Order is compliant.")

    def _get_historical_peak(self, current_balance: float) -> float:
        """Scans the local order history database to identify the highest wallet balance.

        Args:
            current_balance: Current USDT wallet balance.

        Returns:
            Peak balance as float.
        """
        peak = current_balance
        if not self.history_path.exists():
            return peak

        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                history = json.load(f)

            # Expecting a list of records
            if isinstance(history, list):
                for record in history:
                    # Look for recorded wallet balance
                    bal = record.get("wallet_balance")
                    if bal is not None:
                        peak = max(peak, float(bal))
        except Exception as e:
            logger.warning(f"Failed to scan order history for peak balance: {e}")

        return peak
