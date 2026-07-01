"""Typer command-line interface for the Binance Futures Testnet Trading Bot.

Exposes CLI commands to check balances, place manual market, limit, or stop-limit
orders, cancel pending trades, and view order execution histories.
"""

import json
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.paths import EXPORTS_DATA_DIR
from trading_bot.client.client import BinanceTestnetClient
from trading_bot.order_manager import OrderManager
from trading_bot.position_manager import PositionManager
from utils.exceptions import ProjectError

# CLI instantiation
bot_cli = typer.Typer(name="bot", help="Binance Futures Testnet Trading Bot controls.")
console = Console()
logger = logging.getLogger("bot")


@bot_cli.command()
def balance(
    live: bool = typer.Option(False, "--live", "-l", help="Run against the live Binance Testnet (requires API keys)."),
) -> None:
    """Queries account balance, available margin, and list of active positions."""
    try:
        # Initialize client and manager
        client = BinanceTestnetClient(dry_run=not live)
        pos_manager = PositionManager(client)

        wallet_balance = client.get_balance("USDT")
        positions = pos_manager.get_active_positions()

        # Display Wallet Header
        mode_str = "[bold magenta]LIVE TESTNET[/bold magenta]" if live else "[bold cyan]DRY RUN (SIMULATION)[/bold cyan]"
        console.print(f"\nAccount Wallet Status - {mode_str}")
        console.print(f"Total Available Balance: [bold green]{wallet_balance:.2f} USDT[/bold green]\n")

        # Display Positions Table
        pos_table = Table(title="Active Open Positions", show_header=True, header_style="bold magenta")
        pos_table.add_column("Symbol", style="yellow")
        pos_table.add_column("Direction", style="bold")
        pos_table.add_column("Size", style="white")
        pos_table.add_column("Entry Price", style="white")
        pos_table.add_column("Mark Price", style="white")
        pos_table.add_column("Unrealized PnL", style="white")
        pos_table.add_column("Leverage", style="dim")
        pos_table.add_column("Margin Type", style="dim")

        if not positions:
            console.print("No active open positions detected.\n")
            return

        for pos in positions:
            pnl = pos["unrealized_pnl"]
            pnl_str = f"[bold green]+{pnl:.2f} USDT[/bold green]" if pnl >= 0 else f"[bold red]{pnl:.2f} USDT[/bold red]"
            dir_str = (
                f"[bold green]{pos['direction']}[/bold green]"
                if pos["direction"] == "LONG"
                else f"[bold red]{pos['direction']}[/bold red]"
            )

            pos_table.add_row(
                pos["symbol"],
                dir_str,
                f"{pos['size']:.4f}",
                f"{pos['entry_price']:.2f}",
                f"{pos['mark_price']:.2f}",
                pnl_str,
                f"{pos['leverage']}x",
                pos["margin_type"],
            )

        console.print(pos_table)
        console.print("")

    except ProjectError as e:
        console.print(f"[bold red]Configuration or Network Error:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {e}")


@bot_cli.command()
def order(
    symbol: str = typer.Argument(..., help="Ticker symbol to execute (e.g. BTCUSDT)."),
    side: str = typer.Argument(..., help="Order execution direction: BUY or SELL."),
    order_type: str = typer.Argument(..., help="Order format: MARKET, LIMIT, or STOP_LIMIT."),
    qty: float = typer.Argument(..., help="Order size (contracts / coins count)."),
    price: float = typer.Option(None, "--price", "-p", help="Limit price (required for LIMIT & STOP_LIMIT)."),
    stop_price: float = typer.Option(None, "--stop-price", "-s", help="Trigger stop price (required for STOP_LIMIT)."),
    leverage: int = typer.Option(10, "--leverage", "-v", help="Active leverage factor (1 to 125)."),
    margin: str = typer.Option("CROSS", "--margin", "-m", help="Margin allocation type: CROSS or ISOLATED."),
    live: bool = typer.Option(False, "--live", "-l", help="Run against the live Binance Testnet (requires API keys)."),
) -> None:
    """Submits a futures order for execution after validating risk and parameters."""
    try:
        # Standardize Inputs
        side = side.upper()
        order_type = order_type.upper()
        margin = margin.upper()

        if side not in ("BUY", "SELL"):
            console.print("[bold red]Error:[/bold red] Side must be either 'BUY' or 'SELL'.")
            raise typer.Exit(code=1)

        if order_type not in ("MARKET", "LIMIT", "STOP_LIMIT"):
            console.print("[bold red]Error:[/bold red] Type must be one of 'MARKET', 'LIMIT', or 'STOP_LIMIT'.")
            raise typer.Exit(code=1)

        if margin not in ("CROSS", "ISOLATED"):
            console.print("[bold red]Error:[/bold red] Margin must be either 'CROSS' or 'ISOLATED'.")
            raise typer.Exit(code=1)

        # Initialize Bot Components
        client = BinanceTestnetClient(dry_run=not live)
        manager = OrderManager(client)

        console.print("[yellow]Verifying parameters and risk controls...[/yellow]")
        receipt = manager.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            price=price,
            stop_price=stop_price,
            leverage=leverage,
            margin_type=margin,
        )

        logger.info(f"Order processed successfully: {receipt.get('orderId')}")

    except ProjectError as e:
        console.print(f"[bold red]Order Validation or Execution Failed:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Unexpected Failure:[/bold red] {e}")


