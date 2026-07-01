"""HTML report compilation module for PrimeTrade AI.

Compiles analytical and statistical findings into stunning responsive HTML documents.
"""

from datetime import datetime
from typing import Any, Dict


class HTMLReportCompiler:
    """Compiles structured trading intelligence reports into CSS-styled HTML format."""

    # Curated Premium Stylesheet
    CSS_STYLES = """
    :root {
        --bg-color: #0b0f19;
        --card-bg: #131a2c;
        --card-border: rgba(255, 255, 255, 0.05);
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --accent-primary: #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-green: #22c55e;
        --accent-red: #ef4444;
        --accent-warning: #f59e0b;
        --accent-blue-bg: rgba(59, 130, 246, 0.1);
        --accent-green-bg: rgba(34, 197, 94, 0.1);
        --accent-red-bg: rgba(239, 68, 68, 0.1);
        --accent-warning-bg: rgba(245, 158, 11, 0.1);
    }

    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    body {
        background-color: var(--bg-color);
        color: var(--text-main);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        padding: 40px 20px;
        min-height: 100vh;
        line-height: 1.6;
    }

    .container {
        max-width: 1000px;
        margin: 0 auto;
    }

    header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
        padding-bottom: 24px;
        border-bottom: 1px solid var(--card-border);
    }

    h1 {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }

    .report-type {
        font-size: 14px;
        text-transform: uppercase;
        color: var(--accent-primary);
        letter-spacing: 0.1em;
        font-weight: 700;
    }

    .subtitle {
        color: var(--text-muted);
        font-size: 15px;
    }

    .timestamp {
        text-align: right;
        font-size: 13px;
        color: var(--text-muted);
    }

    h2 {
        font-size: 22px;
        font-weight: 600;
        margin: 35px 0 20px 0;
        border-left: 4px solid var(--accent-primary);
        padding-left: 12px;
        letter-spacing: -0.01em;
    }

    h3 {
        font-size: 18px;
        font-weight: 600;
        margin: 25px 0 15px 0;
        color: var(--text-main);
    }

    p {
        color: var(--text-muted);
        margin-bottom: 20px;
    }

    /* Grid layout */
    .grid-2 {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
        gap: 24px;
        margin-bottom: 30px;
    }

    /* Cards */
    .card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
    }

    /* Stats Grid */
    .stats-ribbon {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 35px;
    }

    .stat-box {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .stat-label {
        font-size: 12px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }

    .stat-value {
        font-size: 24px;
        font-weight: 700;
    }

    .text-profit { color: var(--accent-green); }
    .text-loss { color: var(--accent-red); }
    .text-neutral { color: var(--text-main); }

    /* Tables styling */
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 25px;
        font-size: 14px;
    }

    th, td {
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid var(--card-border);
    }

    th {
        background-color: rgba(255, 255, 255, 0.02);
        color: var(--text-main);
        font-weight: 600;
    }

    td {
        color: var(--text-muted);
    }

    tr:hover td {
        color: var(--text-main);
        background-color: rgba(255, 255, 255, 0.01);
    }

    /* Recommendations & Alerts */
    .recommendations-list {
        list-style-type: none;
    }

    .recommendations-list li {
        position: relative;
        padding-left: 28px;
        margin-bottom: 12px;
        color: var(--text-muted);
    }

    .recommendations-list li::before {
        content: "→";
        position: absolute;
        left: 0;
        color: var(--accent-primary);
        font-weight: bold;
    }

    .alert {
        background-color: var(--accent-blue-bg);
        border-left: 4px solid var(--accent-primary);
        padding: 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 20px;
        color: var(--text-muted);
    }

    .alert-warning {
        background-color: var(--accent-warning-bg);
        border-left: 4px solid var(--accent-warning);
        color: #fef3c7;
    }

    .alert-warning strong {
        color: var(--accent-warning);
    }

    /* Embedded Charts */
    .chart-container {
        margin-top: 24px;
        background: rgba(255, 255, 255, 0.01);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }

    .chart-img {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .chart-caption {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 8px;
    }

    footer {
        text-align: center;
        padding-top: 40px;
        margin-top: 50px;
        border-top: 1px solid var(--card-border);
        font-size: 12px;
        color: var(--text-muted);
    }
    """

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
    def _get_html_wrapper(
        cls, title: str, subtitle: str, report_type: str, body_content: str
    ) -> str:
        """Helper to wrap body contents with full HTML boilerplate and styling."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrimeTrade AI - {title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        {cls.CSS_STYLES}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <div class="report-type">{report_type}</div>
                <h1>{title}</h1>
                <div class="subtitle">{subtitle}</div>
            </div>
            <div class="timestamp">
                <div>Generated At</div>
                <div style="font-weight: 600; color: var(--text-main); margin-top: 4px;">{timestamp}</div>
            </div>
        </header>

        {body_content}

        <footer>
            <p>PrimeTrade AI Reporting Engine. All rights reserved. Trade responsibly.</p>
        </footer>
    </div>
</body>
</html>
"""

    @classmethod
    def compile_executive_summary(
        cls, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> str:
        """Compiles the HTML Executive Summary."""
        perf = analytics_res.get("performance_analysis", {})
        risk = analytics_res.get("risk_analysis", {})
        sentiment = analytics_res.get("sentiment_analysis", {})
        coin = analytics_res.get("coin_analysis", {})
        intel = analytics_res.get("intelligence_summary", {})

        net_profit = perf.get("net_profit", 0)
        net_profit_class = "text-profit" if net_profit >= 0 else "text-loss"

        # Generate summary stats cards
        stats_ribbon = f"""
        <section class="stats-ribbon">
            <div class="stat-box">
                <div class="stat-label">Total Trades</div>
                <div class="stat-value">{perf.get('total_trades', 0)}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Net PnL</div>
                <div class="stat-value {net_profit_class}">{cls._format_currency(net_profit)}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value">{cls._format_pct(perf.get('win_rate', 0))}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Profit Factor</div>
                <div class="stat-value">{cls._format_float(perf.get('profit_factor', 0), 2)}</div>
            </div>
        </section>
        """

        # Generate regime-wise breakdown table
        regime_rows = []
        regimes = sentiment.get("pnl_by_sentiment_regime", {})
        if regimes:
            for regime, details in regimes.items():
                if regime == "Unknown":
                    continue
                count = details.get("count", 0)
                pnl = details.get("sum", 0)
                mean_val = details.get("mean", 0)
                win_rate = details.get("win_rate", 0)
                row_class = "text-profit" if pnl >= 0 else "text-loss"
                regime_rows.append(
                    f"""
                    <tr>
                        <td><strong>{regime}</strong></td>
                        <td>{count}</td>
                        <td class="{row_class}">{cls._format_currency(pnl)}</td>
                        <td>{cls._format_pct(win_rate)}</td>
                        <td>{cls._format_currency(mean_val)}</td>
                    </tr>
                    """
                )
        regime_table = "".join(regime_rows)

        # Assets
        best_symbol = coin.get("best_performing_coin", "N/A")
        worst_symbol = coin.get("worst_performing_coin", "N/A")
        best_pnl = coin.get("coin_pnls", {}).get(best_symbol, {}).get("sum", 0)
        worst_pnl = coin.get("coin_pnls", {}).get(worst_symbol, {}).get("sum", 0)

        # Recommendations list
        recs = []
        for rec in intel.get("recommendations", []):
            recs.append(f"<li>{rec}</li>")
        recs_html = "".join(recs)

        # Warnings list
        warns = []
        for warn in intel.get("warnings", []):
            warns.append(
                f"""
                <div class="alert alert-warning">
                    <strong>SYSTEM WARNING:</strong> {warn}
                </div>
                """
            )
        warns_html = "".join(warns)

        body = f"""
        {stats_ribbon}

        {warns_html}

        <div class="grid-2">
            <div class="card">
                <h2>Sentiment Regime Breakdown</h2>
                <p>Performance of executed trades mapped to daily Bitcoin Fear & Greed sentiment index categories.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Regime</th>
                            <th>Trades</th>
                            <th>Net PnL</th>
                            <th>Win Rate</th>
                            <th>Avg PnL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {regime_table}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>Strategic Intelligence Recommendations</h2>
                <p>Rule-based behavioral optimization guidelines based on your historical trades.</p>
                <ul class="recommendations-list">
                    {recs_html if recs_html else "<li>No recommendations available based on current data.</li>"}
                </ul>
            </div>
        </div>

        <div class="card">
            <h2>Market Highlights & Volatility Overview</h2>
            <p>Highlights of assets traded and their general performance.</p>
            <table>
                <thead>
                    <tr>
                        <th>Asset Rank</th>
                        <th>Symbol</th>
                        <th>Realized Profit/Loss</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Top Asset</strong></td>
                        <td><code>{best_symbol}</code></td>
                        <td class="text-profit">{cls._format_currency(best_pnl)}</td>
                        <td><span class="text-profit" style="font-weight:600;">Outperforming</span></td>
                    </tr>
                    <tr>
                        <td><strong>Bottom Asset</strong></td>
                        <td><code>{worst_symbol}</code></td>
                        <td class="text-loss">{cls._format_currency(worst_pnl)}</td>
                        <td><span class="text-loss" style="font-weight:600;">Underperforming</span></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>Cumulative Realized Returns</h2>
                <div class="chart-container">
                    <img src="../../outputs/charts/cumulative_pnl.png" class="chart-img" alt="Cumulative Realized PnL">
                    <div class="chart-caption">Figure 1.1: Cumulative realized profit/loss curve over time.</div>
                </div>
            </div>

            <div class="card">
                <h2>Win / Loss Ratio Distribution</h2>
                <div class="chart-container">
                    <img src="../../outputs/charts/win_loss_pie.png" class="chart-img" alt="Win/Loss Ratio">
                    <div class="chart-caption">Figure 1.2: Proportion of winning vs. losing futures trades.</div>
                </div>
            </div>
        </div>
        """

        return cls._get_html_wrapper(
            title="Executive Trading Summary",
            subtitle="High-level performance analysis, sentiment regimes, and core optimizations.",
            report_type="Executive Report",
            body_content=body,
        )

    @classmethod
    def compile_technical_summary(
        cls, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> str:
        """Compiles the HTML Technical Summary."""
        descriptive = statistics_res.get("descriptive", {})
        corr = statistics_res.get("correlations", {})
        hypo = statistics_res.get("hypothesis_tests", {})
        dist = statistics_res.get("distributions", {})
        ci = statistics_res.get("confidence_intervals", {})
        effects = statistics_res.get("effect_sizes", {})
        obs = statistics_res.get("observations", [])

        # Stats Descriptive Table
        pnl_stats = descriptive.get("closed_pnl", {})
        vol_stats = descriptive.get("market_volatility", {})

        # Correlation Table
        corr_rows = []
        for key, value in corr.items():
            if isinstance(value, dict) and "pearson" in value and "spearman" in value:
                p_coef = value["pearson"].get("coefficient")
                p_pval = value["pearson"].get("p_value")
                s_coef = value["spearman"].get("coefficient")
                s_pval = value["spearman"].get("p_value")
                sig = "YES" if value["pearson"].get("significant") or value["spearman"].get("significant") else "NO"
                var_name = key.replace("_", " ").title()
                corr_rows.append(
                    f"""
                    <tr>
                        <td><strong>{var_name}</strong></td>
                        <td>{cls._format_float(p_coef)}</td>
                        <td>{cls._format_float(p_pval)}</td>
                        <td>{cls._format_float(s_coef)}</td>
                        <td>{cls._format_float(s_pval)}</td>
                        <td style="font-weight:600; color: {'var(--accent-green)' if sig == 'YES' else 'var(--text-muted)'}">{sig}</td>
                    </tr>
                    """
                )
        corr_table = "".join(corr_rows)

        # Hypothesis Tests rows
        hypo_rows = []
        tests_list = [
            ("t_test", "Independent T-Test", "Compares mean returns in Fear vs. Greed regimes"),
            ("mann_whitney", "Mann-Whitney U", "Compares return distribution ranks in Fear vs. Greed"),
            ("anova", "One-Way ANOVA", "Compares mean returns across all sentiment classes"),
            ("chi_square", "Chi-Square Association", "Checks relation between Trading Side and Sentiment"),
        ]
        for key, name, desc in tests_list:
            t = hypo.get(key, {})
            if t:
                sig = "YES" if t.get("significant") else "NO"
                hypo_rows.append(
                    f"""
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>{cls._format_float(t.get('stat'))}</td>
                        <td>{cls._format_float(t.get('p_value'))}</td>
                        <td style="font-weight:600; color: {'var(--accent-green)' if sig == 'YES' else 'var(--text-muted)'}">{sig}</td>
                        <td>{desc}</td>
                    </tr>
                    """
                )
        hypo_table = "".join(hypo_rows)

        # Normality rows
        norm_rows = []
        for col, tests in dist.items():
            if isinstance(tests, dict):
                shapiro = tests.get("shapiro", {})
                ks = tests.get("kolmogorov_smirnov", {})
                s_stat = shapiro.get("stat")
                s_p = shapiro.get("p_value")
                s_norm = "YES" if shapiro.get("normal") else "NO"
                k_p = ks.get("p_value")
                k_norm = "YES" if ks.get("normal") else "NO"
                norm_rows.append(
                    f"""
                    <tr>
                        <td><code>{col}</code></td>
                        <td>{cls._format_float(s_stat)}</td>
                        <td>{cls._format_float(s_p)}</td>
                        <td>{s_norm}</td>
                        <td>{cls._format_float(k_p)}</td>
                        <td>{k_norm}</td>
                    </tr>
                    """
                )
        norm_table = "".join(norm_rows)

        # CI rows
        ci_rows = []
        for param, details in ci.items():
            if isinstance(details, dict):
                name = param.replace("_", " ").title()
                est = details.get("estimate")
                low = details.get("lower_bound")
                up = details.get("upper_bound")
                ci_type = details.get("type", "Student-t")
                if "win_rate" in param:
                    ci_rows.append(
                        f"""
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{cls._format_pct(est)}</td>
                            <td>{cls._format_pct(low)}</td>
                            <td>{cls._format_pct(up)}</td>
                            <td>Wilson Score</td>
                        </tr>
                        """
                    )
                else:
                    ci_rows.append(
                        f"""
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{cls._format_currency(est)}</td>
                            <td>{cls._format_currency(low)}</td>
                            <td>{cls._format_currency(up)}</td>
                            <td>{ci_type}</td>
                        </tr>
                        """
                    )
        ci_table = "".join(ci_rows)

        # Observations
        obs_list = []
        for ob in obs:
            obs_list.append(f"<li>{ob}</li>")
        obs_html = "".join(obs_list)

        cohen = effects.get("cohens_d", {})
        eta = effects.get("eta_squared", {})

        body = f"""
        <div class="card">
            <h2>Descriptive Parameter Summary</h2>
            <p>Summary of central tendency, dispersion, and shape of PnL and volatility distributions.</p>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Closed Realized PnL</th>
                        <th>Market Volatility</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td><strong>Mean</strong></td><td>{cls._format_currency(pnl_stats.get('mean'))}</td><td>{cls._format_float(vol_stats.get('mean'))}</td></tr>
                    <tr><td><strong>Standard Deviation</strong></td><td>{cls._format_float(pnl_stats.get('std'))}</td><td>{cls._format_float(vol_stats.get('std'))}</td></tr>
                    <tr><td><strong>Skewness</strong></td><td>{cls._format_float(pnl_stats.get('skew'))}</td><td>{cls._format_float(vol_stats.get('skew'))}</td></tr>
                    <tr><td><strong>Kurtosis</strong></td><td>{cls._format_float(pnl_stats.get('kurtosis'))}</td><td>{cls._format_float(vol_stats.get('kurtosis'))}</td></tr>
                    <tr><td><strong>Minimum Value</strong></td><td>{cls._format_currency(pnl_stats.get('min'))}</td><td>{cls._format_float(vol_stats.get('min'))}</td></tr>
                    <tr><td><strong>Median (50%)</strong></td><td>{cls._format_currency(pnl_stats.get('50%'))}</td><td>{cls._format_float(vol_stats.get('50%'))}</td></tr>
                    <tr><td><strong>Maximum Value</strong></td><td>{cls._format_currency(pnl_stats.get('max'))}</td><td>{cls._format_float(vol_stats.get('max'))}</td></tr>
                </tbody>
            </table>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>Sentiment Correlation Parameters</h2>
                <p>Pearson and Spearman coefficients correlating Fear & Greed values against closed PnLs.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Variable Pair</th>
                            <th>Pearson r</th>
                            <th>Pearson p-val</th>
                            <th>Spearman rho</th>
                            <th>Spearman p-val</th>
                            <th>Sig?</th>
                        </tr>
                    </thead>
                    <tbody>
                        {corr_table}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>Hypothesis Testing Validation Suite</h2>
                <p>Determines statistical significance of returns and side mappings across regimes.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Method</th>
                            <th>Stat</th>
                            <th>p-value</th>
                            <th>Sig?</th>
                            <th>Purpose</th>
                        </tr>
                    </thead>
                    <tbody>
                        {hypo_table}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>Distribution Normality Checks</h2>
                <p>Verifies whether closed PnL and market volatility correspond to Gaussian normal distributions.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Target Column</th>
                            <th>Shapiro W</th>
                            <th>Shapiro p-val</th>
                            <th>Normal?</th>
                            <th>KS p-val</th>
                            <th>Normal?</th>
                        </tr>
                    </thead>
                    <tbody>
                        {norm_table}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>95% Parameter Confidence Intervals</h2>
                <p>Statistically estimated ranges for sample mean parameters.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Sample Estimate</th>
                            <th>CI Lower Bound</th>
                            <th>CI Upper Bound</th>
                            <th>Interval Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ci_table}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>Statistical Effect Sizes & Observations</h2>
            <div style="margin-bottom: 20px;">
                <p><strong>Cohen's d (Fear vs Greed Returns)</strong>: {cls._format_float(cohen.get('value'))} &mdash; <span class="text-neutral" style="font-weight:600;">{cohen.get('interpretation', 'N/A')}</span></p>
                <p><strong>Eta-squared (ANOVA sentiment variance)</strong>: {cls._format_float(eta.get('value'))} &mdash; <span class="text-neutral" style="font-weight:600;">{eta.get('interpretation', 'N/A')}</span></p>
            </div>
            <h3>Rigorous Mathematical Observations</h3>
            <ul class="recommendations-list">
                {obs_html if obs_html else "<li>No observations generated.</li>"}
            </ul>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>Return Normality Fit</h2>
                <div class="chart-container">
                    <img src="../../outputs/charts/pnl_distribution.png" class="chart-img" alt="Return Distribution Fit">
                    <div class="chart-caption">Figure 2.1: Closed PnL distribution fit overlaid with a kernel density estimate.</div>
                </div>
            </div>

            <div class="card">
                <h2>Sentiment vs. Realized Return Correlation</h2>
                <div class="chart-container">
                    <img src="../../outputs/charts/sentiment_correlation_scatter.png" class="chart-img" alt="Sentiment Scatter Fit">
                    <div class="chart-caption">Figure 2.2: Daily Fear & Greed index versus closed realized trade returns with regression trend line.</div>
                </div>
            </div>
        </div>
        """

        return cls._get_html_wrapper(
            title="Technical & Statistical Report",
            subtitle="Mathematical verification of sentiment features, correlations, and hypothesis tests.",
            report_type="Technical Report",
            body_content=body,
        )

    @classmethod
    def compile_business_report(
        cls, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> str:
        """Compiles the HTML Business Report."""
        perf = analytics_res.get("performance_analysis", {})
        risk = analytics_res.get("risk_analysis", {})
        traders = analytics_res.get("trader_analysis", {})
        coin = analytics_res.get("coin_analysis", {})
        time_analysis = analytics_res.get("time_analysis", {})
        intel = analytics_res.get("intelligence_summary", {})

        # Portfolio Summary Table
        pnl_vol = risk.get("pnl_volatility", 0)
        risk_class = "text-neutral"
        if risk.get("risk_classification") == "Low Risk":
            risk_class = "text-profit"
        elif risk.get("risk_classification") in ["High Risk", "Extreme Risk"]:
            risk_class = "text-loss"

        # Coin Leaderboard Table
        coin_rows = []
        coin_pnls = coin.get("coin_pnls", {})
        if coin_pnls:
            sorted_coins = sorted(
                coin_pnls.items(), key=lambda item: item[1].get("sum", 0), reverse=True
            )
            for symbol, details in sorted_coins:
                row_class = "text-profit" if details.get("sum", 0) >= 0 else "text-loss"
                coin_rows.append(
                    f"""
                    <tr>
                        <td><strong>{symbol}</strong></td>
                        <td class="{row_class}">{cls._format_currency(details.get('sum', 0))}</td>
                        <td>{details.get('count', 0)}</td>
                        <td>{cls._format_pct(details.get('win_rate', 0))}</td>
                        <td>{cls._format_float(details.get('volume', 0), 2)}</td>
                    </tr>
                    """
                )
        coin_table = "".join(coin_rows)

        # Trader Leaderboard Table
        trader_rows = []
        top_traders = traders.get("top_10_traders", [])
        if top_traders:
            for idx, t in enumerate(top_traders, 1):
                trader_rows.append(
                    f"""
                    <tr>
                        <td>Rank #{idx} <code>{t.get('trader_id')}</code></td>
                        <td class="text-profit">{cls._format_currency(t.get('net_profit'))}</td>
                        <td>{cls._format_pct(t.get('win_rate'))}</td>
                        <td>{cls._format_float(t.get('profit_factor'), 2)}</td>
                        <td>{t.get('total_trades')}</td>
                    </tr>
                    """
                )
        trader_table = "".join(trader_rows)

        # Strategic recommendations
        recs = []
        for rec in intel.get("recommendations", []):
            recs.append(f"<li>{rec}</li>")
        recs_html = "".join(recs)

        body = f"""
        <div class="grid-2">
            <div class="card">
                <h2>Portfolio Financial Performance</h2>
                <p>Business view of realized profits, losses, transaction costs, and win ratios.</p>
                <table>
                    <tbody>
                        <tr><td><strong>Gross Profit</strong></td><td class="text-profit">{cls._format_currency(perf.get('gross_profit', 0))}</td></tr>
                        <tr><td><strong>Gross Loss</strong></td><td class="text-loss">{cls._format_currency(perf.get('gross_loss', 0))}</td></tr>
                        <tr><td><strong>Net Realized Return</strong></td><td class="{'text-profit' if perf.get('net_profit', 0) >= 0 else 'text-loss'}" style="font-weight:700;">{cls._format_currency(perf.get('net_profit', 0))}</td></tr>
                        <tr><td><strong>Win Rate</strong></td><td>{cls._format_pct(perf.get('win_rate', 0))}</td></tr>
                        <tr><td><strong>Profit Factor</strong></td><td>{cls._format_float(perf.get('profit_factor', 0), 2)}</td></tr>
                        <tr><td><strong>Binance Futures Trading Fees</strong></td><td class="text-loss">{cls._format_currency(perf.get('total_fees', 0))}</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>Exposures & Risk Summary</h2>
                <p>Standardized risk analysis metrics, Value at Risk (VaR), and expected declines.</p>
                <table>
                    <tbody>
                        <tr><td><strong>Portfolio Volatility (Closed PnL Std)</strong></td><td>{cls._format_float(pnl_vol, 4)}</td></tr>
                        <tr><td><strong>Max Realized Drawdown</strong></td><td class="text-loss">{cls._format_pct(risk.get('max_drawdown', 0))}</td></tr>
                        <tr><td><strong>Value at Risk (95% VaR)</strong></td><td class="text-loss">{cls._format_currency(risk.get('value_at_risk_95', 0))}</td></tr>
                        <tr><td><strong>Expected Shortfall (95% ES)</strong></td><td class="text-loss">{cls._format_currency(risk.get('expected_shortfall_95', 0))}</td></tr>
                        <tr><td><strong>Average Win/Loss Trade Ratio</strong></td><td>{cls._format_float(risk.get('profit_loss_ratio', 0), 2)}</td></tr>
                        <tr><td><strong>Composite Risk Assessment</strong></td><td><strong class="{risk_class}">{risk.get('risk_classification', 'Unknown')}</strong></td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>Asset Profitability Leaderboard</h2>
                <p>Performance breakdown by cryptocurrency asset traded.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Net Realized Return</th>
                            <th>Trades</th>
                            <th>Win Rate</th>
                            <th>Volume</th>
                        </tr>
                    </thead>
                    <tbody>
                        {coin_table}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>Trader Leadership Rankings</h2>
                <p>Performance ranking of top trading accounts by total net PnL.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Account Code</th>
                            <th>Net PnL</th>
                            <th>Win Rate</th>
                            <th>Profit Factor</th>
                            <th>Trades</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trader_table}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>Temporal Sessions Analysis</h2>
            <p>Breakdown of trading activity based on UTC time parameters.</p>
            <table>
                <tbody>
                    <tr><td><strong>Most Profitable Session Hour</strong></td><td><code>{time_analysis.get('best_trading_hour', 'N/A')}:00 UTC</code></td></tr>
                    <tr><td><strong>Least Profitable Session Hour</strong></td><td><code>{time_analysis.get('worst_trading_hour', 'N/A')}:00 UTC</code></td></tr>
                    <tr><td><strong>Most Profitable Day of Week</strong></td><td><code>{time_analysis.get('best_trading_day', 'N/A')}</code></td></tr>
                    <tr><td><strong>Least Profitable Day of Week</strong></td><td><code>{time_analysis.get('worst_trading_day', 'N/A')}</code></td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>Portfolio Optimization Recommendations</h2>
            <ul class="recommendations-list">
                {recs_html if recs_html else "<li>No recommendations available.</li>"}
            </ul>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>Asset Performance Leaderboard Chart</h2>
                <div class="chart-container">
                    <img src="../../outputs/charts/coin_leaderboard.png" class="chart-img" alt="Asset PnL Leaderboard">
                    <div class="chart-caption">Figure 3.1: Net realized return across symbols traded.</div>
                </div>
            </div>

            <div class="card">
                <h2>UTC Session Profitability Grid</h2>
                <div class="chart-container">
                    <img src="../../outputs/charts/hourly_heatmap.png" class="chart-img" alt="UTC Session Heatmap">
                    <div class="chart-caption">Figure 3.2: UTC hour of day vs. day of week trading performance distribution.</div>
                </div>
            </div>
        </div>
        """

        return cls._get_html_wrapper(
            title="Portfolio & Business Performance",
            subtitle="Business overview, rankings leaderboards, risk profiles, and temporal statistics.",
            report_type="Business Report",
            body_content=body,
        )

    @classmethod
    def compile_all(
        cls, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> Dict[str, str]:
        """Compiles all three HTML reports and returns them in a dictionary."""
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
