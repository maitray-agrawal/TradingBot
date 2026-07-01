# Release Notes

## v1.0.0 — Production Release

**Release Date**: 2026-07-01

PrimeTrade AI v1.0.0 is the first stable production release of the complete sentiment-driven crypto trading analytics and Binance Futures Testnet bot system.

---

### What's Included

#### 🏗️ Infrastructure (Phase 1)
- Modular Python package scaffold with SOLID architecture
- Centralized `config/` package (settings, paths, constants, enums)
- Multi-file rotating logging system (analytics, bot, errors)
- Custom exception hierarchy
- Generic utilities library
- GitHub Actions CI pipeline
- Entry point verification (`main.py`)

#### 📥 Dataset Ingestion Engine (Phase 2)
- Auto-detects CSV, XLSX, JSON, and Parquet formats
- Column-overlap scoring for dataset type classification
- Schema mapper normalizing 30+ column name variants
- Data validator enforcing minimum schema requirements
- In-memory `DatasetRegistry` with metadata tracking
- Upload handler for runtime file additions

#### 🧹 Preprocessing & Feature Engineering (Phases 3–4)
- Header normalization, casing, deduplication, and type casting
- Timezone-naive timestamp standardization (ISO, unix-s, unix-ms)
- Anomaly filtering (negative prices, zero sizes)
- Time-partition features: hour, day, weekday, month, week
- Rolling PnL and volume windows
- Cumulative PnL tracking
- Nearest-date `merge_asof` chronological join (lookahead-safe)

#### 📊 Analytics Engine (Phase 5)
- Trader analysis: win rate, PnL statistics, trade frequency
- Market analysis: symbol rankings, volume distribution
- Sentiment analysis: PnL grouped by Fear & Greed regime
- Risk analysis: drawdown, VaR, Sharpe ratio
- Time analysis: UTC session heatmaps
- Correlation analysis: sentiment vs performance
- Performance analysis: cumulative and rolling return curves

#### 📐 Statistical Analysis Engine (Phase 6)
- Descriptive statistics with natural language observations
- Pearson, Spearman, and Kendall correlation
- Independent T-Test (profit vs loss groups)
- Mann-Whitney U Test (non-parametric)
- One-Way ANOVA (PnL across sentiment regimes)
- Chi-Square test (sentiment vs outcome)
- Shapiro-Wilk, D'Agostino, and KS normality tests
- Confidence intervals (Wilson score, Student-t)
- Effect sizes (Cohen's d, Eta-squared)

#### 📈 Visualization Engine (Phase 7)
- Matplotlib static charts: PNG and SVG exports
- Plotly interactive charts: HTML exports
- Chart types: cumulative PnL, daily PnL bars, win/loss donut, sentiment violin/box, symbol ranking, hourly heatmap, correlation heatmap, return distribution, scatter with regression
- Unified dark-mode Plotly HTML dashboard assembler

#### 📝 Report Generator (Phase 8)
- Markdown executive summary
- Dark-mode styled HTML report with embedded charts
- FPDF2 PDF with cover page, numbered sections, PnL tables, and chart embeds
- Three report levels: Executive Summary, Technical Report, Business Report

#### 🎯 Strategy Engine (Phase 9)
- `StrategyAction` enum: BUY, SELL, HOLD, REDUCE_LEVERAGE, INCREASE_POSITION_SIZE, AVOID_TRADING
- Configurable `RuleBasedStrategy` with Pydantic-backed thresholds
- Confidence scores (0.0–1.0) for each recommendation
- Natural language explanation per recommendation
- JSON, CSV, and Markdown export

#### 🤖 Binance Futures Testnet Bot (Phase 10)
- `BinanceTestnetClient` with exponential backoff retry (HTTP 429, 418, 5xx)
- Pydantic v2 `FuturesOrder` schema (MARKET, LIMIT, STOP_LIMIT)
- `OrderValidator`: leverage, notional, tick size, initial margin checks
- `RiskManager`: position size, leverage cap, drawdown halt
- `PositionManager`: unrealized PnL, mark price, liquidation tracking
- `OrderManager`: full orchestration + JSON/CSV history export
- Dry-run mode for safe simulation
- Typer CLI with `balance`, `order`, `cancel`, `history` commands

#### 🖥️ Streamlit Dashboard (Phase 11)
- 10-page multi-page Streamlit dashboard
- Glassmorphic dark-mode CSS theme
- Pages: Home, Upload, Analytics, Charts, Statistics, Reports, Strategy, Trading Desk, System Logs, Settings
- Interactive filtering, download buttons, and live KPI cards
- System log terminal with styled `code` blocks

#### ✅ Testing & QA (Phase 12)
- 67 unit tests across 8 test files
- Shared `conftest.py` fixtures (DataFrames, mock Binance client, temp dirs)
- Integration tests: full pipeline end-to-end + bot dry-run lifecycle
- `pytest.ini` with coverage thresholds and test markers
- `.coveragerc` with 70% minimum coverage enforcement
- Pre-commit hooks: black, isort, flake8, bandit, file hygiene

#### 🐳 Docker & Deployment (Phase 13)
- Multi-stage Dockerfile (builder + runtime, non-root `primetrade` user)
- Docker Compose: `dashboard`, `analytics` (profile), `bot` (profile) services
- `.dockerignore` excluding raw data, tests, and dev configs
- Health check on `/_stcore/health` with 30s interval

#### 📚 Documentation (Phase 14)
- `docs/ARCHITECTURE.md`: full Mermaid diagrams (data flow, module graph, bot lifecycle, dashboard map)
- `docs/API_REFERENCE.md`: complete public API for all engines, CLI, and error types
- Updated `README.md` with badges, Docker quickstart, and complete feature overview
- `pyproject.toml` with project metadata for PyPI-readiness

---

### Dependency Summary

| Package | Version | Purpose |
|---|---|---|
| pandas | ≥2.0.0 | DataFrame processing |
| numpy | ≥1.24.0 | Numerical operations |
| scipy | ≥1.10.0 | Statistical tests |
| plotly | ≥5.14.0 | Interactive charts |
| streamlit | ≥1.22.0 | Dashboard UI |
| python-binance | ≥1.0.17 | Binance API client |
| pydantic | ≥2.0.0 | Schema validation |
| typer | ≥0.9.0 | CLI framework |
| rich | ≥13.4.0 | Terminal output |
| fpdf2 | ≥2.7.0 | PDF generation |
| pytest | ≥7.3.0 | Testing framework |
| pytest-cov | ≥4.1.0 | Coverage reporting |
| pre-commit | ≥3.3.0 | Git hook management |

---

### Known Limitations

- Sentiment resolution is daily (Fear & Greed Index updates once per day)
- Binance Futures Testnet only — production mainnet trading is not supported
- Streamlit dashboard loads full DataFrames into memory; performance may degrade with millions of rows

---

### Upgrade Notes

This is the initial stable release — no upgrade path required.

---

### Contributors

Built end-to-end by the PrimeTrade AI development team.

---

*For architecture details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)*
*For API reference, see [docs/API_REFERENCE.md](docs/API_REFERENCE.md)*
