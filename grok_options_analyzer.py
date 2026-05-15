import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
import plotly.graph_objects as go
from datetime import datetime
import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"  # Fix for Streamlit Cloud

st.set_page_config(page_title="Grok Options Analyzer", layout="wide")
st.title("🚀 Grok High-Conviction Options Analyzer")

# Sidebar
ticker_input = st.sidebar.text_input("Stock Ticker", value="SMCI").upper().strip()

@st.cache_data(ttl=60)
def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        options_dates = stock.options
        return stock, info, hist, options_dates
    except:
        return None, None, None, None

stock, info, hist, opt_dates = get_data(ticker_input)

if stock is None or info is None:
    st.error("Could not fetch data. Try a different ticker (e.g. AAPL, NVDA, SMCI) or refresh.")
    st.stop()

current_price = info.get('currentPrice') or info.get('regularMarketPrice', 100)

st.success(f"✅ Loaded {ticker_input} at ${current_price:.2f}")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Analysis", "📈 Options", "🔥 Covered Call (SMCI/BMNR)"])

with tab1:
    st.subheader("Price Chart")
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist.Open, high=hist.High, low=hist.Low, close=hist.Close)])
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if opt_dates:
        expiry = st.selectbox("Expiration Date", opt_dates)
        chain = stock.option_chain(expiry)
        st.dataframe(chain.calls[["strike", "lastPrice", "bid", "ask", "impliedVolatility"]].head(10), use_container_width=True)

with tab3:
    st.subheader("Covered Call Recommendation")
    if ticker_input in ["SMCI", "BMNR"]:
        st.success(f"High-Conviction Covered Call on your 100 shares of {ticker_input}")
        st.write("**Suggested:** Sell 1 call, 3-7% OTM, 30-45 days out")
        st.write("Premium estimate: Check the Options tab above")
    else:
        st.info("Enter SMCI or BMNR for tailored covered call advice")

st.caption("Refresh the page if data doesn't load. Educational tool only.")
