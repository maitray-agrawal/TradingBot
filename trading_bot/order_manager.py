"""Order routing, orchestration, and logging engine for PrimeTrade AI.

Integrates pre-trade validator and risk compliance modules, submits requests
to the Binance client, updates local execution logs, and prints visual receipts.
"""

import csv
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.paths import EXPORTS_DATA_DIR, ensure_directories_exist
from trading_bot.client.client import BinanceTestnetClient
from trading_bot.orders.orders import FuturesOrder
from trading_bot.risk_manager import RiskManager
from trading_bot.validators.validators import OrderValidator

logger = logging.getLogger("bot")
console = Console()


class OrderManager:
    """Orchestrates order validations, execution, and local database archiving."""

    def __init__(
        self,
        client: BinanceTestnetClient,
        validator: OrderValidator | None = None,
        risk_manager: RiskManager | None = None,
    ) -> None:
        """Initializes OrderManager.

        Args:
            client: Instantiated BinanceTestnetClient.
            validator: Instantiated OrderValidator.
            risk_manager: Instantiated RiskManager.
        """
        self.client = client
        self.validator = validator or OrderValidator()
        self.risk_manager = risk_manager or RiskManager()

        # Output file paths
        self.json_history = EXPORTS_DATA_DIR / "order_history.json"
        self.csv_history = EXPORTS_DATA_DIR / "order_history.csv"

        # Ensure directory structures are set up
        ensure_directories_exist()

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
        leverage: int = 10,
        margin_type: str = "CROSS",
    ) -> Dict[str, Any]:
        """Validates and executes an order, updates histories, and prints a visual summary.

        Args:
            symbol: Target ticker symbol.
            side: Execution direction ('BUY' or 'SELL').
            order_type: Execution format ('MARKET', 'LIMIT', 'STOP_LIMIT').
            quantity: Sizing units.
            price: Execution limit price (optional).
            stop_price: Stop-limit trigger price (optional).
            leverage: Active leverage factor.
            margin_type: Margin allocation setting ('CROSS' or 'ISOLATED').

        Returns:
            Dictionary containing order execution receipt or failure logs.
        """
        symbol = symbol.upper()
        side = side.upper()
        order_type = order_type.upper()
        margin_type = margin_type.upper()

        logger.info(f"Initiating order routing for {symbol} ({side})")

        # 1. Apply margin type and leverage settings on the exchange
        try:
            self.client.change_margin_type(symbol, margin_type)
            self.client.change_leverage(symbol, leverage)
        except Exception as e:
            logger.warning(f"Failed to apply leverage or margin configurations: {e}")

        # 2. Run price/quantity filter validation and get standardized values
        validated_params = self.validator.validate_notional_and_lot_size(
            client=self.client,
            symbol=symbol,
            quantity=quantity,
            price=price,
        )
        final_qty = validated_params["quantity"]
        final_price = validated_params["price"] if price is not None else None

        # 3. Construct the verified order model
        order = FuturesOrder(
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=final_qty,
            price=final_price,
            stop_price=stop_price,
        )

        # 4. Run pre-trade risk and wallet validations
        self.validator.validate_leverage(symbol, leverage)
        self.risk_manager.check_order_risk(self.client, order, leverage)
        self.validator.validate_margin_requirements(self.client, order, leverage)

        # 5. Place the order
        receipt = self.client.create_order(
            symbol=order.symbol,
            side=order.side.value,
            order_type=order.type.value,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
            time_in_force=order.time_in_force,
        )

        # 6. Retrieve post-order wallet balance to archive current state
        wallet_balance = self.client.get_balance("USDT")

        # 7. Generate historical record entry
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "order_id": receipt.get("orderId"),
            "symbol": order.symbol,
            "side": order.side.value,
            "type": order.type.value,
            "quantity": order.quantity,
            "price": order.price or 0.0,
            "stop_price": order.stop_price or 0.0,
            "leverage": leverage,
            "wallet_balance": wallet_balance,
            "status": receipt.get("status", "NEW"),
            "mode": "DRY_RUN" if self.client.dry_run else "LIVE",
        }

        # 8. Save records to JSON and CSV history archives
        self._archive_order_json(record)
        self._archive_order_csv(record)

        # 9. Output beautiful console summaries
        self._print_order_card(record)

        return receipt

    def _archive_order_json(self, record: Dict[str, Any]) -> None:
        """Appends the execution record to the local JSON database file.

        Args:
            record: Structured execution record.
        """
        history_list = []
        if self.json_history.exists():
            try:
                with open(self.json_history, "r", encoding="utf-8") as f:
                    history_list = json.load(f)
                if not isinstance(history_list, list):
                    history_list = []
            except Exception as e:
                logger.error(f"Failed to read JSON history: {e}. Starting fresh.")
                history_list = []

        history_list.append(record)

        try:
            with open(self.json_history, "w", encoding="utf-8") as f:
                json.dump(history_list, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to write to JSON history database: {e}")

    def _archive_order_csv(self, record: Dict[str, Any]) -> None:
        """Appends the execution record to the local CSV database file.

        Args:
            record: Structured execution record.
        """
        headers = [
            "timestamp",
            "order_id",
            "symbol",
            "side",
            "type",
            "quantity",
            "price",
            "stop_price",
            "leverage",
            "wallet_balance",
            "status",
            "mode",
        ]
        file_exists = self.csv_history.exists()

        try:
            with open(self.csv_history, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(headers)
                writer.writerow([record.get(h) for h in headers])
        except Exception as e:
            logger.error(f"Failed to write to CSV history database: {e}")

    def _print_order_card(self, record: Dict[str, Any]) -> None:
        """Outputs a high-fidelity visual layout card of the order details.

        Args:
            record: Execution record dict.
        """
        side = record["side"]
        side_color = "green" if side == "BUY" else "red"
        mode_color = "cyan" if record["mode"] == "DRY_RUN" else "magenta"

        # Create details table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Property", style="bold white")
        table.add_column("Value")

        table.add_row("Exchange Order ID", str(record["order_id"]))
        table.add_row("Symbol", f"[yellow]{record['symbol']}[/yellow]")
        table.add_row("Execution side", f"[bold {side_color}]{side}[/bold {side_color}]")
        table.add_row("Order type", record["type"])
        table.add_row("Sizing (Units)", f"{record['quantity']:.4f}")
        table.add_row("Limit Price", f"{record['price']:.2f} USDT" if record["price"] > 0 else "MARKET")
        if record["stop_price"] > 0:
            table.add_row("Stop Trigger Price", f"{record['stop_price']:.2f} USDT")
        table.add_row("Multiplier Leverage", f"{record['leverage']}x")
        table.add_row("Wallet balance", f"{record['wallet_balance']:.2f} USDT")
        table.add_row("Verification Status", f"[bold green]{record['status']}[/bold green]")
        table.add_row("Execution Mode", f"[bold {mode_color}]{record['mode']}[/bold {mode_color}]")

        # Compile Panel
        panel = Panel(
            table,
            title=f"[bold {side_color}]Order Execution Receipt[/bold {side_color}]",
            border_style=mode_color,
            expand=False,
        )
        console.print(panel)
