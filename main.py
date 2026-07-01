"""Entry point runner for PrimeTrade AI.

Verifies folder structure, validates configurations, initializes logging,
runs data ingestion engine diagnostics with rich visual outputs, and integrates
the Binance Futures Testnet Trading Bot CLI.
"""

import logging
import os
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from analytics.ingestion import FileScanner, IngestionEngine

# Config & Utils imports
from config import ensure_directories_exist, settings
from config.enums import DatasetType
from trading_bot.cli import bot_cli
from utils import setup_logging

logger = logging.getLogger("system")
console = Console()

# Instantiate the main Typer application
app = typer.Typer(
    name="primetrade-ai",
    help="PrimeTrade AI: Sentiment-Driven Crypto Trading Analytics & Binance Futures Testnet Trading Bot.",
)

# Register the trading bot sub-commands
app.add_typer(bot_cli, name="bot")


def print_banner() -> None:
    """Prints a premium styled ASCII art banner for the project initialization."""
    banner_text = (
        "[bold cyan]######   #####   #  #     #  ######  ######  #####   #####  #####   ######[/bold cyan]\n"
        "[bold cyan]#     #  #    #  #  ##   ##  #         #     #    #  #   #  #    #  #[/bold cyan]\n"
        "[bold blue]######   #####   #  # # # #  #####     #     #####   #####  #    #  ##### [/bold blue]\n"
        "[bold blue]#        #    #  #  #  #  #  #         #     #    #  #   #  #    #  #[/bold blue]\n"
        "[bold purple]#        #    #  #  #     #  ######    #     #    #  #   #  ######  ######[/bold purple]\n"
        "\n"
        "[bold white]    Sentiment-Driven Crypto Trading Analytics & Binance Futures Bot[/bold white]\n"
        "[bold green]                        SYSTEM INITIALIZATION RUN[/bold green]"
    )
    console.print(
        Panel(
            banner_text,
            title="[bold green]Welcome to PrimeTrade AI[/bold green]",
            expand=False,
            border_style="cyan",
        )
    )


def verify_env_file() -> None:
    """Checks if the environment file exists and issues logs accordingly."""
    env_path = Path(".env")
    if env_path.is_file():
        logger.info("Local configuration file '.env' detected successfully.")
    else:
        logger.warning("Configuration file '.env' not found. System running on fallback defaults.")


def create_demo_files_if_empty() -> None:
    """Generates sample datasets in the data folders if no files exist."""
    raw_dir = Path(settings.data_directory) / "raw"
    uploads_dir = Path(settings.data_directory) / "uploads"

    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # 1. Mock Trader History CSV
    trader_path = raw_dir / "binance_futures_trades.csv"
    if not list(raw_dir.glob("*")) and not trader_path.exists():
        logger.info("Generating demo trader history file...")
        trader_df = pd.DataFrame(
            {
                "Account": ["BOT-ACC-1", "BOT-ACC-1", "BOT-ACC-1", "BOT-ACC-1"],
                "Coin": ["BTCUSDT", "ETHUSDT", "BTCUSDT", "SOLUSDT"],
                "Execution Price": [61230.50, 3350.25, 61400.00, 142.10],
                "Side": ["BUY", "BUY", "SELL", "SELL"],
                "Size": [0.05, 0.8, 0.05, 12.5],
                "Closed PnL": [0.0, 0.0, 8.48, -15.20],
                "Timestamp": [
                    1688212800000,
                    1688223600000,
                    1688234400000,
                    1688245200000,
                ],
            }
        )
        trader_df.to_csv(trader_path, index=False)
        logger.info(f"Demo trader history saved to: {trader_path}")

    # 2. Mock Fear & Greed Excel
    fg_path = uploads_dir / "fear_greed_index.xlsx"
    if not list(uploads_dir.glob("*")) and not fg_path.exists():
        logger.info("Generating demo Fear & Greed index file...")
        fg_df = pd.DataFrame(
            {
                "date": ["2026-06-28", "2026-06-29", "2026-06-30", "2026-07-01"],
                "value": [42, 38, 55, 68],
                "sentiment_classification": ["Fear", "Fear", "Neutral", "Greed"],
            }
        )
        fg_df.to_excel(fg_path, index=False)
        logger.info(f"Demo Fear & Greed saved to: {fg_path}")


