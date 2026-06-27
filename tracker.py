import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timezone

# 🏢 Page Initialization for a Pro-Trading Terminal Space
st.set_page_config(layout="wide", page_title="⚡ Momentum Terminal")

# Inject Custom CSS to give it that dark, high-density "Warrior Trading" dashboard vibe
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
        .stDataFrame { font-size: 12px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Pro Momentum Station & News Catalyst Terminal")

# 📋 Terminal Core Watchlist
WATCHLIST = {
    "S&P 500 Core": "SPY",
    "Nasdaq Tech": "QQQ",
    "Small Cap Momentum": "IWM",
    "Bitcoin Digital Tape": "BTC-USD",
    "Gold Safe Haven": "GLD",
    "Crude Oil Energy": "USO"
}

# 🔄 Caching Core Math Data & News
@st.cache_data(ttl=300)  # 5-minute refresh rate for active trading sessions
def fetch_terminal_data(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="3mo", interval="1d")
        news_feed = t_obj.news
        
        if df is not None and not df.empty:
            df = df.dropna(subset=['Close'])
            # Core Mathematics calculations
            high, low, close = df['High'], df['Low'], df['Close']
            close_prev = close.shift(1)
            tr = pd.concat([high - low, (high - close_prev).abs(), (low - close_prev).abs()], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=14).mean()
            
            sum_tr = tr.rolling(window=14).sum()
            range_hl = high.rolling(window=14).max() - low.rolling(window=14).min()
            df['CHOP'] = 100 * (np.log10(sum_tr / range_hl) / np.log10(14))
            
            plus_dm = np.where((high.diff() > low.diff().abs()) & (high.diff() > 0), high.diff(), 0.0)
            minus_dm = np.where((low.diff() > high.diff()) & (low.diff() > 0), low.diff(), 0.0)
            plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=14).mean() / df['ATR'])
            minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=14).mean() / df['ATR'])
            dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
            df['ADX'] = dx.rolling(window=14).mean()
            
            return df.dropna(subset=['ATR', 'CHOP', 'ADX']), news_feed
    except:
        return None, []
    return None, []

# 🔥 1. The Recency Catalyst Flame Engine
def calculate_news_flame(news_list):
    if not news_list:
        return "⚪ No Recent Feeds", "gray"
    
    now = datetime.now(timezone.utc)
    highest_status = ("⚪ Static Tape", "gray", 999.0) # baseline
    
    for article in news_list:
        # Pull publish time from yfinance news output
        pub_time = article.get('providerPublishTime')
        if not pub_time:
            continue
            
        dt_pub = datetime.fromtimestamp(pub_time, timezone.utc)
        hours_ago = (now - dt_pub).total_seconds() / 3600.0
        
        # Check against our priority flame scale thresholds
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

for name, ticker in WATCHLIST.items():
    df_metrics, raw_news = fetch_terminal_data(ticker)
    news_store[ticker] = raw_news
    
    if df_metrics is not None and not df_metrics.empty:
        latest = df_metrics.iloc[-1]
        flame_label, flame_color = calculate_news_flame(raw_news)
        
        comp_score = (latest['CHOP'] * 1.5) - (latest['ADX'] * 0.5)
        comp_score = max(0.0, min(100.0, comp_score))
        
        matrix_results.append({
            "Symbol": ticker,
            "Price": f"${latest['Close']:,.2f}",
            "Breakout Potential": round(comp_score, 1),
            "News State": flame_label,
            "ADX": round(latest['ADX'], 1),
            "CHOP": round(latest['CHOP'], 1)
        })

scanner_df = pd.DataFrame(matrix_results).sort_values(by="Breakout Potential", ascending=False)

# ----------------- LAYOUT BUILDING -----------------
# We create a 2-Column Split: Column 1 is the Left Sidebar Scanner, Column 2 is the Massive Charting Workspace
col_scan, col_main = st.columns([1, 2])

