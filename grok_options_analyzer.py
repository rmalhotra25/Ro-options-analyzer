import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Grok Options Analyzer", layout="wide")
st.title("🚀 Grok High-Conviction Options Analyzer")

ticker = st.sidebar.text_input("Enter Ticker (SMCI or BMNR)", value="SMCI").upper().strip()

# No heavy caching
stock = yf.Ticker(ticker)
info = stock.info
hist = stock.history(period="1y")
opt_dates = stock.options

current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)

if current_price == 0:
    st.error("Could not load data. Try SMCI, BMNR, AAPL or NVDA")
    st.stop()

st.success(f"✅ Loaded {ticker} — Current Price: **${current_price:.2f}**")

tab1, tab2, tab3 = st.tabs(["📊 Chart", "📈 Options Chain", "🔥 Covered Call"])

with tab1:
    st.subheader("1-Year Price Chart")
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist.Open, high=hist.High, low=hist.Low, close=hist.Close)])
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if opt_dates:
        expiry = st.selectbox("Expiration Date", opt_dates)
        chain = stock.option_chain(expiry)
        st.dataframe(chain.calls[["strike", "lastPrice", "bid", "ask", "impliedVolatility", "volume"]].head(20), use_container_width=True)

with tab3:
    st.subheader("Covered Call Strategy for Your 100 Shares")
    st.success(f"**Recommended for {ticker}**")
    st.write("**Strategy**: Sell **1 call contract** (30–45 days until expiration)")
    st.write("- Choose a strike **3–7% above** current price")
    st.write("- Collect premium immediately (income for retirement)")
    st.write("- Keep shares unless stock rises above strike")
    if ticker == "SMCI":
        st.info("SMCI currently has high volatility → **Excellent premiums** right now")
    elif ticker == "BMNR":
        st.info("BMNR is volatile → Strong income potential from covered calls")

st.caption("Educational tool only • Not financial advice • Pull down to refresh")
