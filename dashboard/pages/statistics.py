"""Statistics Page for the PrimeTrade AI dashboard."""

from pathlib import Path
import streamlit as st
import pandas as pd

from dashboard.components import hero_banner
from analytics.statistics.statistics_engine import StatisticsEngine

hero_banner(
    title="🧮 Statistical Inference Center",
    subtitle="Validate trading performance significance, correlation indexes, normality tests, and effect sizes.",
)

active_path = Path(st.session_state.active_dataset_path) if st.session_state.active_dataset_path else None

if not active_path or not active_path.exists():
    st.warning("⚠️ No active dataset has been selected. Please upload a dataset first in the **Upload Dataset** page.")
else:
    try:
        df = pd.read_csv(active_path)
        required = ["closed_pnl", "timestamp", "symbol", "side"]
        
        if not all(col in df.columns for col in required):
            st.warning("⚠️ Selected dataset does not contain required preprocessed columns. Run Preprocessing on the **Analytics** page first.")
            st.stop()
            
        with st.spinner("Calculating mathematical and statistical models..."):
            # Run engine
            results = StatisticsEngine.run_statistics(df, export_outputs=False)
            
        st.subheader("📝 Statistical Summary Observations")
        observations = results.get("observations", [])
        if observations:
            obs_html = "".join(f"<li style='margin-bottom: 8px;'>{obs}</li>" for obs in observations)
            st.markdown(
                f"""
                <div style="background-color:rgba(30,41,59,0.4); padding:20px; border-radius:10px; border-left: 5px solid #9f7aea; margin-bottom:25px;">
                    <ul style="margin: 0; padding-left: 20px; font-size: 1.05rem; line-height: 1.5; color:#e2e8f0;">
                        {obs_html}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No statistical observations generated for this dataset.")
            
        # Tabs for grouping statistical results
        tab_desc, tab_corr, tab_hyp, tab_dist = st.tabs(
            ["📊 Descriptive Stats", "🔗 Correlations", "🧪 Hypothesis Testing", "📉 Distributions & Effect Sizes"]
        )
        
        with tab_desc:
            st.markdown("#### Descriptive Statistics")
            desc_dict = results.get("descriptive", {})
            
            # Format nicely as table
            desc_df = pd.DataFrame(desc_dict).T
            st.dataframe(desc_df, use_container_width=True)
            
            st.markdown("#### 95% Confidence Intervals")
            ci_dict = results.get("confidence_intervals", {})
            ci_df = pd.DataFrame(ci_dict).T
            st.dataframe(ci_df, use_container_width=True)

        with tab_corr:
            st.markdown("#### Sentiment Correlation Matrix")
            corr_dict = results.get("correlations", {})
            corr_df = pd.DataFrame(corr_dict)
            st.dataframe(corr_df, use_container_width=True)
            
        with tab_hyp:
            st.markdown("#### Significance & Hypothesis Tests (Fear vs Greed)")
            hyp_dict = results.get("hypothesis_tests", {})
            for test_name, test_data in hyp_dict.items():
                p_val = test_data.get("p_value")
                stat = test_data.get("statistic")
                reject = test_data.get("rejects_null", False) or test_data.get("reject_null", False)
                
                sig_badge = '<span class="badge badge-success">Statistically Significant</span>' if reject else '<span class="badge badge-danger">Not Significant</span>'
                
                stat_str = f"{stat:.4f}" if stat is not None else "N/A"
                pval_str = f"{p_val:.6f}" if p_val is not None else "N/A"
                
                st.markdown(
                    f"""
                    <div style="background-color:rgba(15,23,42,0.4); padding:15px; border-radius:8px; border:1px solid rgba(255,255,255,0.05); margin-bottom:15px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h5 style="margin:0; font-size:1.1rem; color:#00bfff;">{test_name.replace('_', ' ').title()}</h5>
                            {sig_badge}
                        </div>
                        <p style="margin: 10px 0 0 0; font-size:0.9rem;">
                            <b>Test Statistic:</b> {stat_str} &nbsp;&nbsp;|&nbsp;&nbsp; <b>P-Value:</b> {pval_str}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
        with tab_dist:
            st.markdown("#### Normality & Distribution Checks")
            dist_dict = results.get("distributions", {})
            dist_df = pd.DataFrame(dist_dict).T
            st.dataframe(dist_df, use_container_width=True)
            
            st.markdown("#### Effect Sizes")
            effects = results.get("effect_sizes", {})
            
            col1, col2 = st.columns(2)
            with col1:
                cohen = effects.get("cohens_d", {})
                cohen_val = cohen.get("value")
                cohen_int = cohen.get("interpretation")
                cohen_val_str = f"{cohen_val:.4f}" if cohen_val is not None else "N/A"
                st.metric("Cohen's d (Magnitude of difference)", cohen_val_str, help=cohen_int)
                st.info(f"Interpretation: **{cohen_int}**")
            with col2:
                eta = effects.get("eta_squared", {})
                eta_val = eta.get("value")
                eta_int = eta.get("interpretation")
                eta_val_str = f"{eta_val:.4f}" if eta_val is not None else "N/A"
                st.metric("Eta Squared (Variance explained)", eta_val_str, help=eta_int)
                st.info(f"Interpretation: **{eta_int}**")
                
    except Exception as e:
        st.error(f"❌ Failed to run statistical computations: {e}")
