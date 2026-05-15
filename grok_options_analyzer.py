import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Grok Options Analyzer", layout="wide")
st.title("🚀 Grok High-Conviction Options Analyzer")

ticker_input = st.sidebar.text_input("Stock Ticker (e.g. SMCI)", value="SMCI").upper().strip()

@st.cache_data(ttl=120, show_spinner=False)
def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        options_dates = stock.options
        return stock, info, hist, options_dates
    except Exception as e:
        st.error(f"Data error: {str(e)[:100]}")
        return None, None, None, None

stock, info, hist, opt_dates = get_data(ticker_input)

if not info:
    st.warning("Could not load data. Try refreshing or using a popular ticker like AAPL, NVDA, or SMCI.")
    st.stop()

current_price = info.get('currentPrice') or info.get('regularMarketPrice', 100)

st.success(f"✅ {ticker_input} at ${current_price:.2f}")

tab1, tab2, tab3 = st.tabs(["📊 Analysis", "📈 Options Chain", "🔥 Covered Call"])

with tab1:
    st.subheader("1-Year Price Chart")
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist.Open, high=hist.High, low=hist.Low, close=hist.Close)])
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if opt_dates:
        expiry = st.selectbox("Select Expiration", opt_dates)
        chain = stock.option_chain(expiry)
        st.dataframe(chain.calls[["strike", "lastPrice", "bid", "ask", "impliedVolatility", "volume"]].head(15), use_container_width=True)

with tab3:
    st.subheader("Covered Call Recommendation")
    st.success(f"**For your 100 shares of {ticker_input}**")
    st.write("Sell **1 call contract** (30-45 days out, 3-7% above current price)")
    st.write("This generates immediate income while you keep the shares unless assigned.")
    if ticker_input == "SMCI":
        st.info("SMCI has high IV right now — good premiums expected.")
    elif ticker_input == "BMNR":
        st.info("BMNR is volatile — excellent premium potential.")

st.caption("Educational tool only • Not financial advice • Refresh if data is slow")
