# PrimeTrade AI — API Reference

> Version 1.0.0 | Production Release

Complete reference documentation for all public APIs in PrimeTrade AI. Each section covers class constructors, public methods, parameters, return types, and usage examples.

---

## Table of Contents

1. [Ingestion Engine](#1-ingestion-engine)
2. [Analytics Engine](#2-analytics-engine)
3. [Statistics Engine](#3-statistics-engine)
4. [Visualization Engine](#4-visualization-engine)
5. [Strategy Engine](#5-strategy-engine)
6. [Report Generator](#6-report-generator)
7. [Trading Bot API](#7-trading-bot-api)
8. [CLI Reference](#8-cli-reference)

---

## 1. Ingestion Engine

**Package**: `analytics.ingestion`

### `DatasetLoader`

The primary entry point for all dataset loading operations. **Never call `pd.read_csv()` directly** — always use this class.

```python
from analytics.ingestion.loader import DatasetLoader

loader = DatasetLoader(data_dir="data/raw/")
trader_df, fear_greed_df = loader.load_all()
```

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `load_all()` | — | `tuple[pd.DataFrame, pd.DataFrame]` | Scans, detects, validates, and returns both datasets |
| `load_dataset(path)` | `path: str` | `pd.DataFrame` | Load a single file by path |
| `get_registry()` | — | `DatasetRegistry` | Returns the internal registry instance |

---

### `DatasetDetector`

Classifies a file as either trader history or Fear & Greed data using column header overlap scoring.

```python
from analytics.ingestion.dataset_detector import DatasetDetector

detector = DatasetDetector()
dataset_type = detector.detect("data/raw/historical_data.csv")
# Returns: "trader_history" | "fear_greed" | None
```

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `detect(file_path)` | `file_path: str` | `str \| None` | Detects dataset type; returns `None` if unrecognized |
| `score(columns, target_schema)` | `columns: list[str]`, `target_schema: set[str]` | `float` | Calculates overlap score (0.0–1.0) |

---

### `DatasetRegistry`

Thread-safe in-memory registry mapping dataset types to loaded DataFrames.

```python
from analytics.ingestion.dataset_registry import DatasetRegistry

registry = DatasetRegistry()
registry.register("trader_history", df)
df = registry.get("trader_history")
all_datasets = registry.list_all()
```

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `register(name, df)` | `name: str`, `df: pd.DataFrame` | `None` | Register a dataset by name |
| `get(name)` | `name: str` | `pd.DataFrame \| None` | Retrieve a dataset by name |
| `list_all()` | — | `list[dict]` | Return metadata for all registered datasets |
| `is_registered(name)` | `name: str` | `bool` | Check if a dataset name is in the registry |

---

### `FileScanner`

Discovers all supported files in a given directory.

```python
from analytics.ingestion.file_scanner import FileScanner

scanner = FileScanner(directory="data/raw/")
files = scanner.scan()
# Returns: list of file paths with supported extensions
```

**Supported extensions**: `.csv`, `.xlsx`, `.xls`, `.json`, `.parquet`

---

### `DataValidator`

Validates a loaded DataFrame against a required column schema.

```python
from analytics.ingestion.validator import DataValidator

validator = DataValidator()
is_valid, missing_cols = validator.validate(df, dataset_type="trader_history")
```

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `validate(df, dataset_type)` | `df: pd.DataFrame`, `dataset_type: str` | `tuple[bool, list[str]]` | Returns validity flag and list of missing columns |

---

## 2. Analytics Engine

**Package**: `analytics.analysis`

### `AnalyticsEngine`

Orchestrator that runs all sub-analyzers and exports results.

```python
from analytics.analysis.analytics_engine import AnalyticsEngine

engine = AnalyticsEngine(df=merged_df)
results = engine.run_all()
engine.export(output_dir="analytics/outputs/")
```

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `run_all()` | — | `dict` | Runs all analyzers and returns aggregated results dict |
| `export(output_dir)` | `output_dir: str` | `None` | Writes JSON, CSV, and Markdown summary files |
| `run_trader_analysis()` | — | `dict` | Win rate, loss rate, PnL statistics |
| `run_market_analysis()` | — | `dict` | Symbol rankings, volume distribution |
| `run_sentiment_analysis()` | — | `dict` | PnL grouped by Fear & Greed classification |
| `run_risk_analysis()` | — | `dict` | Drawdown, VaR, Sharpe ratio estimates |
| `run_time_analysis()` | — | `dict` | Hourly, daily, monthly activity heatmap data |
| `run_correlation_analysis()` | — | `dict` | Sentiment-PnL correlation coefficients |
| `run_performance_analysis()` | — | `dict` | Cumulative returns, rolling PnL curves |

---

## 3. Statistics Engine

**Package**: `analytics.statistics`

### `StatisticsEngine`

Runs all configured statistical tests and returns a unified report.

```python
from analytics.statistics.statistics_engine import StatisticsEngine

engine = StatisticsEngine(df=merged_df)
report = engine.run_all()
engine.export(output_dir="analytics/outputs/")
```

| Method | Returns | Description |
|---|---|---|
| `run_all()` | `dict` | Executes all tests and returns combined results |
| `run_descriptive()` | `dict` | Mean, median, std, skewness, kurtosis for key columns |
| `run_normality_tests()` | `dict` | Shapiro-Wilk, D'Agostino, and 1-sample KS tests |
| `run_correlation()` | `dict` | Pearson, Spearman, and Kendall correlations |
| `run_t_test()` | `dict` | Independent T-Test: profit vs loss PnL groups |
| `run_mann_whitney()` | `dict` | Mann-Whitney U: non-parametric profit vs loss |
| `run_anova()` | `dict` | One-Way ANOVA: PnL across sentiment regimes |
| `run_chi_square()` | `dict` | Chi-Square: sentiment regime vs outcome |
| `export(output_dir)` | `None` | Writes Markdown and JSON reports |

---

### Statistical Result Structure

All test methods return a dictionary with consistent keys:

```python
{
    "test_name": "Independent T-Test",
    "statistic": 3.421,
    "p_value": 0.0012,
    "significant": True,           # p_value < 0.05
    "interpretation": "...",        # Natural language observation
    "effect_size": 0.48,            # Cohen's d or Eta-squared
    "confidence_interval": [0.12, 0.84]
}
```

---

## 4. Visualization Engine

**Package**: `analytics.visualization`

### `VisualizationEngine`

Orchestrates chart generation for both static (Matplotlib) and interactive (Plotly) outputs.

```python
from analytics.visualization.visualization_engine import VisualizationEngine

engine = VisualizationEngine(df=merged_df, output_dir="analytics/outputs/charts/")
engine.generate_all()
```

| Method | Exports | Description |
|---|---|---|
| `generate_all()` | PNG + HTML | Generates all chart types |
| `plot_cumulative_pnl()` | PNG + HTML | Rolling cumulative PnL line chart |
| `plot_daily_pnl()` | PNG | Daily PnL bar chart |
| `plot_win_loss_donut()` | PNG + HTML | Win/Loss outcome donut chart |
| `plot_pnl_by_sentiment()` | PNG + HTML | PnL grouped by sentiment regime |
| `plot_symbol_ranking()` | PNG + HTML | Coin profitability ranking bars |
| `plot_hourly_heatmap()` | PNG | UTC hour × weekday activity heatmap |
| `plot_correlation_heatmap()` | PNG | Numerical feature correlation matrix |
| `plot_return_distribution()` | PNG + HTML | Histogram of closed PnL distribution |
| `build_interactive_dashboard()` | HTML | Unified dark-mode Plotly HTML dashboard |

---

## 5. Strategy Engine

**Package**: `analytics.strategy`

### `StrategyEngine`

Evaluates market metrics against configured thresholds and returns trading recommendations.

```python
from analytics.strategy.strategy_engine import StrategyEngine

engine = StrategyEngine(df=merged_df)
recommendations = engine.run()
engine.export(output_dir="analytics/outputs/strategy/")
```

| Method | Returns | Description |
|---|---|---|
| `run()` | `list[Recommendation]` | Evaluates all rules and returns recommendations |
| `export(output_dir)` | `None` | Writes JSON, CSV, and Markdown exports |

---

### `RuleBasedStrategy`

Configurable rule engine that maps metric thresholds to trading actions.

```python
from analytics.strategy.strategy_engine import RuleBasedStrategy

strategy = RuleBasedStrategy(
    min_win_rate=0.55,
    max_drawdown=0.15,
    min_fg_value=30,
    max_fg_value=70,
    min_trade_frequency=5,
)
action, confidence, explanation = strategy.evaluate(metrics)
```

**Supported Actions** (from `StrategyAction` enum):

| Action | Trigger Condition |
|---|---|
| `BUY` | Win rate ≥ threshold AND sentiment = Greed/Extreme Greed |
| `SELL` | Win rate < threshold AND sentiment = Fear/Extreme Fear |
| `HOLD` | Mixed signals or Neutral sentiment |
| `REDUCE_LEVERAGE` | Drawdown exceeds configured limit |
| `INCREASE_POSITION_SIZE` | Win rate > 0.65 AND low drawdown |
| `AVOID_TRADING` | Extreme Fear with high drawdown |

---

## 6. Report Generator

**Package**: `analytics.reports`

### `ReportEngine`

Compiles analytical results into publication-quality reports.

```python
from analytics.reports.report_engine import ReportEngine

engine = ReportEngine(
    analytics_results=results,
    statistics_results=stats,
    strategy_results=strategy,
    output_dir="analytics/reports/generated/",
)
engine.generate_all()
```

| Method | Output | Description |
|---|---|---|
| `generate_markdown()` | `.md` | Executive Summary in Markdown format |
| `generate_html()` | `.html` | Dark-mode styled HTML with embedded charts |
| `generate_pdf()` | `.pdf` | FPDF2-based PDF with cover page and tables |
| `generate_all()` | All formats | Runs all three generators |

---

## 7. Trading Bot API

**Package**: `trading_bot`

### `BinanceTestnetClient`

Wraps the `python-binance` client with retry logic and structured logging.

```python
from trading_bot.client.client import BinanceTestnetClient

client = BinanceTestnetClient(
    api_key="your_key",
    api_secret="your_secret",
    dry_run=True,   # Skip all actual API calls
)
balance = client.get_balance()
```

| Method | Returns | Description |
|---|---|---|
| `get_balance()` | `dict` | Returns USDT wallet balance details |
| `get_positions()` | `list[dict]` | Returns all open futures positions |
| `get_exchange_info(symbol)` | `dict` | Returns symbol filters from exchange |
| `create_order(**kwargs)` | `dict` | Submits a new order (or simulates in dry-run) |
| `cancel_order(symbol, order_id)` | `dict` | Cancels an open order |
| `get_open_orders(symbol)` | `list[dict]` | Returns all open orders for a symbol |

**Retry Policy**: Automatically retries on HTTP 429 (rate limit), HTTP 418, and HTTP 5xx errors using exponential backoff with jitter.

---

### `OrderManager`

Orchestrates order submission, validation, risk checking, and history recording.

```python
from trading_bot.order_manager import OrderManager
from trading_bot.orders.orders import FuturesOrder

manager = OrderManager(client=client, dry_run=True)
order = FuturesOrder(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.001, leverage=10)
result = manager.submit(order)
```

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `submit(order)` | `order: FuturesOrder` | `dict` | Full pipeline: validate → risk check → execute → log |
| `get_history()` | — | `list[dict]` | Returns all order history records |
| `export_history(fmt)` | `fmt: "json"\|"csv"` | `Path` | Exports history to file |

---

### `OrderValidator`

Pre-trade compliance checks against exchange rules.

```python
from trading_bot.validators.validators import OrderValidator

validator = OrderValidator(client=client)
validator.validate(order)   # Raises OrderValidationError on failure
```

**Checks performed**:
1. Leverage within 1–125
2. Quantity matches LOT_SIZE step size
3. Price matches PRICE_FILTER tick size
4. Notional ≥ MIN_NOTIONAL
5. Initial margin ≤ available wallet balance

---

### `RiskManager`

Portfolio-level risk checks enforcing hard limits before order submission.

```python
from trading_bot.risk_manager import RiskManager

risk = RiskManager(
    client=client,
    max_single_trade_pct=10.0,
    max_leverage=20,
    max_drawdown_pct=15.0,
)
ok = risk.check_position_size(symbol="BTCUSDT", quantity=0.001, price=45000.0, leverage=10)
ok = risk.check_leverage(leverage=10)
ok = risk.check_drawdown()
```

---

### `PositionManager`

Tracks and queries active futures positions.

```python
from trading_bot.position_manager import PositionManager

pm = PositionManager(client=client)
positions = pm.get_positions()         # All positions with non-zero amount
pnl = pm.get_unrealized_pnl("BTCUSDT")
```

---

### `FuturesOrder` Schema

Pydantic v2 model defining order parameters.

```python
from trading_bot.orders.orders import FuturesOrder

# MARKET order
order = FuturesOrder(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.001, leverage=10)

# LIMIT order
order = FuturesOrder(symbol="ETHUSDT", side="SELL", order_type="LIMIT", quantity=0.1, leverage=5, price=3000.0)

# STOP_LIMIT order
order = FuturesOrder(symbol="BTCUSDT", side="SELL", order_type="STOP_LIMIT", quantity=0.001, leverage=10, price=44000.0, stop_price=44500.0)
```

| Field | Type | Required | Description |
|---|---|---|---|
| `symbol` | `str` | ✅ | Trading pair (e.g. `BTCUSDT`) |
| `side` | `Literal["BUY","SELL"]` | ✅ | Trade direction |
| `order_type` | `Literal["MARKET","LIMIT","STOP_LIMIT"]` | ✅ | Execution type |
| `quantity` | `float > 0` | ✅ | Order size in base asset |
| `leverage` | `int` 1–125 | ✅ | Position leverage |
| `price` | `float > 0` | LIMIT/STOP_LIMIT only | Limit price |
| `stop_price` | `float > 0` | STOP_LIMIT only | Trigger price |

---

## 8. CLI Reference

**Package**: `trading_bot.cli` | **Runner**: `python -m trading_bot.cli`

### Commands

```bash
# Show help
python -m trading_bot.cli --help

# Check account balance
python -m trading_bot.cli balance

# Place a MARKET order
python -m trading_bot.cli order \
    --symbol BTCUSDT \
    --side BUY \
    --type MARKET \
    --quantity 0.001 \
    --leverage 10

# Place a LIMIT order
python -m trading_bot.cli order \
    --symbol ETHUSDT \
    --side SELL \
    --type LIMIT \
    --quantity 0.1 \
    --leverage 5 \
    --price 3000.0

# Place a STOP_LIMIT order
python -m trading_bot.cli order \
    --symbol BTCUSDT \
    --side SELL \
    --type STOP_LIMIT \
    --quantity 0.001 \
    --leverage 10 \
    --price 44000.0 \
    --stop-price 44500.0

# Cancel an open order
python -m trading_bot.cli cancel \
    --symbol BTCUSDT \
    --order-id 123456

# View order history
python -m trading_bot.cli history

# Dry-run mode (default when DRY_RUN=true in .env)
python -m trading_bot.cli order \
    --symbol BTCUSDT \
    --side BUY \
    --type MARKET \
    --quantity 0.001 \
    --leverage 10 \
    --dry-run
```

### Global Flags

| Flag | Description |
|---|---|
| `--dry-run` | Simulate the order without API submission |
| `--help` | Display command help |
| `--version` | Display CLI version |

---

## Error Reference

| Exception | Module | Raised When |
|---|---|---|
| `DatasetDetectionError` | `analytics.ingestion` | File type cannot be determined |
| `SchemaValidationError` | `analytics.ingestion` | Required columns are missing |
| `InsufficientDataError` | `analytics.preprocessing` | DataFrame has fewer than minimum rows |
| `OrderValidationError` | `trading_bot.validators` | Order fails exchange compliance checks |
| `InsufficientMarginError` | `trading_bot.validators` | Account balance too low for initial margin |
| `RiskLimitError` | `trading_bot.risk_manager` | Position size or drawdown limit exceeded |
| `BinanceConnectionError` | `trading_bot.client` | API connection or authentication failure |
