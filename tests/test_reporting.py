"""Unit tests for the Phase 8 Reporting Engine of PrimeTrade AI."""

from pathlib import Path
import tempfile
import pytest

from analytics.reports.markdown_compiler import MarkdownReportCompiler
from analytics.reports.html_compiler import HTMLReportCompiler
from analytics.reports.pdf_compiler import PDFReportCompiler, PrimeTradePDF
from analytics.reports.report_engine import ReportingEngine


@pytest.fixture
def mock_analytics_results():
    """Returns a mock analytics results dictionary conforming to the engine specs."""
    return {
        "performance_analysis": {
            "total_trades": 50,
            "gross_profit": 15000.0,
            "gross_loss": -5000.0,
            "net_profit": 10000.0,
            "win_rate": 0.65,
            "profit_factor": 3.0,
            "average_pnl": 200.0,
            "sharpe_ratio": 1.85,
            "total_fees": 120.0,
        },
        "risk_analysis": {
            "max_drawdown": 0.125,
            "pnl_volatility": 0.035,
            "value_at_risk_95": -450.0,
            "expected_shortfall_95": -620.0,
            "profit_loss_ratio": 1.6,
            "composite_risk_score": 4.5,
            "risk_classification": "Low Risk",
        },
        "sentiment_analysis": {
            "sentiment_regime_count": {"Total": 50},
            "pnl_by_sentiment_regime": {
                "Fear": {"count": 20, "sum": 4000.0, "mean": 200.0, "win_rate": 0.6},
                "Greed": {"count": 30, "sum": 6000.0, "mean": 200.0, "win_rate": 0.7},
            },
        },
        "coin_analysis": {
            "best_performing_coin": "BTCUSDT",
            "worst_performing_coin": "ETHUSDT",
            "coin_pnls": {
                "BTCUSDT": {"sum": 8000.0, "count": 30, "win_rate": 0.7, "volume": 12.5},
                "ETHUSDT": {"sum": 2000.0, "count": 20, "win_rate": 0.58, "volume": 45.0},
            },
        },
        "trader_analysis": {
            "top_10_traders": [
                {"trader_id": "TRD_001", "net_profit": 8000.0, "win_rate": 0.72, "profit_factor": 3.2, "total_trades": 35},
                {"trader_id": "TRD_002", "net_profit": 2000.0, "win_rate": 0.58, "profit_factor": 1.8, "total_trades": 15},
            ]
        },
        "time_analysis": {
            "best_trading_hour": 14,
            "worst_trading_hour": 4,
            "best_trading_day": "Wednesday",
            "worst_trading_day": "Saturday",
        },
        "intelligence_summary": {
            "recommendations": [
                "Increase leverage safety margin during extreme greed cycles.",
                "Favor BTCUSDT over ETHUSDT due to better historical win rate.",
            ],
            "warnings": [
                "High volatility detected in recent 24-hour cycle.",
            ],
        },
    }


@pytest.fixture
def mock_statistics_results():
    """Returns a mock statistics results dictionary conforming to the engine specs."""
    return {
        "descriptive": {
            "closed_pnl": {
                "mean": 200.0,
                "std": 150.0,
                "skew": 0.45,
                "kurtosis": 1.2,
                "min": -300.0,
                "50%": 180.0,
                "max": 600.0,
            },
            "market_volatility": {
                "mean": 0.025,
                "std": 0.005,
                "skew": 0.12,
                "kurtosis": -0.4,
                "min": 0.015,
                "50%": 0.024,
                "max": 0.038,
            },
        },
        "correlations": {
            "sentiment_vs_pnl": {
                "pearson": {"coefficient": 0.28, "p_value": 0.042, "significant": True},
                "spearman": {"coefficient": 0.25, "p_value": 0.065, "significant": False},
            }
        },
        "hypothesis_tests": {
            "t_test": {"stat": 2.15, "p_value": 0.038, "significant": True},
            "mann_whitney": {"stat": 185.0, "p_value": 0.048, "significant": True},
            "anova": {"stat": 3.42, "p_value": 0.025, "significant": True},
            "chi_square": {"stat": 4.12, "p_value": 0.12, "significant": False},
        },
        "distributions": {
            "closed_pnl": {
                "shapiro": {"stat": 0.96, "p_value": 0.18, "normal": True},
                "ks_1sample": {"stat": 0.12, "p_value": 0.22, "normal": True},
            }
        },
        "confidence_intervals": {
            "win_rate": {"estimate": 0.65, "lower_bound": 0.52, "upper_bound": 0.76, "type": "Wilson Score"},
            "average_pnl": {"estimate": 200.0, "lower_bound": 150.0, "upper_bound": 250.0, "type": "Student-t"},
        },
        "effect_sizes": {
            "cohens_d": {"value": 0.58, "interpretation": "Medium"},
            "eta_squared": {"value": 0.14, "interpretation": "Large"},
        },
        "observations": [
            "Normality checks suggest returns are roughly symmetric.",
            "Independent t-test indicates significant mean return differences.",
        ],
    }


