# PrimeTrade AI

> **Sentiment-Driven Crypto Trading Analytics & Binance Futures Testnet Bot**

[![CI/CD](https://github.com/yourusername/TradingBOT/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/TradingBOT/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/yourusername/TradingBOT/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/TradingBOT)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://hub.docker.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Release](https://img.shields.io/badge/release-v1.0.0-brightgreen)](https://github.com/yourusername/TradingBOT/releases/tag/v1.0.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)

PrimeTrade AI is a production-grade, end-to-end platform that bridges the gap between **Bitcoin sentiment analysis** and **automated futures trading**. It ingests historical trade records and the Bitcoin Fear & Greed Index, applies rigorous statistical testing, generates publication-quality reports, formulates actionable trading strategies, and executes orders on the Binance Futures Testnet — all through a beautiful Streamlit dashboard or a powerful CLI.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📥 **Smart Ingestion** | Auto-detects CSV, Excel, JSON, and Parquet formats with column-overlap scoring |
| 🧹 **Production Preprocessing** | Deduplication, timezone-normalization, anomaly filtering, lookahead-safe merge |
| ⚙️ **Feature Engineering** | Rolling PnL, cumulative returns, time partitions, trade direction indicators |
| 📊 **Analytics Engine** | 8 analyzers: trader, market, sentiment, risk, time, correlation, performance |
| 📐 **Statistics Engine** | T-Test, ANOVA, Mann-Whitney, Chi-Square, Pearson/Spearman/Kendall, normality tests |
| 📈 **Visualization Engine** | 10+ chart types in Matplotlib (PNG) + Plotly (interactive HTML) |
| 📝 **Report Generator** | PDF, HTML, and Markdown executive / technical / business reports |
| 🎯 **Strategy Engine** | Rule-based BUY/SELL/HOLD with confidence scores and natural language explanations |
| 🤖 **Testnet Bot** | Market, Limit, Stop-Limit orders with retry, validation, and risk management |
| 🖥️ **Streamlit Dashboard** | 10-page glassmorphic dark-mode UI |
| 🐳 **Docker Ready** | Multi-stage image, Docker Compose with 3 services |
| ✅ **Quality Assured** | 67 unit tests, integration tests, pre-commit hooks, CI/CD pipeline |

---

## 🚀 Quick Start

### Option A: Local (Python)

```bash
# 1. Clone
git clone https://github.com/yourusername/TradingBOT.git
cd TradingBOT

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Binance Testnet API keys

# 5. Verify installation
python main.py

# 6. Launch dashboard
streamlit run dashboard/app.py
```

### Option B: Docker Compose

```bash
# Clone and configure
git clone https://github.com/yourusername/TradingBOT.git
cd TradingBOT
cp .env.example .env
# Edit .env with your keys

# Launch Streamlit dashboard
docker-compose up dashboard

# Run analytics pipeline (one-shot)
docker-compose --profile analytics up analytics

# Open trading bot CLI
docker-compose --profile bot run bot python -m trading_bot.cli --help
```

The dashboard will be available at **http://localhost:8501**

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and set the following:

```env
# Binance Futures Testnet (get keys at testnet.binancefuture.com)
BINANCE_API_KEY=your_testnet_api_key
BINANCE_SECRET_KEY=your_testnet_secret_key

# Environment
PROJECT_ENV=DEVELOPMENT          # DEVELOPMENT | STAGING | PRODUCTION
LOG_LEVEL=INFO                   # DEBUG | INFO | WARNING | ERROR | CRITICAL

# Safety (DRY_RUN=true skips all real API calls)
DRY_RUN=true

# Risk limits
DEFAULT_LEVERAGE=10
MAX_LEVERAGE=20
MAX_DRAWDOWN_PCT=15.0            # Halt trading if drawdown exceeds 15%
MAX_CAPITAL_AT_RISK_PCT=50.0    # Max 50% of portfolio in open positions
MAX_SINGLE_TRADE_PCT=10.0       # Max 10% of balance per single trade
```

---

## 📂 Project Structure

```
TradingBOT/
├── .github/workflows/
│   └── ci.yml                     # 5-job CI/CD: lint → test → integration → docker → release
├── analytics/
│   ├── ingestion/                 # File scanner, detector, mapper, validator, registry
│   ├── preprocessing/             # Normalizer, cleaner, asof merger
│   ├── feature_engineering/       # Rolling/cumulative metrics, time features
│   ├── analysis/                  # 8 sub-analyzers + AnalyticsEngine
│   ├── statistics/                # 8 test types + StatisticsEngine
│   ├── visualization/             # Matplotlib + Plotly + dashboard assembler
│   ├── strategy/                  # RuleBasedStrategy + StrategyEngine
│   └── reports/                   # PDF / HTML / Markdown report compilers
├── trading_bot/
│   ├── client/                    # BinanceTestnetClient + retry decorator
│   ├── orders/                    # FuturesOrder Pydantic schema
│   ├── validators/                # OrderValidator (leverage, notional, margin)
│   ├── risk_manager.py            # Drawdown, position size, leverage caps
│   ├── position_manager.py        # Active position tracking
│   ├── order_manager.py           # Orchestrator + JSON/CSV history
│   └── cli.py                     # Typer CLI: balance, order, cancel, history
├── dashboard/
│   ├── app.py                     # Multi-page Streamlit router
│   ├── pages/                     # 10 pages: Home → Settings
│   ├── components/                # Reusable UI cards
│   └── styles/                    # Glassmorphic dark CSS
├── config/                        # settings.py, paths.py, constants.py, enums.py
├── utils/                         # logger.py, exceptions.py, helpers.py
├── tests/
│   ├── conftest.py                # Shared fixtures
│   ├── integration/               # End-to-end pipeline + bot tests
│   └── test_*.py                  # 8 unit test modules (67 tests)
├── docs/
│   ├── ARCHITECTURE.md            # System diagrams + design decisions
│   └── API_REFERENCE.md           # Complete public API documentation
├── data/                          # raw/, processed/, uploads/, exports/
├── logs/                          # system.log, analytics.log, bot.log, errors.log
├── Dockerfile                     # Multi-stage build
├── docker-compose.yml             # dashboard + analytics + bot services
├── .pre-commit-config.yaml        # black, isort, flake8, bandit hooks
├── pyproject.toml                 # black/isort config + project metadata
├── .flake8                        # Linting configuration
├── pytest.ini                     # Test configuration + coverage
├── .coveragerc                    # Coverage reporting config
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── RELEASE_NOTES.md               # Changelog
├── main.py                        # Verification and pipeline runner
└── PROJECT_REPORT.md              # Permanent project record
```

---

## 🤖 Trading Bot CLI

```bash
# Check wallet balance
python -m trading_bot.cli balance

# Place a MARKET BUY order (dry-run by default)
python -m trading_bot.cli order \
    --symbol BTCUSDT \
    --side BUY \
    --type MARKET \
    --quantity 0.001 \
    --leverage 10

# View order history
python -m trading_bot.cli history

# Cancel an order
python -m trading_bot.cli cancel --symbol BTCUSDT --order-id 123456
```

---

## 🧪 Running Tests

```bash
# Full test suite with coverage
pytest

# Unit tests only (fast)
pytest -m "not integration" -v

# Integration tests only
pytest -m integration tests/integration/ -v

# With HTML coverage report
pytest --cov-report=html
open htmlcov/index.html
```

---

## 🔧 Code Quality

```bash
# Install pre-commit hooks (once)
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Format code
black .

# Sort imports
isort . --profile black

# Lint
flake8 . --max-line-length=127
```

---

## 📊 Dashboard Pages

| Page | Description |
|---|---|
| 🏠 **Home** | Real-time system status, active dataset metadata |
| 📤 **Upload** | Drag-and-drop file upload with format detection |
| 📊 **Analytics** | KPI cards, PnL metrics, trader statistics |
| 📈 **Charts** | Interactive Plotly figures |
| 📐 **Statistics** | Run hypothesis tests with one click |
| 📝 **Reports** | Generate and download PDF/HTML/Markdown |
| 🎯 **Strategy** | Configure parameters, run recommendations |
| 🤖 **Trading Desk** | Order forms with live validation |
| 🖥️ **System Logs** | Styled log terminal |
| ⚙️ **Settings** | In-app `.env` editor |

---

## 🗺️ Development Roadmap

All phases complete ✅

| Phase | Feature | Status |
|---|---|---|
| 1 | Architecture & Infrastructure | ✅ Complete |
| 2 | Dataset Ingestion Engine | ✅ Complete |
| 3 | Data Cleaning & Preprocessing | ✅ Complete |
| 4 | Feature Engineering | ✅ Complete |
| 5 | Analytics Engine | ✅ Complete |
| 6 | Statistical Analysis Engine | ✅ Complete |
| 7 | Visualization Engine | ✅ Complete |
| 8 | Report Generator | ✅ Complete |
| 9 | Strategy Recommendation Engine | ✅ Complete |
| 10 | Binance Futures Testnet Bot | ✅ Complete |
| 11 | Streamlit Dashboard | ✅ Complete |
| 12 | Testing & QA | ✅ Complete |
| 13 | Docker & Deployment | ✅ Complete |
| 14 | Documentation | ✅ Complete |

---

## 📚 Documentation

- [Architecture Reference](docs/ARCHITECTURE.md) — System diagrams, data flow, design decisions
- [API Reference](docs/API_REFERENCE.md) — Full API for all engines, schemas, and CLI
- [Release Notes](RELEASE_NOTES.md) — Changelog and version history
- [Project Report](PROJECT_REPORT.md) — Permanent project record

---

## ⚠️ Disclaimer

PrimeTrade AI connects **exclusively** to the Binance Futures **Testnet**. No real money is ever at risk. This project is built for educational and research purposes only.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with Python 3.12 · Streamlit · Plotly · python-binance · Pydantic v2 · pytest · Docker*