with col_scan:
    st.markdown("### 📋 Active Momentum Scanners")
    
    # Render the styled Day-Trading Scanner Grid
    st.dataframe(
        scanner_df,
        column_config={
            "Breakout Potential": st.column_config.ProgressColumn(
                "Potential", format="%.0f%%", min_value=0, max_value=100
            )
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    st.markdown("### ⚠️ Live Volatility Conditions")
    for idx, row in scanner_df.iterrows():
        # Display explicit colored status alerts underneath the table
        lbl = row['News State']
        tick = row['Symbol']
        if "💥" in lbl:
            st.markdown(f"🔴 **{tick}** - {lbl}")
        elif "🔥" in lbl:
            st.markdown(f"🟠 **{tick}** - {lbl}")
        elif "☀️" in lbl:
            st.markdown(f"🟡 **{tick}** - {lbl}")

with col_main:
    # 🎛️ Asset focus selector
    st.markdown("### 🎯 Focused Command Workspace")
    focus_ticker = st.selectbox("Select Core Asset Focus to Route Terminal Visuals:", list(WATCHLIST.values()))
    
    # Pull current active stats for workspace headers
    focus_data, focus_news = fetch_terminal_data(focus_ticker)
    
    if focus_data is not None and not focus_data.empty:
        latest_focus = focus_data.iloc[-1]
        
        # Display top ribbon data bars resembling an interactive trading dashboard execution widget
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Last Executed Price", f"${latest_focus['Close']:,.2f}")
        m2.metric("ADX Vector Strength", f"{latest_focus['ADX']:.2f}")
        m3.metric("Structural Chop Index", f"{latest_focus['CHOP']:.2f}")
        m4.metric("ATR Band Drift", f"${latest_focus['ATR']:.2f}")
        
        # 📊 RENDER MULTI-TIMELINE MATRIX SPREAD (Simulating Ross Cameron's Multi-Chart Grid)
        st.markdown("#### 📈 Multi-Pane Technical Analysis Workspace")
        c1, c2 = st.columns(2)
        
        # Chart 1: 6-Month Macro Swing Frame
        with c1:
            fig1 = go.Figure(data=[go.Candlestick(
                x=focus_data.index, open=focus_data['Open'], high=focus_data['High'],
                low=focus_data['Low'], close=focus_data['Close'], name="Macro Daily"
            )])
            fig1.update_layout(template="plotly_dark", title="6-Month Trend Framework", height=240, margin=dict(l=10,r=10,t=30,b=10), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig1, use_container_width=True)
            
        # Chart 2: 30-Day Aggressive Momentum Frame
        with c2:
            short_df = focus_data.tail(30)
            fig2 = go.Figure(data=[go.Scatter(x=short_df.index, y=short_df['Close'], mode='lines+markers', line=dict(color='#00ffcc'), name="30D Close")])
            fig2.update_layout(template="plotly_dark", title="30-Day Velocity Zoom Panel", height=240, margin=dict(l=10,r=10,t=30,b=10))
            st.plotly_chart(fig2, use_container_width=True)

        # 📰 CURRENT FOCUS ACTIVE NEWS FEED PANEL
        st.markdown("---")
        st.markdown("### 📰 Routed Catalyst Streaming Feed")
        
        if focus_news:
            for item in focus_news[:5]: # display top 5 most recent feeds
                p_time = item.get('providerPublishTime')
                time_str = datetime.fromtimestamp(p_time, timezone.utc).strftime('%H:%M:%S UTC') if p_time else "Unknown"
                
                # Check current item timeline to inject inline styling
                now = datetime.now(timezone.utc)
                dt_pub = datetime.fromtimestamp(p_time, timezone.utc) if p_time else now
                h_diff = (now - dt_pub).total_seconds() / 3600.0
                
                if h_diff <= 1.0:
                    badge, txt_col = "💥 [CRIMSON FLASH]", "#ff3333"
                elif h_diff <= 5.0:
                    badge, txt_col = "🔥 [ORANGE CATALYST]", "#ff9933"
                elif h_diff <= 12.0:
                    badge, txt_col = "☀️ [YELLOW GLOW]", "#ffff33"
                else:
                    badge, txt_col = "📁 [ARCHIVE]", "#888888"
                    
                st.markdown(f"""
                    <div style="padding:8px; border-left: 4px solid {txt_col}; background-color: #1e1e1e; margin-bottom:6px; border-radius:4px;">
                        <span style="color: {txt_col}; font-weight:bold;">{badge} ({time_str})</span><br/>
                        <a href="{item.get('link')}" target="_blank" style="color: #ffffff; font-weight:500; text-decoration:none;">{item.get('title')}</a><br/>
                        <span style="color: #888888; font-size:11px;">Source: {item.get('publisher')}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No active structural print cycles found for this asset index.")
