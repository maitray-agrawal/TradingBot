"""Trading Bot Execution Desk Page for the PrimeTrade AI dashboard."""

import json
from pathlib import Path
import streamlit as st
import pandas as pd

from config import settings
from dashboard.components import hero_banner
from trading_bot.client.client import BinanceTestnetClient
from trading_bot.orders.orders import FuturesOrder
from trading_bot.validators import OrderValidator
from trading_bot.risk_manager import RiskManager
from trading_bot.order_manager import OrderManager

hero_banner(
    title="🤖 Trading Desk & Execution Console",
    subtitle="Configure order inputs, inspect pre-trade risk checklists, and execute orders to the Binance Futures Testnet.",
)

# Mode Selector
col_mode, col_bal = st.columns([2, 1])

with col_mode:
    live_mode = st.toggle("Activate Live Testnet Mode", value=st.session_state.bot_live_mode)
    if live_mode != st.session_state.bot_live_mode:
        st.session_state.bot_live_mode = live_mode
        # Re-initialize client
        if live_mode:
            if not settings.binance_api_key or not settings.binance_secret_key:
                st.error("❌ Binance Credentials missing in your configurations (.env). Cannot activate Live mode.")
                st.session_state.bot_live_mode = False
                st.rerun()
            else:
                st.session_state.binance_client = BinanceTestnetClient(
                    api_key=settings.binance_api_key,
                    api_secret=settings.binance_secret_key,
                    dry_run=False
                )
        else:
            st.session_state.binance_client = BinanceTestnetClient(dry_run=True)
        st.rerun()

# Client and Balance Fetching
client = st.session_state.binance_client
try:
    balance = client.get_balance("USDT")
except Exception as e:
    balance = 0.0

