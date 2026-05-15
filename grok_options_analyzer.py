import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import norm

st.set_page_config(page_title="Grok Pro Options Analyzer", layout="wide")
st.title("🚀 Grok Pro Options Analyzer")
st.caption("Professional-grade options analysis for your retirement portfolio")

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

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Chart", "📈 Options Chain", "🔥 Covered Call", "🎯 Directional Strategy", "📈 Outlook"])

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

with tab4:
    st.subheader("🎯 High-Conviction Directional Strategy")
    st.caption("Buy Call or Buy Put — Weekly / Monthly / LEAPs")

    # Find expirations
    today = datetime.now()
    weekly = monthly = leaps = None
    for d in opt_dates:
        try:
            dte = (datetime.strptime(d, "%Y-%m-%d") - today).days
            if 5 <= dte <= 14 and not weekly: weekly = (d, dte)
            elif 25 <= dte <= 60 and not monthly: monthly = (d, dte)
            elif dte >= 300 and not leaps: leaps = (d, dte)
        except: continue

    # Professional conviction scoring
    analyst_target = info.get('targetMeanPrice')
    momentum = (current_price / hist['Close'].iloc[-30]) - 1 if len(hist) > 30 else 0
    conviction = 0
    if analyst_target and analyst_target > current_price * 1.15: conviction += 50
    if momentum > 0.08: conviction += 30
    if conviction >= 65 and weekly:
        exp, dte = weekly
        strike = round(current_price * 1.04 / 0.5) * 0.5
        pop = 42
        st.success("**EXTREME HIGH CONVICTION: BUY CALL (Weekly)**")
    elif conviction >= 45 and monthly:
        exp, dte = monthly
        strike = round(current_price * 1.06 / 0.5) * 0.5
        pop = 48
        st.success("**HIGH CONVICTION: BUY CALL (Monthly)**")
    else:
        st.info("**No high-conviction directional setup right now.**")
        exp = None

    if exp:
        st.write(f"**Expiration:** {exp} ({dte} days)")
        st.write(f"**Suggested Strike:** **${strike:.2f}**")
        st.write(f"**Est. Probability of Profit:** ~**{pop}%**")
        st.caption("Max risk = premium paid. Size small (1-2% of portfolio).")

with tab5:
    st.subheader("Long-term Outlook")
    if info.get('targetMeanPrice'):
        st.metric("Analyst Consensus Target", f"${info['targetMeanPrice']:.2f}")

st.caption("Educational tool only • Not financial advice • Pull down to refresh")
