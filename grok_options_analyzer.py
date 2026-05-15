import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import norm

st.set_page_config(page_title="Grok Options Analyzer", layout="wide")
st.title("🚀 Grok High-Conviction Options Analyzer")

ticker = st.sidebar.text_input("Enter Ticker", value="AAPL").upper().strip()

stock = yf.Ticker(ticker)
info = stock.info
hist = stock.history(period="5y")
opt_dates = stock.options

current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)

if current_price == 0:
    st.error("Could not load data.")
    st.stop()

st.success(f"✅ Loaded {ticker} — Current Price: **${current_price:.2f}**")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Chart", "📈 Options Chain", "🔥 Covered Call", "🎯 Directional Strategy", "📈 Long-term Prediction", "📝 Trade Log"])

with tab1:
    st.subheader("1-Year Price Chart")
    fig = go.Figure(data=[go.Candlestick(x=hist.tail(252).index, open=hist.Open.tail(252), high=hist.High.tail(252), low=hist.Low.tail(252), close=hist.Close.tail(252))])
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if opt_dates:
        expiry = st.selectbox("Expiration Date", opt_dates)
        chain = stock.option_chain(expiry)
        st.dataframe(chain.calls[["strike", "lastPrice", "bid", "ask", "impliedVolatility", "volume"]].head(20), use_container_width=True)

# Covered Call Tab (unchanged)
with tab3:
    st.subheader("Covered Call Strategy for Your 100 Shares")
    today = datetime.now()
    best_expiry = None
    best_dte = 999
    best_expiry_date = None
    for d in opt_dates:
        try:
            exp_date = datetime.strptime(d, "%Y-%m-%d")
            dte = (exp_date - today).days
            if 25 <= dte <= 50 and abs(dte - 37) < best_dte:
                best_dte = abs(dte - 37)
                best_expiry = d
                best_expiry_date = exp_date.strftime("%b %d, %Y")
        except:
            continue
    if best_expiry:
        chain = stock.option_chain(best_expiry)
        calls = chain.calls
        def get_delta(S, K, T, sigma):
            if T <= 0 or sigma <= 0: return 1.0 if S > K else 0.0
            d1 = (np.log(S / K) + (0.04 + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            return norm.cdf(d1)
        tiers = {"High": [], "Moderate": [], "Conservative": []}
        for _, row in calls.iterrows():
            K = row['strike']
            if K <= current_price * 1.01: continue
            premium = max(float(row.get('bid', 0)), float(row.get('lastPrice', 0)))
            if premium < 0.10: continue
            T = best_dte / 365.0
            sigma = float(row['impliedVolatility'])
            delta = get_delta(current_price, K, T, sigma)
            prob_called = round(delta * 100, 1)
            rec = {"strike": K, "premium": round(premium, 2), "prob_called": prob_called, "prob_keep": round(100-prob_called,1), "expiry": best_expiry_date, "dte": best_dte}
            if prob_called >= 45: tiers["High"].append(rec)
            elif 25 <= prob_called < 40: tiers["Moderate"].append(rec)
            elif 10 <= prob_called <= 25: tiers["Conservative"].append(rec)
        for name, recs in [("🔥 High Premium", tiers["High"]), ("⚖️ Moderate", tiers["Moderate"]), ("🛡️ Low Premium", tiers["Conservative"])]:
            if recs:
                b = recs[0]
                st.markdown(f"### {name}")
                st.write(f"**Exp:** {b['expiry']} | **Strike:** **${b['strike']:.2f}** | **Premium:** **${b['premium']:.2f}** (${b['premium']*100:.0f} total)")
                st.write(f"Called chance: {b['prob_called']}% | Keep shares: {b['prob_keep']}%")
                st.divider()

# Directional Strategy Tab - Weekly / Monthly / LEAPs
with tab4:
    st.subheader("🎯 High-Conviction Directional Strategy")
    st.caption("Buy Call or Buy Put — Weekly, Monthly, LEAPs")

    # Find suitable expirations
    today = datetime.now()
    weekly = None
    monthly = None
    leaps = None
    for d in opt_dates:
        try:
            exp_date = datetime.strptime(d, "%Y-%m-%d")
            dte = (exp_date - today).days
            if 5 <= dte <= 14 and not weekly:
                weekly = d
            elif 25 <= dte <= 60 and not monthly:
                monthly = d
            elif dte >= 300 and not leaps:
                leaps = d
        except:
            continue

    # Simple conviction score
    analyst_target = info.get('targetMeanPrice')
    recent_momentum = (current_price / hist['Close'].iloc[-30]) - 1 if len(hist) > 30 else 0
    conviction = 0
    if analyst_target and analyst_target > current_price * 1.12: conviction += 55
    if recent_momentum > 0.05: conviction += 35

    if conviction >= 70 and weekly:
        st.success("**EXTREME HIGH CONVICTION: BUY CALL (Weekly)**")
        st.write(f"**Expiration:** {weekly}")
        st.write(f"**Suggested Strike:** ~ **${round(current_price * 1.03, 2)}** (slightly OTM)")
    elif conviction >= 50 and monthly:
        st.success("**HIGH CONVICTION: BUY CALL (Monthly)**")
        st.write(f"**Expiration:** {monthly}")
        st.write(f"**Suggested Strike:** ~ **${round(current_price * 1.05, 2)}**")
    elif conviction >= 75 and leaps:
        st.info("**HIGH CONVICTION LEAP: BUY CALL**")
        st.write(f"**Expiration:** {leaps} (Long-term)")
        st.write(f"**Suggested Strike:** ~ **${round(current_price * 1.10, 2)}**")
    elif conviction <= 20:
        st.warning("**HIGH CONVICTION: BUY PUT (Monthly)**")
        st.write(f"**Expiration:** {monthly or 'Next available'}")
        st.write(f"**Suggested Strike:** ~ **${round(current_price * 0.95, 2)}**")
    else:
        st.info("**No High-Conviction Directional Setup Right Now**")
        st.caption("Consider running Covered Calls instead or waiting for better momentum.")

    st.caption("Always verify exact premiums and Greeks in the Options Chain tab before trading.")

# Long-term Prediction Tab
with tab5:
    st.subheader(f"12–24 Month Price Outlook for {ticker}")
    analyst_mean = info.get('targetMeanPrice')
    if analyst_mean:
        st.metric("Analyst Consensus Target", f"${analyst_mean:.2f}")
    st.info("Use this for overall portfolio conviction, not short-term option trades.")

# Trade Log
with tab6:
    st.subheader("📝 Trade Log")
    if 'trades' not in st.session_state:
        st.session_state.trades = []
    col1, col2 = st.columns(2)
    with col1:
        trade_type = st.selectbox("Type", ["Buy Call", "Buy Put", "Covered Call"])
    with col2:
        strike = st.number_input("Strike", value=float(current_price))
    premium = st.number_input("Premium Paid/Received", value=1.0)
    expiry = st.date_input("Expiration")
    if st.button("Log Trade"):
        st.session_state.trades.append({"Date": datetime.now().strftime("%Y-%m-%d"), "Ticker": ticker, "Type": trade_type, "Strike": strike, "Premium": premium, "Expiry": expiry})
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades), use_container_width=True)

st.caption("Educational tool only • Not financial advice • Always verify in your brokerage")