with col_bal:
    st.markdown(
        f"""
        <div style="background-color:rgba(15,23,42,0.6); padding:10px 20px; border-radius:8px; border:1px solid rgba(255,255,255,0.08); text-align:center;">
            <div style="font-size:0.85rem; color:#94a3b8; text-transform:uppercase;">USDT Wallet Balance</div>
            <div style="font-size:1.6rem; font-weight:800; color:#48bb78;">${balance:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# Main order routing grids
col_form, col_val = st.columns([3, 2])

with col_form:
    st.subheader("🛒 Place Futures Order")
    
    order_symbol = st.selectbox(
        "Symbol",
        options=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"],
        index=0
    )
    
    order_side = st.radio("Side", options=["BUY", "SELL"], horizontal=True)
    order_type = st.selectbox("Order Type", options=["MARKET", "LIMIT", "STOP_LIMIT"])
    
    col_qty, col_lev = st.columns(2)
    with col_qty:
        order_qty = st.number_input("Quantity (Units)", min_value=0.0001, value=0.01, step=0.001, format="%.4f")
    with col_lev:
        order_leverage = st.slider("Multiplier Leverage", 1, 125, 10)
        
    margin_type = st.radio("Margin Mode", options=["CROSS", "ISOLATED"], horizontal=True)
    
    order_price = None
    order_stop_price = None
    
    if order_type in ["LIMIT", "STOP_LIMIT"]:
        # Get simulated latest price for defaults
        try:
            curr_price = client.get_ticker_price(order_symbol)
        except Exception:
            curr_price = 30000.0 if "BTC" in order_symbol else 1800.0
            
        order_price = st.number_input("Limit Price (USDT)", min_value=0.0, value=float(curr_price), step=0.1)
        
    if order_type == "STOP_LIMIT":
        try:
            curr_price = client.get_ticker_price(order_symbol)
        except Exception:
            curr_price = 30000.0 if "BTC" in order_symbol else 1800.0
            
        order_stop_price = st.number_input("Stop/Trigger Price (USDT)", min_value=0.0, value=float(curr_price), step=0.1)

# Pre-trade compliance checker
with col_val:
    st.subheader("🔍 Pre-Trade Compliance Checklist")
    
    validator = OrderValidator()
    risk_manager = RiskManager()
    
    # Run interactive checks
    checks_passed = True
    
    # 1. Lot Size & Notional
    try:
        validated = validator.validate_notional_and_lot_size(
            client=client, symbol=order_symbol, quantity=order_qty, price=order_price
        )
        st.markdown(
            f"🟢 **Lot & Notional Filters**: Passed (Quantity: `{validated['quantity']:.4f}`, Price: `{validated['price']}`)"
        )
    except Exception as e:
        checks_passed = False
        st.markdown(f"❌ **Lot & Notional Filters**: Failed ({e})")
        
    # 2. Leverage Limit Check
    try:
        validator.validate_leverage(order_symbol, order_leverage)
        st.markdown(f"🟢 **Leverage Boundary**: Approved ({order_leverage}x)")
    except Exception as e:
        checks_passed = False
        st.markdown(f"❌ **Leverage Boundary**: Failed ({e})")
        
    # 3. Risk Engine Checklist (Max exposure, drawdowns)
    try:
        standardized_price = order_price
        if standardized_price is None:
            # Fallback ticker price
            try:
                standardized_price = client.get_ticker_price(order_symbol)
            except Exception:
                standardized_price = 30000.0 if "BTC" in order_symbol else 1800.0
                
        test_order = FuturesOrder(
            symbol=order_symbol,
            side=order_side,
            type=order_type,
            quantity=order_qty,
            price=standardized_price,
            stop_price=order_stop_price,
        )
        risk_manager.check_order_risk(client, test_order, order_leverage)
        st.markdown("🟢 **Risk Limits**: Approved (Within single-trade sizing ceilings)")
    except Exception as e:
        checks_passed = False
        st.markdown(f"❌ **Risk Limits**: Violation ({e})")
        
    # 4. Margin Balance Verification
    try:
        validator.validate_margin_requirements(client, test_order, order_leverage)
        st.markdown("🟢 **Wallet Margin**: Sufficient Initial Balance available")
    except Exception as e:
        checks_passed = False
        st.markdown(f"❌ **Wallet Margin**: Under-collateralized ({e})")
        
    # Overall indicator
    if checks_passed:
        st.success("✅ COMPLIANCE: Ready to Execute")
    else:
        st.warning("⚠️ COMPLIANCE: Order parameters violate risk boundaries")

# Submit Execution
if st.button("🚀 Submit Futures Order", disabled=not checks_passed, use_container_width=True):
    with st.spinner("Submitting order to the exchange client..."):
        try:
            manager = OrderManager(client=client, validator=validator, risk_manager=risk_manager)
            receipt = manager.place_order(
                symbol=order_symbol,
                side=order_side,
                order_type=order_type,
                quantity=order_qty,
                price=order_price,
                stop_price=order_stop_price,
                leverage=order_leverage,
                margin_type=margin_type,
            )
            
            # Display Execution receipt card
            st.markdown("### 🎉 Order Execution Receipt")
            mode_color = "#00bfff" if client.dry_run else "#9f7aea"
            side_color = "#48bb78" if order_side == "BUY" else "#e53e3e"
            
            st.markdown(
                f"""
                <div style="background-color:rgba(15,23,42,0.6); padding:20px; border-radius:10px; border:2px solid {mode_color}; margin-top:15px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; color:#ffffff;">Order ID: <b>{receipt.get('orderId', 'MOCK-ID')}</b></h4>
                        <span style="font-weight:700; color:{side_color};">{order_side} {order_symbol}</span>
                    </div>
                    <p style="margin-top:10px;"><b>Status:</b> <span class="badge badge-success">{receipt.get('status', 'NEW')}</span></p>
                    <p><b>Executed Quantity:</b> {order_qty:.4f} units</p>
                    <p><b>Limit Price:</b> {order_price if order_price else 'MARKET'}</p>
                    <p><b>Leverage Multiplier:</b> {order_leverage}x (Margin Type: {margin_type})</p>
                    <p style="font-size:0.85rem; color:#718096;">Timestamp: {receipt.get('updateTime', 'Simulated execution')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
        except Exception as e:
            st.error(f"❌ Order Execution Failed: {e}")

# Order History Log
st.markdown("---")
st.subheader("📜 Recent Order History logs")

history_file = Path("data/exports/order_history.json")
if history_file.exists():
    try:
        with open(history_file, "r") as f:
            history_data = json.load(f)
        if history_data:
            history_df = pd.DataFrame(history_data)
            # Reorder columns for readability
            cols = ["timestamp", "order_id", "symbol", "side", "type", "quantity", "price", "leverage", "status", "mode"]
            # Keep only available columns
            cols = [c for c in cols if c in history_df.columns]
            st.dataframe(history_df[cols].sort_values("timestamp", ascending=False), use_container_width=True)
        else:
            st.info("Order history log database is currently empty.")
    except Exception as e:
        st.error(f"Failed to load order history: {e}")
else:
    st.info("No orders executed yet in this environment.")
