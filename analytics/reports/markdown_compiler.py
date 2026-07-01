"""Markdown report compilation module for PrimeTrade AI.

Formats analytical and statistical findings into publication-quality Markdown documents.
"""

from typing import Any, Dict


class MarkdownReportCompiler:
    """Compiles structured trading intelligence reports into Markdown format."""

    @classmethod
    def _format_pct(cls, val: Any) -> str:
        """Helper to format numeric value as percentage."""
        try:
            if val is None:
                return "N/A"
            return f"{float(val) * 100:.2f}%"
        except (ValueError, TypeError):
            return str(val)

    @classmethod
    def _format_currency(cls, val: Any) -> str:
        """Helper to format numeric value as currency."""
        try:
            if val is None:
                return "N/A"
            v = float(val)
            sign = "-" if v < 0 else ""
            return f"{sign}${abs(v):,.2f}"
        except (ValueError, TypeError):
            return str(val)

    @classmethod
    def _format_float(cls, val: Any, decimal_places: int = 4) -> str:
        """Helper to format float values."""
        try:
            if val is None:
                return "N/A"
            return f"{float(val):.{decimal_places}f}"
        except (ValueError, TypeError):
            return str(val)

    @classmethod
    def compile_executive_summary(
        cls, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> str:
        """Compiles the Executive Summary report.

        Focuses on high-level performance, overall sentiment regimes, and top-level recommendations.
        """
        perf = analytics_res.get("performance_analysis", {})
        risk = analytics_res.get("risk_analysis", {})
        sentiment = analytics_res.get("sentiment_analysis", {})
        coin = analytics_res.get("coin_analysis", {})
        intel = analytics_res.get("intelligence_summary", {})

        md = []
        md.append("# PrimeTrade AI - Executive Summary Report")
        md.append("")
        md.append("## Overview")
        md.append(
            "This report summarizes high-level portfolio performance, overall market sentiment regimes, "
            "and key performance highlights based on the ingested trader historical records."
        )
        md.append("")

        # Key Metrics Table
        md.append("## Key Performance Indicators")
        md.append("| Metric | Value | Description |")
        md.append("| :--- | :--- | :--- |")
        md.append(f"| **Total Trades** | {perf.get('total_trades', 0)} | Number of completed futures contracts |")
        md.append(f"| **Net Realized PnL** | {cls._format_currency(perf.get('net_profit', 0))} | Total net profit or loss |")
        md.append(f"| **Win Rate** | {cls._format_pct(perf.get('win_rate', 0))} | Proportion of profitable trades |")
        md.append(f"| **Profit Factor** | {cls._format_float(perf.get('profit_factor', 0), 2)} | Ratio of gross profits to gross losses |")
        md.append(f"| **Average Trade return** | {cls._format_currency(perf.get('average_pnl', 0))} | Mean profit/loss per trade |")
        md.append(f"| **Sharpe Ratio** | {cls._format_float(perf.get('sharpe_ratio', 0), 2)} | Risk-adjusted return metric |")
        md.append(f"| **Max Drawdown** | {cls._format_pct(risk.get('max_drawdown', 0))} | Maximum peak-to-trough decline |")
        md.append(f"| **Composite Risk Score** | {cls._format_float(risk.get('composite_risk_score', 0), 2)} / 10 | Standardized portfolio risk score |")
        md.append("")

        # Sentiment Analysis Summary
        md.append("## Sentiment Regime Analysis")
        md.append(
            f"The system has analyzed trading activity mapped against the **Bitcoin Fear & Greed Index** "
            f"across {sentiment.get('sentiment_regime_count', {}).get('Total', 0)} total historical points."
        )
        md.append("")

        # Regime-wise breakdown
        regimes = sentiment.get("pnl_by_sentiment_regime", {})
        if regimes:
            md.append("| Sentiment Regime | Trades | Net PnL | Win Rate | Average PnL |")
            md.append("| :--- | :---: | :---: | :---: | :---: |")
            for regime, details in regimes.items():
                if regime == "Unknown":
                    continue
                count = details.get("count", 0)
                pnl = details.get("sum", 0)
                mean_val = details.get("mean", 0)
                win_rate = details.get("win_rate", 0)
                md.append(
                    f"| **{regime}** | {count} | {cls._format_currency(pnl)} | {cls._format_pct(win_rate)} | {cls._format_currency(mean_val)} |"
                )
            md.append("")

        # Key Market Highlights
        best_symbol = coin.get("best_performing_coin", "N/A")
        worst_symbol = coin.get("worst_performing_coin", "N/A")
        best_pnl = coin.get("coin_pnls", {}).get(best_symbol, {}).get("sum", 0)
        worst_pnl = coin.get("coin_pnls", {}).get(worst_symbol, {}).get("sum", 0)

        md.append("## Market Highlights")
        md.append(f"- **Top Performing Asset**: `{best_symbol}` with a total realized PnL of **{cls._format_currency(best_pnl)}**.")
        md.append(f"- **Bottom Performing Asset**: `{worst_symbol}` with a total realized PnL of **{cls._format_currency(worst_pnl)}**.")
        md.append("")

        # Core Recommendations
        md.append("## Strategic Intelligence Recommendations")
        recommendations = intel.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                md.append(f"- **{rec}**")
        else:
            md.append("- No specific recommendations available based on current data.")
        md.append("")

        # Warnings
        warnings = intel.get("warnings", [])
        if warnings:
            md.append("### Critical System Warnings")
            for warn in warnings:
                md.append(f"> [!WARNING]\n> {warn}\n")
            md.append("")

        # Visualizations Links
        md.append("## Visual Charts Archive")
        md.append("Static and interactive charts have been saved to the outputs directory:")
        md.append("- **Cumulative Realized PnL**: [cumulative_pnl.png](../../outputs/charts/cumulative_pnl.png) / [cumulative_pnl.html](../../outputs/charts/cumulative_pnl.html)")
        md.append("- **Win/Loss Ratio**: [win_loss_pie.png](../../outputs/charts/win_loss_pie.png) / [win_loss_pie.html](../../outputs/charts/win_loss_pie.html)")
        md.append("- **Sentiment Regime Returns**: [sentiment_returns_violin.png](../../outputs/charts/sentiment_returns_violin.png) / [sentiment_returns_violin.html](../../outputs/charts/sentiment_returns_violin.html)")
        md.append("")
        md.append("---")
        md.append("*Generated by PrimeTrade AI Report Compiler.*")

        return "\n".join(md)

    @classmethod
    def compile_technical_summary(
        cls, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> str:
        """Compiles the Technical Summary report.

        Focuses on in-depth statistical testing, correlations, hypothesis validation, and distribution modeling.
        """
        descriptive = statistics_res.get("descriptive", {})
        corr = statistics_res.get("correlations", {})
        hypo = statistics_res.get("hypothesis_tests", {})
        dist = statistics_res.get("distributions", {})
        ci = statistics_res.get("confidence_intervals", {})
        effects = statistics_res.get("effect_sizes", {})
        obs = statistics_res.get("observations", [])

        md = []
        md.append("# PrimeTrade AI - Technical & Statistical Report")
        md.append("")
        md.append("## Mathematical Scope")
        md.append(
            "This document compiles rigorous statistical parameters validating whether "
            "market sentiment features correlate with trader performance metrics. "
            "All findings are validated using classical hypothesis testing and normality checks."
        )
        md.append("")

        # Descriptive Statistics
        md.append("## Descriptive Statistics (PnL and Volatility)")
        pnl_stats = descriptive.get("closed_pnl", {})
        vol_stats = descriptive.get("market_volatility", {})
        md.append("| Metric | Closed PnL | Market Volatility |")
        md.append("| :--- | :---: | :---: |")
        md.append(f"| **Mean** | {cls._format_currency(pnl_stats.get('mean'))} | {cls._format_float(vol_stats.get('mean'))} |")
        md.append(f"| **Standard Deviation** | {cls._format_float(pnl_stats.get('std'))} | {cls._format_float(vol_stats.get('std'))} |")
        md.append(f"| **Skewness** | {cls._format_float(pnl_stats.get('skew'))} | {cls._format_float(vol_stats.get('skew'))} |")
        md.append(f"| **Kurtosis** | {cls._format_float(pnl_stats.get('kurtosis'))} | {cls._format_float(vol_stats.get('kurtosis'))} |")
        md.append(f"| **Min Value** | {cls._format_currency(pnl_stats.get('min'))} | {cls._format_float(vol_stats.get('min'))} |")
        md.append(f"| **Median (50%)** | {cls._format_currency(pnl_stats.get('50%'))} | {cls._format_float(vol_stats.get('50%'))} |")
        md.append(f"| **Max Value** | {cls._format_currency(pnl_stats.get('max'))} | {cls._format_float(vol_stats.get('max'))} |")
        md.append("")

        # Correlation Analysis Table
        md.append("## Sentiment Correlation Parameters")
        md.append("| Correlation Variable | Pearson Coeff | Pearson p-val | Spearman Coeff | Spearman p-val | Significant? |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
        for key, value in corr.items():
            if isinstance(value, dict) and "pearson" in value and "spearman" in value:
                p_coef = value["pearson"].get("coefficient")
                p_pval = value["pearson"].get("p_value")
                s_coef = value["spearman"].get("coefficient")
                s_pval = value["spearman"].get("p_value")
                sig = "YES" if value["pearson"].get("significant") or value["spearman"].get("significant") else "NO"
                var_name = key.replace("_", " ").title()
                md.append(
                    f"| {var_name} | {cls._format_float(p_coef)} | {cls._format_float(p_pval)} | {cls._format_float(s_coef)} | {cls._format_float(s_pval)} | **{sig}** |"
                )
        md.append("")

        # Hypothesis Testing Table
        md.append("## Hypothesis Validation Suite")
        md.append("| Test Method | Statistic | p-value | Significant? | Details / Interpretation |")
        md.append("| :--- | :---: | :---: | :---: | :--- |")

        # Independent T-Test
        t_test = hypo.get("t_test", {})
        if t_test:
            sig = "YES" if t_test.get("significant") else "NO"
            md.append(
                f"| **Independent T-Test** | {cls._format_float(t_test.get('stat'))} | {cls._format_float(t_test.get('p_value'))} | **{sig}** | Compares mean returns in Fear vs. Greed regimes |"
            )

        # Mann-Whitney U
        mwu = hypo.get("mann_whitney", {})
        if mwu:
            sig = "YES" if mwu.get("significant") else "NO"
            md.append(
                f"| **Mann-Whitney U** | {cls._format_float(mwu.get('stat'))} | {cls._format_float(mwu.get('p_value'))} | **{sig}** | Compares return distribution ranks in Fear vs. Greed |"
            )

        # ANOVA
        anova = hypo.get("anova", {})
        if anova:
            sig = "YES" if anova.get("significant") else "NO"
            md.append(
                f"| **One-Way ANOVA** | {cls._format_float(anova.get('stat'))} | {cls._format_float(anova.get('p_value'))} | **{sig}** | Compares mean returns across all sentiment classes |"
            )

        # Chi-Square
        chi = hypo.get("chi_square", {})
        if chi:
            sig = "YES" if chi.get("significant") else "NO"
            md.append(
                f"| **Chi-Square Association** | {cls._format_float(chi.get('stat'))} | {cls._format_float(chi.get('p_value'))} | **{sig}** | Checks relation between Trading Side and Sentiment |"
            )
        md.append("")

        # Distribution Normality Table
        md.append("## Distribution Normality Parameters")
        md.append("| Target Column | Shapiro stat | Shapiro p-val | Normal? | Kolmogorov-Smirnov p-val | Normal? |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
        for col, tests in dist.items():
            if isinstance(tests, dict):
                shapiro = tests.get("shapiro", {})
                ks = tests.get("kolmogorov_smirnov", {})
                s_stat = shapiro.get("stat")
                s_p = shapiro.get("p_value")
                s_norm = "YES" if shapiro.get("normal") else "NO"
                k_p = ks.get("p_value")
                k_norm = "YES" if ks.get("normal") else "NO"
                md.append(
                    f"| `{col}` | {cls._format_float(s_stat)} | {cls._format_float(s_p)} | {s_norm} | {cls._format_float(k_p)} | {k_norm} |"
                )
        md.append("")

        # Confidence Intervals and Effect Sizes
        md.append("## Confidence Intervals & Effect Sizes")

        # Confidence Intervals
        md.append("### Parameter Confidence Ranges (95% Confidence)")
        md.append("| Parameter | Sample Mean/Rate | Lower Bound | Upper Bound | Interval Type |")
        md.append("| :--- | :---: | :---: | :---: | :--- |")
        for param, details in ci.items():
            if isinstance(details, dict):
                name = param.replace("_", " ").title()
                est = details.get("estimate")
                low = details.get("lower_bound")
                up = details.get("upper_bound")
                ci_type = details.get("type", "Student-t")
                if "win_rate" in param:
                    md.append(f"| {name} | {cls._format_pct(est)} | {cls._format_pct(low)} | {cls._format_pct(up)} | Wilson Score |")
                else:
                    md.append(f"| {name} | {cls._format_currency(est)} | {cls._format_currency(low)} | {cls._format_currency(up)} | {ci_type} |")
        md.append("")

        # Effect Sizes
        md.append("### Effect Size Estimates")
        cohen = effects.get("cohens_d", {})
        eta = effects.get("eta_squared", {})
        md.append(f"- **Cohen's d (Fear vs Greed Returns)**: {cls._format_float(cohen.get('value'))} ({cohen.get('interpretation', 'N/A')})")
        md.append(f"- **Eta-squared (Sentiment Class Variance)**: {cls._format_float(eta.get('value'))} ({eta.get('interpretation', 'N/A')})")
        md.append("")

        # Stats observations
        md.append("## Rigorous Mathematical Observations")
        if obs:
            for ob in obs:
                md.append(f"- **{ob}**")
        else:
            md.append("- No statistical observation records were generated.")
        md.append("")

        # Visualizations Links
        md.append("## Visual Charts Archive")
        md.append("Static and interactive charts verifying statistics:")
        md.append("- **Return Distribution Histogram**: [pnl_distribution.png](../../outputs/charts/pnl_distribution.png) / [pnl_distribution.html](../../outputs/charts/pnl_distribution.html)")
        md.append("- **Fear/Greed Correlation Scatter**: [sentiment_correlation_scatter.png](../../outputs/charts/sentiment_correlation_scatter.png) / [sentiment_correlation_scatter.html](../../outputs/charts/sentiment_correlation_scatter.html)")
        md.append("- **Correlation Heatmap**: [correlation_heatmap.png](../../outputs/charts/correlation_heatmap.png) / [correlation_heatmap.html](../../outputs/charts/correlation_heatmap.html)")
        md.append("")
        md.append("---")
        md.append("*Generated by PrimeTrade AI Report Compiler.*")

        return "\n".join(md)

    @classmethod
    def compile_business_report(
        cls, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> str:
        """Compiles the Business Report.

        Focuses on symbol profitability leaderboards, trader performance, risk profile summaries,
        time-based activity, and business recommendations.
        """
        perf = analytics_res.get("performance_analysis", {})
        risk = analytics_res.get("risk_analysis", {})
        traders = analytics_res.get("trader_analysis", {})
        coin = analytics_res.get("coin_analysis", {})
        time_analysis = analytics_res.get("time_analysis", {})
        intel = analytics_res.get("intelligence_summary", {})

        md = []
        md.append("# PrimeTrade AI - Portfolio & Business Performance Report")
        md.append("")
        md.append("## Portfolio Performance Overview")
        md.append(
            "This report delivers structured business analytics regarding asset performance, "
            "trader leadership rankings, system-wide risk exposures, and temporal trade distributions."
        )
        md.append("")

        # Financial Performance Summary
        md.append("## Portfolio Profitability Summary")
        md.append("| Performance Metric | Value | Business Definition |")
        md.append("| :--- | :--- | :--- |")
        md.append(f"| **Gross Realized Profit** | {cls._format_currency(perf.get('gross_profit', 0))} | Sum of all profitable futures trades |")
        md.append(f"| **Gross Realized Loss** | {cls._format_currency(perf.get('gross_loss', 0))} | Sum of all losing futures trades |")
        md.append(f"| **Net Portfolio Return** | {cls._format_currency(perf.get('net_profit', 0))} | Combined net profitability |")
        md.append(f"| **Win Ratio** | {cls._format_pct(perf.get('win_rate', 0))} | Percentage of winning contracts |")
        md.append(f"| **Profit Factor** | {cls._format_float(perf.get('profit_factor', 0), 2)} | Profit to Loss ratio |")
        md.append(f"| **Total Brokerage Fees** | {cls._format_currency(perf.get('total_fees', 0))} | Realized Binance Futures trading fees |")
        md.append("")

        # Asset Profitability Leaderboard
        md.append("## Asset Profitability Leaderboard")
        coin_pnls = coin.get("coin_pnls", {})
        if coin_pnls:
            md.append("| Symbol | Net PnL | Trades | Win Rate | Volume (Lots/Contracts) |")
            md.append("| :---: | :---: | :---: | :---: | :---: |")
            # Sort by net PnL descending
            sorted_coins = sorted(
                coin_pnls.items(), key=lambda item: item[1].get("sum", 0), reverse=True
            )
            for symbol, details in sorted_coins:
                md.append(
                    f"| **{symbol}** | {cls._format_currency(details.get('sum', 0))} | {details.get('count', 0)} | {cls._format_pct(details.get('win_rate', 0))} | {cls._format_float(details.get('volume', 0), 2)} |"
                )
            md.append("")

        # Trader Performance Leaderboard
        md.append("## Trader Performance Rankings")
        top_traders = traders.get("top_10_traders", [])
        if top_traders:
            md.append("| Trader Account / Rank | Net Realized PnL | Win Rate | Profit Factor | Trades |")
            md.append("| :--- | :---: | :---: | :---: | :---: |")
            for idx, trader in enumerate(top_traders, 1):
                md.append(
                    f"| **Rank #{idx}**: `{trader.get('trader_id')}` | {cls._format_currency(trader.get('net_profit'))} | {cls._format_pct(trader.get('win_rate'))} | {cls._format_float(trader.get('profit_factor'), 2)} | {trader.get('total_trades')} |"
                )
            md.append("")

        # Risk Exposures
        md.append("## System Risk Profile Summary")
        md.append("| Risk Parameter | Value | Business Description |")
        md.append("| :--- | :--- | :--- |")
        md.append(f"| **Portfolio Volatility (Realized)** | {cls._format_float(risk.get('pnl_volatility', 0), 4)} | Trade-by-trade standard deviation |")
        md.append(f"| **Max Realized Drawdown** | {cls._format_pct(risk.get('max_drawdown', 0))} | Peak-to-trough drop in realized PnL |")
        md.append(f"| **Value at Risk (95% VaR)** | {cls._format_currency(risk.get('value_at_risk_95', 0))} | Potential loss at 95% confidence level |")
        md.append(f"| **Expected Shortfall (95% ES)** | {cls._format_currency(risk.get('expected_shortfall_95', 0))} | Average loss in the worst 5% of cases |")
        md.append(f"| **Profit-Loss Ratio** | {cls._format_float(risk.get('profit_loss_ratio', 0), 2)} | Average profit divided by average loss |")
        md.append(f"| **Composite Risk Classification** | **{risk.get('risk_classification', 'Unknown')}** | Overall portfolio risk state |")
        md.append("")

        # Time analysis summary
        md.append("## Hourly Trading Activity Breakdown")
        best_hour = time_analysis.get("best_trading_hour", "N/A")
        worst_hour = time_analysis.get("worst_trading_hour", "N/A")
        best_day = time_analysis.get("best_trading_day", "N/A")
        worst_day = time_analysis.get("worst_trading_day", "N/A")

        md.append(f"- **Most Profitable Hour**: `{best_hour}:00 UTC` session.")
        md.append(f"- **Least Profitable Hour**: `{worst_hour}:00 UTC` session.")
        md.append(f"- **Most Profitable Day of Week**: `{best_day}`.")
        md.append(f"- **Least Profitable Day of Week**: `{worst_day}`.")
        md.append("")

        # Dynamic Recommendations
        md.append("## Strategic Business Recommendations")
        recommendations = intel.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                md.append(f"- **{rec}**")
        else:
            md.append("- No specific recommendations available based on current data.")
        md.append("")

        # Visualizations Links
        md.append("## Visual Charts Archive")
        md.append("Static and interactive charts illustrating business rankings:")
        md.append("- **Asset Rankings**: [coin_leaderboard.png](../../outputs/charts/coin_leaderboard.png) / [coin_leaderboard.html](../../outputs/charts/coin_leaderboard.html)")
        md.append("- **Hourly Session Activity Heatmap**: [hourly_heatmap.png](../../outputs/charts/hourly_heatmap.png) / [hourly_heatmap.html](../../outputs/charts/hourly_heatmap.html)")
        md.append("- **Daily PnL**: [daily_pnl.png](../../outputs/charts/daily_pnl.png) / [daily_pnl.html](../../outputs/charts/daily_pnl.html)")
        md.append("")
        md.append("---")
        md.append("*Generated by PrimeTrade AI Report Compiler.*")

        return "\n".join(md)

    @classmethod
    def compile_all(
        cls, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> Dict[str, str]:
        """Compiles all three reports and returns them in a dictionary."""
        return {
            "executive_summary": cls.compile_executive_summary(
                analytics_res, statistics_res
            ),
            "technical_summary": cls.compile_technical_summary(
                analytics_res, statistics_res
            ),
            "business_report": cls.compile_business_report(
                analytics_res, statistics_res
            ),
        }
