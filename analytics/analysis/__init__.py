"""Exposes public analysis modules and the master AnalyticsEngine."""

from analytics.analysis.analytics_engine import AnalyticsEngine
from analytics.analysis.coin_analysis import CoinAnalysis
from analytics.analysis.correlation_analysis import CorrelationAnalysis
from analytics.analysis.market_analysis import MarketAnalysis
from analytics.analysis.performance_analysis import PerformanceAnalysis
from analytics.analysis.risk_analysis import RiskAnalysis
from analytics.analysis.sentiment_analysis import SentimentAnalysis
from analytics.analysis.summary_generator import SummaryGenerator
from analytics.analysis.time_analysis import TimeAnalysis
from analytics.analysis.trader_analysis import TraderAnalysis

__all__ = [
    "AnalyticsEngine",
    "TraderAnalysis",
    "MarketAnalysis",
    "SentimentAnalysis",
    "CoinAnalysis",
    "PerformanceAnalysis",
    "RiskAnalysis",
    "TimeAnalysis",
    "CorrelationAnalysis",
    "SummaryGenerator",
]
