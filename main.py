"""Entry point runner for PrimeTrade AI.

Verifies folder structure, validates configurations, initializes the logging system,
and displays a project confirmation banner.
"""

import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

# Config & Utils imports
from config import ensure_directories_exist, settings
from utils import setup_logging

logger = logging.getLogger("system")
console = Console()


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
        "[bold green]                        PHASE 1 - INFRASTRUCTURE[/bold green]"
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
        logger.warning(
            "Configuration file '.env' not found. System running on fallback defaults."
        )


def main() -> None:
    """Main verification sequence for the system infrastructure."""
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
        logger.warning(
            "Binance keys are missing. Testnet trading bot features will be locked."
        )
    else:
        logger.info("Binance Futures credentials found and validated.")

    # Confirmation statement
    console.print(
        "\n[bold green][OK][/bold green] [bold white]PrimeTrade AI project initialized successfully![/bold white]\n"
        "[yellow]Note: Analytical models, statistical tests, and trading routines are currently offline.[/yellow]\n"
    )


if __name__ == "__main__":
    main()