@bot_cli.command()
def cancel(
    symbol: str = typer.Argument(..., help="Trading symbol ticker (e.g. BTCUSDT)."),
    order_id: int = typer.Argument(..., help="Exchange Order ID to cancel."),
    live: bool = typer.Option(False, "--live", "-l", help="Run against the live Binance Testnet (requires API keys)."),
) -> None:
    """Cancels a pending limit or stop-limit order."""
    try:
        client = BinanceTestnetClient(dry_run=not live)
        console.print(f"[yellow]Attempting cancellation of order {order_id} on {symbol}...[/yellow]")
        receipt = client.cancel_order(symbol, order_id)

        console.print(
            Panel(
                f"Successfully cancelled order [bold yellow]{order_id}[/bold yellow] on [bold cyan]{symbol}[/bold cyan].\n"
                f"Current Status: [bold red]{receipt.get('status', 'CANCELED')}[/bold red]",
                title="Cancellation Receipt",
                border_style="green",
            )
        )
    except ProjectError as e:
        console.print(f"[bold red]Cancellation Failed:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Unexpected Failure:[/bold red] {e}")


@bot_cli.command()
def history(
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum historical logs count to display."),
) -> None:
    """Prints the archived order execution history list from the local database."""
    history_path = EXPORTS_DATA_DIR / "order_history.json"

    if not history_path.exists():
        console.print("No order execution history found locally.\n")
        return

    try:
        with open(history_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        if not records or not isinstance(records, list):
            console.print("Order execution history database is empty.\n")
            return

        # Sort and limit entries
        records = sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

        # Display history table
        hist_table = Table(
            title=f"Order Execution History (Last {len(records)} entries)",
            show_header=True,
            header_style="bold cyan",
        )
        hist_table.add_column("Timestamp", style="dim")
        hist_table.add_column("Order ID", style="white")
        hist_table.add_column("Symbol", style="yellow")
        hist_table.add_column("Side", style="bold")
        hist_table.add_column("Type", style="white")
        hist_table.add_column("Quantity", style="white")
        hist_table.add_column("Price", style="white")
        hist_table.add_column("Leverage", style="dim")
        hist_table.add_column("Wallet Balance", style="green")
        hist_table.add_column("Status", style="bold")
        hist_table.add_column("Mode", style="white")

        for rec in records:
            side = rec.get("side", "")
            side_color = "green" if side == "BUY" else "red"
            side_str = f"[{side_color}]{side}[/{side_color}]"

            ts = rec.get("timestamp", "")
            if ts:
                # Truncate decimals for readability
                ts = ts.split(".")[0].replace("T", " ")

            mode = rec.get("mode", "")
            mode_color = "cyan" if mode == "DRY_RUN" else "magenta"
            mode_str = f"[{mode_color}]{mode}[/{mode_color}]"

            hist_table.add_row(
                ts,
                str(rec.get("order_id", "")),
                rec.get("symbol", ""),
                side_str,
                rec.get("type", ""),
                f"{rec.get('quantity', 0.0):.4f}",
                f"{rec.get('price', 0.0):.2f}" if rec.get("price", 0.0) > 0 else "MARKET",
                f"{rec.get('leverage', 10)}x",
                f"{rec.get('wallet_balance', 0.0):.2f}",
                rec.get("status", ""),
                mode_str,
            )

        console.print(hist_table)
        console.print("")

    except Exception as e:
        console.print(f"[bold red]Failed to read history logs:[/bold red] {e}")


if __name__ == "__main__":
    bot_cli()
