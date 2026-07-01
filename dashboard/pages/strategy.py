"""Strategy Evaluation Page for the PrimeTrade AI dashboard."""

import json
from pathlib import Path
import streamlit as st
import pandas as pd

from dashboard.components import hero_banner
from analytics.strategy.rule_based import RuleBasedStrategy, StrategyConfig
from analytics.strategy.strategy_engine import StrategyEngine

hero_banner(
    title="🧠 Strategy Recommendation Desk",
    subtitle="Configure risk limits and sentiment ranges, compute real-time buy/sell triggers, and download strategy signals.",
)

active_path = Path(st.session_state.active_dataset_path) if st.session_state.active_dataset_path else None

if not active_path or not active_path.exists():
    st.warning("⚠️ No active dataset selected. Go to the **Upload Dataset** page to load trades first.")
else:
    # Load dataset
    df = pd.read_csv(active_path)
    
    # Check columns
    required = ["closed_pnl", "timestamp", "symbol", "side"]
    if not all(col in df.columns for col in required):
        st.warning("⚠️ Dataset needs to be preprocessed. Preprocess it on the **Analytics** page.")
        st.stop()
        
    st.sidebar.subheader("⚙️ Strategy Parameters")
    
    # Sliders for parameters
    max_dd = st.sidebar.slider("Max Drawdown Threshold", 0.01, 0.50, 0.15, 0.01, help="Max loss allowance before halting trades")
    min_wr = st.sidebar.slider("Min Rolling Win Rate", 0.10, 0.90, 0.45, 0.05, help="Win rate threshold below which leverage is reduced")
    overtrading_limit = st.sidebar.slider("Overtrading Freq Limit (Trades/Day)", 1.0, 50.0, 10.0, 1.0)
    fg_buy = st.sidebar.slider("Fear Accumulation Threshold (F&G)", 5.0, 45.0, 25.0, 1.0, help="Buy point")
    fg_sell = st.sidebar.slider("Greed Distribution Threshold (F&G)", 55.0, 95.0, 75.0, 1.0, help="Sell point")
    initial_bal = st.sidebar.number_input("Initial Balance ($)", 100.0, 1000000.0, 10000.0, step=1000.0)
    
    current_fg = st.number_input("Simulated Latest Fear & Greed Index Score (0-100)", 0, 100, 50)
    
    if st.button("⚡ Evaluate Recommendation"):
        with st.spinner("Executing rule-based sentiment checks..."):
            try:
                # Construct config
                config = StrategyConfig(
                    max_drawdown_threshold=max_dd,
                    min_rolling_win_rate=min_wr,
                    overtrading_frequency_limit=overtrading_limit,
                    fear_greed_buy_threshold=fg_buy,
                    fear_greed_sell_threshold=fg_sell,
                    initial_balance=initial_bal,
                )
                
                # Setup engine
                strategy = RuleBasedStrategy(config=config)
                engine = StrategyEngine(strategies=[strategy])
                
                # Execute
                rec_dict = engine.run_strategy_analysis(
                    df, current_sentiment_val=float(current_fg), export_outputs=False
                )
                
                # Store in session state
                st.session_state.last_recommendation = rec_dict
                st.success("Analysis executed successfully!")
                
            except Exception as e:
                st.error(f"❌ Failed to run strategy engine: {e}")
                
    # Display last recommendations if available
    if "last_recommendation" in st.session_state and st.session_state.last_recommendation:
        rec = st.session_state.last_recommendation
        
        # Determine the recommendations structure
        # Let's inspect what StrategyEngine returns
        # Usually it returns: { "recommendations": [ { "strategy_name": ..., "recommendation": { "action": ..., "confidence_score": ..., "explanations": ..., "metrics": ... } } ] }
        # Let's print or display nicely based on the output keys
        recs = rec.get("recommendations", [])
        
        for r_entry in recs:
            strat_name = r_entry.get("strategy_name")
            r_details = r_entry.get("recommendation", {})
            action = r_details.get("action")
            confidence = r_details.get("confidence_score", 0.0)
            explanations = r_details.get("explanations", [])
            metrics = r_details.get("metrics", {})
            
            # Action Colors and Display
            action_colors = {
                "BUY": "#48bb78",
                "SELL": "#e53e3e",
                "HOLD": "#a0aec0",
                "REDUCE_LEVERAGE": "#ec971f",
                "INCREASE_POSITION_SIZE": "#00bfff",
                "AVOID_TRADING": "#d69e2e",
            }
            color = action_colors.get(action, "#ffffff")
            
            st.markdown(
                f"""
                <div style="background-color:rgba(25, 30, 40, 0.7); border-radius:12px; border:2px solid {color}; padding:25px; margin-bottom:25px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0; color:#ffffff;">{strat_name}</h3>
                        <span style="font-size:1.8rem; font-weight:800; color:{color}; text-transform:uppercase;">{action}</span>
                    </div>
                    <div style="margin-top:15px; font-size:1.15rem;">
                        <b>Confidence Score:</b> <span style="color:#00bfff; font-weight:700;">{confidence * 100:.0f}%</span>
                    </div>
                    <div style="margin-top:15px;">
                        <b>Explanations & Rationale:</b>
                        <ul style="margin-top:5px; padding-left:20px; line-height:1.6;">
                            {"".join(f"<li>{exp}</li>" for exp in explanations)}
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Display calculated metrics inside column cards
            st.markdown("#### Computed Analysis Metrics")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("Latest F&G Score", f"{metrics.get('fear_greed_score', 0.0):.0f}")
            with m_col2:
                dd_val = metrics.get('current_drawdown', 0.0)
                st.metric("Current Drawdown", f"{dd_val:.2%}")
            with m_col3:
                wr_val = metrics.get('rolling_win_rate', 0.0)
                st.metric("Rolling Win Rate", f"{wr_val:.1%}")
            with m_col4:
                st.metric("Trades / Day", f"{metrics.get('trades_per_day', 0.0):.2f}")
                
        # Export triggers
        st.markdown("### 📥 Download Recommendations")
        rec_json = json.dumps(rec, indent=2)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download recommendations (JSON)",
                data=rec_json,
                file_name="strategy_recommendations.json",
                mime="application/json",
                use_container_width=True,
            )
        with col2:
            # Simple markdown generator for recommendations
            md_str = f"# Strategy Recommendations Report\n\n"
            for r_entry in recs:
                md_str += f"## Strategy: {r_entry.get('strategy_name')}\n"
                details = r_entry.get("recommendation", {})
                md_str += f"- **Action**: {details.get('action')}\n"
                md_str += f"- **Confidence**: {details.get('confidence_score') * 100:.0f}%\n"
                md_str += "- **Rationale**:\n"
                for exp in details.get("explanations", []):
                    md_str += f"  - {exp}\n"
                md_str += "\n"
            st.download_button(
                label="Download Report (Markdown)",
                data=md_str,
                file_name="strategy_recommendations.md",
                mime="text/markdown",
                use_container_width=True,
            )
