import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timezone

# 🏢 Page Initialization
st.set_page_config(layout="wide", page_title="⚡ TapeStrike Terminal")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
        .stDataFrame { font-size: 12px !important; }
        .alert-box { padding: 6px; background-color: #1a1a1a; border-radius: 4px; margin-bottom: 4px; font-family: monospace; font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

# ⚡ Your Official Software Brand Title
st.title("⚡ TapeStrike Premium Momentum Terminal")

# 📋 Terminal Core Watchlist
WATCHLIST = {
    "S&P 500 Core": "SPY",
    "Nasdaq Tech": "QQQ",
    "Small Cap Momentum": "IWM",
    "Bitcoin Digital Tape": "BTC-USD",
    "Gold Safe Haven": "GLD",
    "Crude Oil Energy": "USO"
}

# 🔄 Caching Core Math Data & News - STRICT 60-SECOND REFRESH
@st.cache_data(ttl=60)
def fetch_terminal_data(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="6mo", interval="1d")
        raw_news = t_obj.news
        news_feed = raw_news if isinstance(raw_news, list) else []
        
        if df is not None and not df.empty:
            df = df.dropna(subset=['Close'])
            high, low, close, volume = df['High'], df['Low'], df['Close'], df['Volume']
            close_prev = close.shift(1)
            
            # 1. True Range, ATR & Chop calculations
            tr = pd.concat([high - low, (high - close_prev).abs(), (low - close_prev).abs()], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=14).mean()
            sum_tr = tr.rolling(window=14).sum()
            range_hl = high.rolling(window=14).max() - low.rolling(window=14).min()
            df['CHOP'] = 100 * (np.log10(sum_tr / range_hl) / np.log10(14))
            
            # 2. ADX calculation
            plus_dm = np.where((high.diff() > low.diff().abs()) & (high.diff() > 0), high.diff(), 0.0)
            minus_dm = np.where((low.diff() > high.diff()) & (low.diff() > 0), low.diff(), 0.0)
            plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=14).mean() / df['ATR'])
            minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=14).mean() / df['ATR'])
            dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
            df['ADX'] = dx.rolling(window=14).mean()
            
            # 3. RVOL Calculation (Current Day Volume / 20-Day Average Volume)
            df['Vol_Avg20'] = volume.rolling(window=20).mean()
            df['RVOL'] = volume / df['Vol_Avg20']
            
            return df.dropna(subset=['ATR', 'CHOP', 'ADX', 'RVOL']), news_feed
    except:
        return None, []
    return None, []

# 🔥 The Recency Catalyst Flame Engine
def calculate_news_flame(news_list):
    if not news_list:
        return "⚪ No Recent Feeds", "gray"
    now = datetime.now(timezone.utc)
    highest_status = ("⚪ Static Tape", "gray", 999.0)
    
    for article in news_list:
        pub_time = article.get('providerPublishTime') or article.get('pubdate') or article.get('publishDate')
        if not pub_time:
            continue
        try:
            dt_pub = datetime.fromtimestamp(int(pub_time), timezone.utc)
        except:
            continue
        hours_ago = (now - dt_pub).total_seconds() / 3600.0
        if hours_ago <= 1.0:
            return "💥 FRESH CATALYST (<1h)", "red"
        elif hours_ago <= 5.0 and highest_status[2] > 5.0:
            highest_status = ("🔥 ACTIVE CATALYST (1-5h)", "orange", hours_ago)
        elif hours_ago <= 12.0 and highest_status[2] > 12.0:
            highest_status = ("☀️ COOLING FEED (5-12h)", "yellow", hours_ago)
            
    return highest_status[0], highest_status[1]

# 🗂️ Compile Sidebar Scanner Engine Data
matrix_results = []
news_store = {}
hod_alerts = []

for name, ticker in WATCHLIST.items():
    df_metrics, raw_news = fetch_terminal_data(ticker)
    news_store[ticker] = raw_news
    
    if df_metrics is not None and not df_metrics.empty:
        latest = df_metrics.iloc[-1]
        flame_label, flame_color = calculate_news_flame(raw_news)
        
        comp_score = (latest['CHOP'] * 1.5) - (latest['ADX'] * 0.5)
        comp_score = max(0.0, min(100.0, comp_score))
        
        # 🚨 HOD Momentum Trigger Logic
        if latest['Close'] >= (latest['High'] * 0.995):
            hod_alerts.append(f"⚡ [ALERT] {ticker} striking near session highs. Price: ${latest['Close']:,.2f} | RVOL: {latest['RVOL']:.1f}x")
            
        matrix_results.append({
            "Symbol": ticker,
            "Price": f"${latest['Close']:,.2f}",
            "RVOL": round(latest['RVOL'], 1),
            "Breakout Potential": round(comp_score, 1),
            "News State": flame_label,
            "ADX": round(latest['ADX'], 1)
        })

scanner_df = pd.DataFrame(matrix_results).sort_values(by="Breakout Potential", ascending=False)

# ----------------- LAYOUT BUILDING -----------------
col_scan, col_main = st.columns([1, 2])

with col_scan:
    st.markdown("### 📋 Active Momentum Scanners")
    st.dataframe(
        scanner_df,
        column_config={
            "Breakout Potential": st.column_config.ProgressColumn("Potential", format="%.0f%%", min_value=0, max_value=100),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx")
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    st.markdown("### 🚨 High-Of-Day (HOD) Momentum Stream")
    if hod_alerts:
        for alert in hod_alerts:
            st.markdown(f"<div class='alert-box' style='border-left: 3px solid #00ffcc; color: #00ffcc;'>{alert}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='alert-box' style='color:#666;'>No active structural breakout prints running.</div>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("### ⚠️ Live Volatility Conditions")
    for idx, row in scanner_df.iterrows():
        lbl = row['News State']
        tick = row['Symbol']
        if "💥" in lbl:
            st.markdown(f"🔴 **{tick}** - {lbl}")
        elif "🔥" in lbl:
            st.markdown(f"🟠 **{tick}** - {lbl}")
        elif "☀️" in lbl:
            st.markdown(f"🟡 **{tick}** - {lbl}")

with col_main:
    st.markdown("### 🎯 Focused Command Workspace")
    focus_ticker = st.selectbox("Select Core Asset Focus to Route Terminal Visuals:", list(WATCHLIST.values()))
    focus_data, focus_news = fetch_terminal_data(focus_ticker)
    
    if focus_data is not None and not focus_data.empty:
        latest_focus = focus_data.iloc[-1]
        
        # Calculate Key S&R Floor/Ceiling lines dynamically
        prev_session = focus_data.iloc[-2] if len(focus_data) > 1 else latest_focus
        p_high = prev_session['High']
        p_low = prev_session['Low']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Last Executed Price", f"${latest_focus['Close']:,.2f}")
        m2.metric("RVOL Factor", f"{latest_focus
