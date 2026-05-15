import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import norm

st.set_page_config(page_title="Grok Pro Options Analyzer", layout="wide")
st.title("🚀 Grok Pro Options Analyzer")

ticker = st.sidebar.text_input("Enter Ticker", value="AAPL").upper().strip()

stock = yf.Ticker(ticker)
info = stock.info
hist = stock.history(period="5y")
opt_dates = stock.options

current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)

if current_price == 0:
    st.error("Could not load data.")
    st.stop()

st.success(f"✅ Loaded {ticker} — ${current_price:.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Chart", "📈 Options Chain", "🔥 Covered Call", "🎯 Directional Strategy"])

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
    st.subheader("Covered Call (Income)")
    st.caption("For your 100 shares")
    # Simple placeholder for now to avoid errors
    st.info("Covered Call recommendations coming in next update - currently stable version")

with tab4:
    st.subheader("🎯 High-Conviction Directional Strategy")
    st.caption("Buy Call or Buy Put recommendations")
    st.success("**Working on professional version**")
    st.write("Test with different tickers (AAPL, SMCI, BMNR, NVDA)")
    st.info("This tab will show Weekly / Monthly Buy Call or Buy Put when conviction is high.")

st.caption("Educational tool only • Not financial advice • Pull down to refresh")
