import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from scipy.stats import norm

st.set_page_config(page_title="Grok Options Analyzer", layout="wide")
st.title("🚀 Grok High-Conviction Options Analyzer")

ticker = st.sidebar.text_input("Enter Ticker (SMCI or BMNR)", value="BMNR").upper().strip()

stock = yf.Ticker(ticker)
info = stock.info
hist = stock.history(period="1y")
opt_dates = stock.options

current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)

if current_price == 0:
    st.error("Could not load data.")
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
    
    # Find best 30-45 DTE expiration
    today = datetime.now()
    best_expiry = None
    best_dte = 999
    for d in opt_dates:
        try:
            dte = (datetime.strptime(d, "%Y-%m-%d") - today).days
            if 25 <= dte <= 50 and abs(dte - 37) < best_dte:
                best_dte = abs(dte - 37)
                best_expiry = d
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
            if K <= current_price * 1.01: continue  # Skip deep ITM
            premium = max(row['bid'], row['lastPrice'])
            if premium < 0.10: continue
            T = best_dte / 365.0
            sigma = row['impliedVolatility']
            delta = get_delta(current_price, K, T, sigma)
            prob_called = round(delta * 100, 1)
            prob_keep = round(100 - prob_called, 1)
            
            rec = {
                "strike": K,
                "premium": round(premium, 2),
                "prob_called": prob_called,
                "prob_keep": prob_keep,
                "dte": best_dte
            }
            
            if prob_called >= 45:
                tiers["High"].append(rec)
            elif 25 <= prob_called < 40:
                tiers["Moderate"].append(rec)
            elif 10 <= prob_called <= 25:
                tiers["Conservative"].append(rec)
        
        # Show best from each tier
        for tier_name, recs in [("High Premium (Higher Chance of Assignment)", tiers["High"]),
                               ("Moderate Premium (<40% Called)", tiers["Moderate"]),
                               ("Low Premium (10-25% Called)", tiers["Conservative"])]:
            if recs:
                best = recs[0]  # closest to ideal in tier
                st.markdown(f"### {tier_name}")
                st.write(f"**Strike:** ${best['strike']:.2f}")
                st.write(f"**Premium:** ${best['premium']:.2f} per share → **${best['premium']*100:.0f} total**")
                st.write(f"**Days:** {best['dte']} | **Chance of being called:** {best['prob_called']}%")
                st.write(f"**Chance you keep premium + shares:** {best['prob_keep']}%")
                st.divider()
    
    st.caption("Higher premium = higher chance of assignment. Choose based on your view of the stock.")

st.caption("Educational tool only • Not financial advice • Pull down to refresh")
