# PrimeTrade AI — Architecture Reference

> Version 1.0.0 | Production Release

This document describes the complete system architecture of PrimeTrade AI — a sentiment-driven cryptocurrency analytics suite and Binance Futures Testnet trading bot.

---

## 1. System Overview

PrimeTrade AI is organized into six distinct operational layers. Each layer has a clearly defined responsibility with no cross-layer coupling:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                           │
│          Streamlit Dashboard  •  Typer CLI                          │
├─────────────────────────────────────────────────────────────────────┤
│                       Execution Layer                               │
│     Binance Testnet Client  •  Order Manager  •  Risk Manager       │
├─────────────────────────────────────────────────────────────────────┤
│                      Strategy Layer                                 │
│       Rule-Based Strategy Engine  •  Recommendation Exporter        │
├─────────────────────────────────────────────────────────────────────┤
│                      Analytics Layer                                │
│  Analytics Engine  •  Statistics Engine  •  Visualization Engine    │
│               Report Generator                                      │
├─────────────────────────────────────────────────────────────────────┤
│                    Data Processing Layer                            │
│  Feature Engineer  •  Preprocessor  •  Normalizer  •  Merger        │
├─────────────────────────────────────────────────────────────────────┤
│                      Ingestion Layer                                │
│   File Scanner  •  Dataset Detector  •  Schema Mapper  •  Registry  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Data Flow

```mermaid
graph TD
    A["📁 Raw Files\n(CSV / XLSX / JSON / Parquet)"] --> B["🔍 File Scanner\nDiscovers files in data/raw/"]
    B --> C["🧠 Dataset Detector\nClassifies: Trader or Fear & Greed"]
    C --> D["🗺️ Schema Mapper\nNormalizes column names"]
    D --> E["✅ Data Validator\nChecks schema compliance"]
    E --> F["📋 Dataset Registry\nRegisters and caches loaded DataFrames"]
    F --> G["🧹 Preprocessor / Normalizer\nCleaning, deduplication, type casting"]
    G --> H["⚙️ Feature Engineer\nAdds PnL, direction, rolling metrics, time features"]
    H --> I["🔗 Chronological Merger\nNearest-date asof join: trader ↔ sentiment"]
    I --> J["📊 Analytics Engine\nTrader / Market / Risk / Correlation / Time analysis"]
    I --> K["📐 Statistics Engine\nPearson / Spearman / T-Test / ANOVA / Chi-Square"]
    I --> L["📈 Visualization Engine\nMatplotlib static + Plotly interactive charts"]
    J & K & L --> M["📝 Report Generator\nMarkdown / HTML / PDF reports"]
    J --> N["🎯 Strategy Engine\nBUY / SELL / HOLD / REDUCE_LEVERAGE recommendations"]
    N --> O["🤖 Trading Bot\nOrder validation + Binance Testnet execution"]
    M & N & O --> P["🖥️ Streamlit Dashboard\n10-page interactive UI"]
```

---

## 3. Module Dependency Graph

```mermaid
graph LR
    config --> utils
    config --> analytics
    config --> trading_bot
    utils --> analytics
    utils --> trading_bot
    analytics/ingestion --> analytics/preprocessing
    analytics/preprocessing --> analytics/feature_engineering
    analytics/feature_engineering --> analytics/analysis
    analytics/feature_engineering --> analytics/statistics
    analytics/feature_engineering --> analytics/visualization
    analytics/analysis --> analytics/strategy
    analytics/statistics --> analytics/reports
    analytics/visualization --> analytics/reports
    analytics/strategy --> trading_bot
    trading_bot --> dashboard
    analytics --> dashboard
```

---

## 4. Trading Bot Request & Validation Lifecycle

```mermaid
sequenceDiagram
    participant CLI as CLI / Dashboard
    participant OM as OrderManager
    participant V as OrderValidator
    participant RM as RiskManager
    participant C as BinanceTestnetClient
    participant API as Binance Testnet API

    CLI->>OM: submit(FuturesOrder)
    OM->>V: validate(order)
    V->>C: get_exchange_info(symbol)
    C->>API: GET /fapi/v1/exchangeInfo
    API-->>C: filters (tick size, step size, min notional)
    C-->>V: filters
    V->>V: check precision, min notional, leverage bounds
    alt Validation fails
        V-->>OM: raise OrderValidationError
        OM-->>CLI: error summary (rich Panel)
    else Validation passes
        V-->>OM: validated order
        OM->>RM: check_position_size(symbol, qty, price, leverage)
        RM->>C: get_balance()
        C->>API: GET /fapi/v2/account
        API-->>C: wallet balance
        C-->>RM: balance
        RM->>RM: check drawdown, capital-at-risk, position size
        alt Risk check fails
            RM-->>OM: raise RiskLimitError
            OM-->>CLI: error summary
        else Risk check passes
            OM->>C: create_order(symbol, side, type, qty, price)
            C->>API: POST /fapi/v1/order
            API-->>C: order result
            C-->>OM: order result
            OM->>OM: log to JSON + CSV history
            OM-->>CLI: success summary (rich Table)
        end
    end
```

---

## 5. Dashboard Page Dependency Map