def test_markdown_report_compiler(mock_analytics_results, mock_statistics_results):
    """Verifies that the Markdown compiler generates valid markdown structure and contains expected markers."""
    reports = MarkdownReportCompiler.compile_all(mock_analytics_results, mock_statistics_results)
    
    assert "executive_summary" in reports
    assert "technical_summary" in reports
    assert "business_report" in reports
    
    exec_summary = reports["executive_summary"]
    assert "# PrimeTrade AI - Executive Summary Report" in exec_summary
    assert "## Key Performance Indicators" in exec_summary
    assert "BTCUSDT" in exec_summary
    assert "Increase leverage safety margin" in exec_summary
    
    tech_summary = reports["technical_summary"]
    assert "# PrimeTrade AI - Technical & Statistical Report" in tech_summary
    assert "Pearson" in tech_summary
    assert "Independent T-Test" in tech_summary
    
    biz_report = reports["business_report"]
    assert "# PrimeTrade AI - Portfolio & Business Performance Report" in biz_report
    assert "TRD_001" in biz_report
    assert "Wednesday" in biz_report


def test_html_report_compiler(mock_analytics_results, mock_statistics_results):
    """Verifies that the HTML compiler generates full valid CSS-styled HTML page strings."""
    reports = HTMLReportCompiler.compile_all(mock_analytics_results, mock_statistics_results)
    
    assert "executive_summary" in reports
    assert "technical_summary" in reports
    assert "business_report" in reports
    
    exec_summary = reports["executive_summary"]
    assert "<!DOCTYPE html>" in exec_summary
    assert "<style>" in exec_summary
    assert "Executive Trading Summary" in exec_summary
    assert "cumulative_pnl.png" in exec_summary
    
    tech_summary = reports["technical_summary"]
    assert "Technical & Statistical Report" in tech_summary
    assert "Pearson" in tech_summary
    
    biz_report = reports["business_report"]
    assert "Portfolio & Business Performance" in biz_report


def test_pdf_report_compiler(mock_analytics_results, mock_statistics_results):
    """Verifies that the PDF compiler successfully instantiates and builds PrimeTradePDF objects."""
    reports = PDFReportCompiler.compile_all(mock_analytics_results, mock_statistics_results)
    
    assert "executive_summary" in reports
    assert "technical_summary" in reports
    assert "business_report" in reports
    
    for name, pdf in reports.items():
        assert isinstance(pdf, PrimeTradePDF)
        assert pdf.report_title is not None
        # Verify page count is initialized (cover page + content pages)
        assert pdf.page_no() > 0  # Page count should be positive after pages are compiled


def test_reporting_engine_workflow(mock_analytics_results, mock_statistics_results):
    """Verifies the complete ReportingEngine orchestrates outputs to disk in all three formats."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        engine = ReportingEngine(output_dir=tmp_path)
        
        results = engine.run_reporting(mock_analytics_results, mock_statistics_results)
        
        # Check dictionary structure
        assert "executive_summary" in results
        assert "technical_summary" in results
        assert "business_report" in results
        
        for name in ["executive_summary", "technical_summary", "business_report"]:
            assert "md" in results[name]
            assert "html" in results[name]
            assert "pdf" in results[name]
            
            # Check files exist on disk
            assert results[name]["md"].exists()
            assert results[name]["html"].exists()
            assert results[name]["pdf"].exists()
            
            # File size checks
            assert results[name]["md"].stat().st_size > 0
            assert results[name]["html"].stat().st_size > 0
            assert results[name]["pdf"].stat().st_size > 0
