# PrimeTrade AI

PrimeTrade AI is a production-quality, sentiment-driven cryptocurrency trading analytics suite and automated Binance Futures Testnet trading bot. The system combines statistical analysis of market sentiment (Bitcoin Fear & Greed Index) with historical trade data to evaluate performance, make recommendations, and execute orders within strict risk bounds.

---

## Key Features
- **Centralized Project Scaffold**: Structured using SOLID design principles and robust modular packaging.
- **Dynamic Data Pipeline**: Automatically scans, classifies, cleans, and merges diverse dataset formats (CSV, Excel, JSON, Parquet) with lookahead safety.
- **Behavioral Statistics**: Hypothesis significance tests validating correlation between market sentiment indicators and trader metrics.
- **Strategy Recommendation Engine**: Formulates trading parameters and actions based on current fear & greed regimes.
- **Binance Futures Testnet Bot**: Standardized execution wrapper supporting leverage validation, order execution, and failsafe limits.
- **Interactive Streamlit Dashboard**: Seamless multi-page dashboard displaying visual reports, uploads, parameters control, and live trade logs.

---

## Project Structure
```
PrimeTrade-AI/
├── config/              # Centralized configuration, paths, enums, constants
├── utils/               # Structured logging, exception classes, generic helpers
├── analytics/           # Ingestion, preprocessing, stats, reports, and strategy engines
│   ├── ingestion/       # Automatic file detection and classification
│   ├── preprocessing/   # Normalization, cleaning, and lookahead-safe merge
│   ├── feature_engineering/ # Rolling values, return PnLs, time indicators
│   ├── statistics/      # Correlation, ANOVA, T-Tests, and non-parametric checks
│   ├── visualization/   # Static and Plotly chart generation
│   ├── strategy/        # Rule-based sentiment recommendation model
│   └── reports/         # PDF and HTML report generators
├── trading_bot/         # Testnet order execution client and validations
├── dashboard/           # Multi-page Streamlit dashboard interface
├── data/                # Data storage (raw, processed, uploads, exports)
├── logs/                # central system logging directory
├── docs/                # Technical documentation
├── tests/               # Test suites
├── main.py              # Verification and pipeline runner
├── requirements.txt     # Python package dependencies
├── .env.example         # System configurations template
├── .gitignore           # Ignored version control paths
└── PROJECT_REPORT.md    # Permanent project record
```

---

## Installation

### Prerequisites
- Python 3.12+
- Git

### Setup
1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd TradingBOT
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration
1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your details:
   - `BINANCE_API_KEY`: Your Binance Futures Testnet API Key.
   - `BINANCE_SECRET_KEY`: Your Binance Futures Testnet API Secret.
   - `PROJECT_ENV`: `DEVELOPMENT`, `STAGING`, or `PRODUCTION`.
   - `LOG_LEVEL`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).

---

## Running the Application
To verify that the scaffolding, paths, configurations, and loggers are initialized correctly:
```bash
python main.py
```

---

## Development Roadmap
- **Phase 1**: Architecture & Infrastructure Initialization (Completed)
- **Phase 2**: Dataset Ingestion
- **Phase 3**: Data Cleaning & Standardization
- **Phase 4**: Feature Engineering
- **Phase 5**: Behavior & Profitability Analytics
- **Phase 6**: Statistical Significance Tests
- **Phase 7**: Visualization Suite
- **Phase 8**: Report Compilers
- **Phase 9**: Strategy Recommendation Engine
- **Phase 10**: Testnet Trading Bot
- **Phase 11**: Streamlit Dashboard Pages
- **Phase 12**: System Testing
- **Phase 13**: Deployment Setup
- **Phase 14**: System Documentation