def display_dataset_diagnostics(dataset) -> None:
    """Renders a gorgeous terminal display of the ingested dataset's profile."""
    # Metadata Table
    meta_table = Table(
        title=f"Metadata Profile - {dataset.metadata.rows} rows x {dataset.metadata.columns} cols",
        show_header=True,
        header_style="bold magenta",
    )
    meta_table.add_column("Property", style="dim", width=25)
    meta_table.add_column("Value", style="white")

    meta = dataset.metadata
    meta_table.add_row("Dataset Type", f"[bold green]{dataset.dataset_type.name}[/bold green]")
    meta_table.add_row("Size on Disk", f"{meta.file_size_bytes} bytes")
    meta_table.add_row("Memory Footprint", f"{meta.memory_usage_bytes / 1024:.2f} KB")
    meta_table.add_row("SHA-256 Checksum", meta.file_checksum[:20] + "...")
    meta_table.add_row("Load Duration", f"{meta.load_time_seconds:.4f} seconds")
    meta_table.add_row("Duplicate Rows", f"{meta.duplicate_count}")

    # Data Quality Report
    qual = dataset.quality_report
    score_color = "green" if qual.quality_score > 85.0 else ("yellow" if qual.quality_score > 60.0 else "red")
    qual_panel = Panel(
        f"[bold {score_color}]Quality Score: {qual.quality_score:.1f}/100.0[/bold {score_color}]\n"
        f"Issues Found: {len(qual.potential_issues)}\n"
        f"Recommendations:\n" + "\n".join(f"  • {r}" for r in qual.recommendations),
        title="[bold yellow]Data Quality Profiler[/bold yellow]",
        border_style=score_color,
    )

    # Column Mapping Table
    map_table = Table(title="Column Normalization Mapping", show_header=True, header_style="bold blue")
    map_table.add_column("Original Header")
    map_table.add_column("Mapped Clean Header")
    for orig, target in dataset.column_mapping.items():
        map_table.add_row(orig, target)

    # Preview Data Table
    preview_df = dataset.dataframe.head(3)
    preview_table = Table(
        title="Ingested Data Preview (First 3 Rows)",
        show_header=True,
        header_style="bold cyan",
    )
    for col in preview_df.columns:
        preview_table.add_column(col)
    for _, row in preview_df.iterrows():
        preview_table.add_row(*(str(val) for val in row))

    console.print(
        Panel(
            f"[bold cyan]Dataset Path:[/bold cyan] {meta.file_checksum}",
            title="Diagnostics Output",
            border_style="cyan",
        )
    )
    console.print(meta_table)
    console.print(map_table)
    console.print(preview_table)
    console.print(qual_panel)
    console.print("\n" + "=" * 80 + "\n")


def run_ingestion_diagnostics() -> None:
    """Discovers, loads, and displays diagnostics for all files in the directories."""
    console.print("\n[bold yellow]Starting Ingestion Engine Diagnostics...[/bold yellow]")

    create_demo_files_if_empty()

    raw_dir = Path(settings.data_directory) / "raw"
    uploads_dir = Path(settings.data_directory) / "uploads"

    scanner = FileScanner(search_dirs=[raw_dir, uploads_dir])
    discovered_files = scanner.scan_directories()

    if not discovered_files:
        logger.warning("No files discovered by scanner.")
        return

    logger.info(f"Discovered {len(discovered_files)} files to ingest.")
    engine = IngestionEngine()

    for path_str, dtype in discovered_files.items():
        try:
            dataset = engine.load_dataset(path_str)
            display_dataset_diagnostics(dataset)
        except Exception as e:
            logger.error(f"Failed to ingest file {path_str}: {e}")


def run_diagnostics_flow() -> None:
    """Executes the standard project initialization and diagnostics sequence."""
    # 1. Initialize folders
    ensure_directories_exist()

    # 2. Setup central logging system
    setup_logging(settings.log_level)

    # 3. Print Welcome Banner
    print_banner()

    logger.info("Initializing system diagnostics...")

    # 4. Check environmental profile
    verify_env_file()

    # 5. Output active config properties
    logger.info(f"Active Environment: {settings.project_env.value}")
    logger.info(f"Target Data Directory: {settings.data_directory}")
    logger.info(f"Binance Futures URL: {settings.testnet_url}")

    if not settings.binance_api_key or not settings.binance_secret_key:
        logger.warning("Binance keys are missing. Testnet trading bot features will be locked in live mode.")
    else:
        logger.info("Binance Futures credentials found and validated.")

    # 6. Run Phase 2 Ingestion Engine Diagnostics
    run_ingestion_diagnostics()

    # Confirmation statement
    console.print(
        "\n[bold green][OK][/bold green] [bold white]PrimeTrade AI project initialized successfully![/bold white]\n"
        "[yellow]Note: Bot operations are online via CLI. Type 'python main.py bot --help' to explore bot controls.[/yellow]\n"
    )


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Runs data ingestion diagnostics if no subcommand is executed."""
    if ctx.invoked_subcommand is None:
        run_diagnostics_flow()


if __name__ == "__main__":
    app()
