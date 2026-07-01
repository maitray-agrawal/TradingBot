"""Intelligence and business summary generator module for PrimeTrade AI.

Uses statistical summaries across all sub-analysis results to generate
natural language executive summaries, insights, recommendations, and warnings.
"""

from typing import Any, Dict, List

from utils.logger import analytics_logger


class SummaryGenerator:
    """Generates text-based executive summaries and actionable trading recommendations."""

    @staticmethod
    def generate_summary(
        trader_results: Any,
        market_results: Any,
        sentiment_results: Any,
        coin_results: Any,
        performance_results: Any,
        risk_results: Any,
        time_results: Any,
        correlation_results: Any,
    ) -> Dict[str, Any]:
        """Orchestrates heuristic generation of textual insights.

        Args:
            trader_results: Result from TraderAnalysis.
            market_results: Result from MarketAnalysis.
            sentiment_results: Result from SentimentAnalysis.
            coin_results: Result from CoinAnalysis.
            performance_results: Result from PerformanceAnalysis.
            risk_results: Result from RiskAnalysis.
            time_results: Result from TimeAnalysis.
            correlation_results: Result from CorrelationAnalysis.

        Returns:
            Dict[str, Any]: Textual report summaries and lists of insights.
        """
        analytics_logger.info(
            "Generating intelligence summaries and recommendations..."
        )

        # 1. Executive Summary text
        tot_trades = performance_results.total_trades
        net_profit = performance_results.net_profit
        win_rate = performance_results.win_rate * 100.0
        profit_factor = performance_results.profit_factor
        traders_count = trader_results.total_traders

        if tot_trades == 0:
            exec_summary = "No trading data is available to analyze performance."
            insights = ["No trades logged in the dataset."]
            observations = []
            recommendations = ["Ingest transaction history before running analytics."]
            warnings = ["Analytics execution was triggered on an empty dataset."]
        else:
            exec_summary = (
                f"PrimeTrade AI has completed a comprehensive audit of {tot_trades} transactions "
                f"across {traders_count} accounts. The portfolio generated a net profit of "
                f"${net_profit:,.2f} with a trade-level win rate of {win_rate:.1f}% and a profit factor "
                f"of {profit_factor:.2f}. "
            )
            if net_profit > 0:
                exec_summary += "The overall portfolio exhibits positive expectancy and steady capital growth."
            else:
                exec_summary += "The system is currently unprofitable; optimization of execution limits is recommended."

            # 2. Top Insights (Positive observations)
            insights = []

            # Best trader
            if trader_results.top_10_traders:
                best_t = trader_results.top_10_traders[0]
                insights.append(
                    f"Trader account '{best_t['account_id']}' is the top performer, generating ${best_t['total_pnl']:,.2f} in net PnL."
                )

            # Best coin
            if coin_results.best_performing_coin and coin_results.coins:
                best_c = coin_results.coins[coin_results.best_performing_coin]
                insights.append(
                    f"Asset '{best_c['symbol']}' was the most profitable token, contributing ${best_c['total_pnl']:,.2f} to the net PnL."
                )

            if win_rate > 55.0:
                insights.append(
                    f"High overall win rate of {win_rate:.1f}% indicates a strong directional edge."
                )
            elif profit_factor > 1.5:
                insights.append(
                    f"Strong profit factor of {profit_factor:.2f} confirms profit sizes outpace loss sizes."
                )

            if not insights:
                insights.append(
                    "Historical trade outcomes are uniformly distributed with no single major driver."
                )

            # 3. Important Observations (Patterns)
            observations = []

            # Session observations
            if time_results.session_metrics:
                best_sess = max(
                    time_results.session_metrics.keys(),
                    key=lambda s: time_results.session_metrics[s]["average_pnl"],
                )
                best_sess_pnl = time_results.session_metrics[best_sess]["average_pnl"]
                observations.append(
                    f"Trading is most profitable during the {best_sess} session, yielding ${best_sess_pnl:,.2f} on average per trade."
                )

            # Best trading hour
            if time_results.best_trading_hour is not None:
                observations.append(
                    f"Hourly peak profitability is achieved at hour {time_results.best_trading_hour:02d}:00 UTC."
                )

            # Sentiment correlation
            sent_corr = correlation_results.sentiment_vs_pnl_pearson
            if abs(sent_corr) > 0.1:
                strength = "moderate" if abs(sent_corr) > 0.3 else "weak"
                direction = "positive" if sent_corr > 0 else "negative"
                observations.append(
                    f"There is a {strength} {direction} correlation ({sent_corr:.2f}) between the Fear & Greed index and trade PnL."
                )

            if not observations:
                observations.append(
                    "No strong periodic or external correlation patterns detected."
                )

            # 4. Business Recommendations
            recommendations = []

            # Sentiment based sizing
            if sentiment_results.regimes:
                worst_regime = sentiment_results.worst_performing_regime
                if worst_regime and worst_regime in sentiment_results.regimes:
                    worst_pnl = sentiment_results.regimes[worst_regime]["average_pnl"]
                    if worst_pnl < 0:
                        recommendations.append(
                            f"Reduce position sizing or pause execution during '{worst_regime}' market regimes, "
                            f"which historically generated average losses of ${worst_pnl:,.2f} per trade."
                        )

            # Volume HHI concentration recommendation
            hhi = market_results.volume_concentration_hhi
            if hhi > 3000:
                recommendations.append(
                    f"Trade volume is heavily concentrated in a few symbols (HHI: {hhi:.1f}). "
                    f"Diversify across additional active symbols to mitigate asset-specific risks."
                )
            else:
                recommendations.append(
                    "Maintain the current diversified allocation profile across traded assets."
                )

            # General risk control
            recommendations.append(
                "Optimize automated order limits for low-profitability sessions to reduce unnecessary fees."
            )

            # 5. Risk Warnings
            warnings = []
            max_dd = risk_results.max_drawdown
            warnings.append(
                f"Maximum historical peak-to-trough drawdown reached ${max_dd:,.2f}. Ensure stop-loss margins are calibrated."
            )

            var_val = risk_results.value_at_risk_95
            warnings.append(
                f"Historical 95% Value at Risk (VaR) is ${var_val:,.2f}. There is a 5% probability that a single trade loses more than this."
            )

            es_val = risk_results.expected_shortfall_95
            warnings.append(
                f"Expected Shortfall (Conditional VaR) is ${es_val:,.2f}, representing the average loss in the worst 5% of trade events."
            )

            # Concentration warnings
            worst_share = risk_results.top_3_loss_share * 100.0
            if worst_share > 50.0:
                warnings.append(
                    f"High loss concentration: the top 3 worst trades represent {worst_share:.1f}% of total gross losses."
                )

        return {
            "executive_summary": exec_summary,
            "top_insights": insights,
            "important_observations": observations,
            "business_recommendations": recommendations,
            "risk_warnings": warnings,
        }
