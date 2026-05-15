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
                st.write(f"**Exp:** {b['expiry']} | **Strike:** **${b['strike']:.2f}** | **Premium:** **${