```mermaid
graph TD
    App["app.py\nRouter + Shared State"] --> Home["🏠 Home\nSystem status cards"]
    App --> Upload["📤 Upload\nFile upload + profile"]
    App --> Analytics["📊 Analytics\nKPI metrics display"]
    App --> Charts["📈 Charts\nPlotly interactive figures"]
    App --> Statistics["📐 Statistics\nHypothesis test runner"]
    App --> Reports["📝 Reports\nDownload PDF/HTML/MD"]
    App --> Strategy["🎯 Strategy\nRecommendation engine UI"]
    App --> Bot["🤖 Trading Desk\nOrder routing form"]
    App --> Logs["🖥️ System Logs\nLog file terminal"]
    App --> Settings["⚙️ Settings\n.env editor"]

    Upload --> IngestionEngine["analytics/ingestion"]
    Analytics --> AnalyticsEngine["analytics/analysis"]
    Charts --> VizEngine["analytics/visualization"]
    Statistics --> StatsEngine["analytics/statistics"]
    Reports --> ReportEngine["analytics/reports"]
    Strategy --> StrategyEngine["analytics/strategy"]
    Bot --> TradingBot["trading_bot/"]
    Logs --> LogFiles["logs/*.log"]
    Settings --> DotEnv[".env"]
```

---

## 6. Directory Structure

```
PrimeTrade-AI/
├── .github/
│   └── workflows/
│       └── ci.yml                   # 5-job CI/CD pipeline
├── analytics/
│   ├── ingestion/                   # File detection and registry
│   ├── preprocessing/               # Normalization, cleaning, merge
│   ├── feature_engineering/         # Metric and indicator generation
│   ├── analysis/                    # Behavioral and profitability metrics
│   ├── statistics/                  # Statistical significance testing
│   ├── visualization/               # Matplotlib + Plotly chart generators
│   ├── strategy/                    # Rule-based recommendation engine
│   ├── reports/                     # HTML / PDF / Markdown report compilers
│   └── outputs/                     # Generated charts, reports, and exports
├── trading_bot/
│   ├── client/                      # Binance Testnet REST client + retry
│   ├── orders/                      # Pydantic order schemas
│   ├── validators/                  # Pre-trade validation logic
│   ├── risk_manager.py              # Portfolio and position risk checks
│   ├── position_manager.py          # Active position tracking
│   ├── order_manager.py             # Orchestrator + history exporter
│   └── cli.py                       # Typer-based CLI entrypoint
├── dashboard/
│   ├── app.py                       # Streamlit multi-page router
│   ├── pages/                       # 10 individual page modules
│   ├── components/                  # Reusable UI card components
│   └── styles/                      # CSS theme and glassmorphic styles
├── config/
│   ├── settings.py                  # .env-driven system configuration
│   ├── paths.py                     # Centralized path constants
│   ├── constants.py                 # Numerical thresholds and limits
│   └── enums.py                     # Shared enumerations
├── utils/
│   ├── logger.py                    # Multi-file rotating logger
│   ├── exceptions.py                # Custom exception hierarchy
│   └── helpers.py                   # Generic helper functions
├── tests/
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── integration/                 # End-to-end pipeline & bot tests
│   └── test_*.py                    # Module-level unit tests
├── docs/
│   ├── ARCHITECTURE.md              # This file
│   └── API_REFERENCE.md             # Public API documentation
├── data/
│   ├── raw/                         # Original uploaded datasets
│   ├── processed/                   # Cleaned and merged outputs
│   ├── uploads/                     # Dashboard-uploaded files
│   └── exports/                     # Order history exports
├── logs/                            # system.log, analytics.log, bot.log, errors.log
├── Dockerfile                       # Multi-stage Docker build
├── docker-compose.yml               # dashboard + analytics + bot services
├── .pre-commit-config.yaml          # Pre-commit hooks
├── pyproject.toml                   # black / isort / project metadata
├── .flake8                          # Flake8 configuration
├── pytest.ini                       # Pytest configuration
├── .coveragerc                      # Coverage configuration
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variable template
├── main.py                          # Verification and pipeline runner
├── README.md                        # Quickstart documentation
├── RELEASE_NOTES.md                 # Release changelog
└── PROJECT_REPORT.md                # Permanent project record
```

---

## 7. Key Design Decisions

| Decision | Rationale |
|---|---|
| **Single ingestion entry point** | All downstream modules use `DatasetLoader` — no raw `pd.read_csv()` calls allowed |
| **Timezone-naive timestamps** | `pd.merge_asof` requires matching dtypes; all timestamps normalized to `datetime64[ns]` |
| **Pydantic v2 for bot schemas** | Strict field validation at the boundary catches invalid orders before any API call |
| **Dry-run mode** | All bot commands default to `DRY_RUN=true` for safe testing without API credentials |
| **Non-root Docker user** | Security best practice — container runs as `primetrade` (UID 1001) |
| **Multi-stage Docker build** | Separates build tools from runtime; reduces final image size significantly |
| **Pre-commit hooks** | Enforces code quality locally before any push, avoiding CI failures |

---

## 8. Configuration & Secrets

All credentials and environment-specific settings are controlled via `.env` (git-ignored). The `.env.example` template documents all supported variables:

| Variable | Description | Default |
|---|---|---|
| `BINANCE_API_KEY` | Binance Futures Testnet API Key | *(required)* |
| `BINANCE_SECRET_KEY` | Binance Futures Testnet Secret | *(required)* |
| `PROJECT_ENV` | `DEVELOPMENT` / `STAGING` / `PRODUCTION` | `DEVELOPMENT` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `DRY_RUN` | Skip live order submission | `true` |
| `DEFAULT_LEVERAGE` | Default position leverage | `10` |
| `MAX_LEVERAGE` | Hard cap on leverage | `20` |
| `MAX_DRAWDOWN_PCT` | Max allowed drawdown before halt | `15.0` |
| `MAX_CAPITAL_AT_RISK_PCT` | Max portfolio exposure | `50.0` |
| `MAX_SINGLE_TRADE_PCT` | Max single trade as % of balance | `10.0` |
