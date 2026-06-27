import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timezone

# 🏢 Page Initialization
st.set_page_config(layout="wide", page_title="⚡ TapeStrike Terminal")

# Injecting terminal styles and custom structural layout tweaks
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        div[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: bold; }
        .stDataFrame { font-size: 12px !important; }
        .alert-box { padding: 6px; background-color: #1a1a1a; border-radius: 4px; margin-bottom: 4px; font-family: monospace; font-size: 11px; }
        .heatmap-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; margin-top: 5px; }
        .heatmap-card { padding: 12px; border-radius: 4px; text-align: center; font-weight: bold; font-family: monospace; font-size: 13px; min-height: 55px; }
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

# 🗺️ Sector Heatmap Reference Core
SECTORS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Healthcare",
    "XLE": "Energy"
}

# 🔄 Caching Macro Framework Data - 60-SECOND REFRESH
@st.cache_data(ttl=60)
def fetch_terminal_data(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="6mo", interval="1d")
        raw_news = t_obj.news
        news_feed = raw_news if isinstance(raw_news, list) else []
        
        if df is not None and not df.empty:
            df = df.dropna(subset=['Close'])
            if len(df) < 20:
                return None, []
                
            high, low, close, volume = df['High'], df['Low'], df['Close'], df['Volume']
            close_prev = close.shift(1)
            
            # True Range, ATR & Chop calculations
            tr = pd.concat([high - low, (high - close_prev).abs(), (low - close_prev).abs()], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=14).mean()
            sum_tr = tr.rolling(window=14).sum()
            range_hl = high.rolling(window=14).max() - low.rolling(window=14).min()
            df['CHOP'] = 100 * (np.log10(sum_tr / range_hl) / np.log10(14))
            
            # ADX calculation
            plus_dm = np.where((high.diff() > low.diff().abs()) & (high.diff() > 0), high.diff(), 0.0)
            minus_dm = np.where((low.diff() > high.diff()) & (low.diff() > 0), low.diff(), 0.0)
            plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=14).mean() / df['ATR'])
            minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=14).mean() / df['ATR'])
            dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
            df['ADX'] = dx.rolling(window=14).mean()
            
            # RVOL Calculation
            df['Vol_Avg20'] = volume.rolling(window=20).mean()
            df['RVOL'] = volume / df['Vol_Avg20']
            
            return df.dropna(subset=['ATR', 'CHOP', 'ADX', 'RVOL']), news_feed
    except:
        return None, []
    return None, []

# ⏱️ Caching Intraday Fine-Grained Data
@st.cache_data(ttl=60)
def fetch_intraday_data(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        # Pulling 5 days of 5-minute candles for intraday matrix formatting
        df = t_obj.history(period="5d", interval="5m")
        if df is not None and not df.empty:
            df = df.dropna(subset=['Close'])
            # Dynamic Intraday VWAP Calculation
            tp = (df['High'] + df['Low'] + df['Close']) / 3.0
            df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
            df['VWAP'] = df['VWAP'].fillna(df['Close'])
            return df
    except:
        return None
    return None

# Fetch Sector Matrix Changes with nan Safety Backstop
@st.cache_data(ttl=60)
def fetch_sector_data():
    sector_perf = {}
    for sym, name in SECTORS.items():
        try:
            tk = yf.Ticker(sym)
            h = tk.history(period="5d")
            if h is not None and len(h) >= 2:
                h = h.dropna(subset=['Close'])
                c_today = h['Close'].iloc[-1]
                c_prev = h['Close'].iloc[-2]
                
                if pd.isna(c_today) or pd.isna(c_prev) or c_prev == 0:
                    sector_perf[name] = 0.0
                else:
                    pct = ((c_today - c_prev) / c_prev) * 100
                    sector_perf[name] = pct
            else:
                sector_perf[name] = 0.0
        except:
            sector_perf[name] = 0.0
    return sector_perf

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

# 🗂️ Compile Core Data & Triggers
matrix_results = []
news_store = {}
hod_alerts = []
audio_queue = []

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
            alert_msg = f"⚡ [ALERT] {ticker} near highs. Price: ${latest['Close']:,.2f}"
            hod_alerts.append(alert_msg)
            audio_queue.append(f"{ticker} breakout alert")
            
        matrix_results.append({
            "Symbol": ticker,
            "Price": f"${latest['Close']:,.2f}",
            "RVOL": round(latest['RVOL'], 1),
            "Breakout Potential": round(comp_score, 1),
            "News State": flame_label
        })

if matrix_results:
    scanner_df = pd.DataFrame(matrix_results).sort_values(by="Breakout Potential", ascending=False)
else:
    scanner_df = pd.DataFrame(columns=["Symbol", "Price", "RVOL", "Breakout Potential", "News State"])

sector_map = fetch_sector_data()

# ----------------- LAYOUT BUILDING -----------------
col_scan, col_main = st.columns([1, 2.2])

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
    st.markdown("### 🗺️ Institutional Sector Heatmap")
    heatmap_html = "<div class='heatmap-grid'>"
    for sec_name, sec_val in sector_map.items():
        val_checked = 0.0 if (pd.isna(sec_val) or np.isnan(sec_val)) else sec_val
        bg_col = "#1c3b2b" if val_checked >= 0 else "#4a151b"
        txt_col = "#33ff99" if val_checked >= 0 else "#ff4d62"
        sign = "+" if val_checked >= 0 else ""
        heatmap_html += f"<div class='heatmap-card' style='background-color: {bg_col}; color: {txt_col};'>{sec_name}<br/>{sign}{val_checked:.2f}%</div>"
    heatmap_html += "</div>"
    st.markdown(heatmap_html, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🚨 High-Of-Day (HOD) Momentum Stream")
    if hod_alerts:
        for alert in hod_alerts:
            st.markdown(f"<div class='alert-box' style='border-left: 3px solid #00ffcc; color: #00ffcc;'>{alert}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='alert-box' style='color:#666;'>No active structural breakout prints running.</div>", unsafe_allow_html=True)

with col_main:
    st.markdown("### 🎯 Focused Command Workspace")
    focus_ticker = st.selectbox("Select Core Asset Focus to Route Terminal Visuals:", list(WATCHLIST.values()))
    
    # Fetch both data layers
    focus_data, focus_news = fetch_terminal_data(focus_ticker)
    intra_data = fetch_intraday_data(focus_ticker)
    
    if focus_data is not None and not focus_data.empty:
        latest_focus = focus_data.iloc[-1]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Last Executed Price", f"${latest_focus['Close']:,.2f}")
        m2.metric("RVOL Factor", f"{latest_focus['RVOL']:.1f}x")
        m3.metric("Structural Chop Index", f"{latest_focus['CHOP']:.2f}")
        m4.metric("ATR Band Drift", f"${latest_focus['ATR']:.2f}")
        
        st.markdown("#### 📊 Multi-Timeframe Chart Quadrants")
        
        # Quadrant Layout Grid: 2 rows of 2 columns each
        row1_c1, row1_c2 = st.columns(2)
        row2_c1, row2_c2 = st.columns(2)
        
        # --- CHART 1: Intraday 5-Min execution View with purple VWAP ---
        with row1_c1:
            if intra_data is not None and not intra_data.empty:
                # Zoom into the most recent 100 intervals for execution fidelity
                v_df = intra_data.tail(100)
                fig_5m = go.Figure()
                fig_5m.add_trace(go.Candlestick(x=v_df.index, open=v_df['Open'], high=v_df['High'], low=v_df['Low'], close=v_df['Close'], name="5m Candles"))
                fig_5m.add_trace(go.Scatter(x=v_df.index, y=v_df['VWAP'], mode='lines', line=dict(color='#b55fe6', width=2), name="VWAP"))
                fig_5m.update_layout(template="plotly_dark", title="5-Minute Tactical (with VWAP)", height=220, margin=dict(l=5, r=5, t=30, b=5), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig_5m, use_container_width=True, config={'scrollZoom': True})
            else:
                st.info("Intraday feed loading...")

        # --- CHART 2: Intraday 15-Min macro tracking trend ---
        with row1_c2:
            if intra_data is not None and not intra_data.empty:
                # Resample 5m bars to 15m intervals dynamically
                df_15m = intra_data.resample('15min').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna().tail(60)
                fig_15m = go.Figure(data=[go.Candlestick(x=df_15m.index, open=df_15m['Open'], high=df_15m['High'], low=df_15m['Low'], close=df_15m['Close'], name="15m")])
                fig_15m.update_layout(template="plotly_dark", title="15-Minute Structural Frame", height=220, margin=dict(l=5, r=5, t=30, b=5), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig_15m, use_container_width=True, config={'scrollZoom': True})
            else:
                st.info("Resampling data matrix...")

        # --- CHART 3: 30-Day Close Velocity Panel ---
        with row2_c1:
            short_df = focus_data.tail(30)
            fig_30d = go.Figure(data=[go.Scatter(x=short_df.index, y=short_df['Close'], mode='lines+markers', line=dict(color='#00ffcc'), name="30D Close")])
            fig_30d.update_layout(template="plotly_dark", title="30-Day Zoom Trend", height=220, margin=dict(l=5, r=5, t=30, b=5))
            st.plotly_chart(fig_30d, use_container_width=True, config={'scrollZoom': True})

        # --- CHART 4: 6-Month Daily Macro Support & Resistance framework ---
        with row2_c2:
            p_high = focus_data.iloc[-2]['High'] if len(focus_data) > 1 else latest_focus['High']
            p_low = focus_data.iloc[-2]['Low'] if len(focus_data) > 1 else latest_focus['Low']
            
            fig_6m = go.Figure(data=[go.Candlestick(x=focus_data.index, open=focus_data['Open'], high=focus_data['High'], low=focus_data['Low'], close=focus_data['Close'], name="Daily")])
            fig_6m.add_hline(y=p_high, line_dash="dash", line_color="#ff3366")
            fig_6m.add_hline(y=p_low, line_dash="dash", line_color="#33cc34")
            fig_6m.update_layout(template="plotly_dark", title="6-Month Macro S&R", height=220, margin=dict(l=5, r=5, t=30, b=5), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_6m, use_container_width=True, config={'scrollZoom': True})

        # 📰 CURRENT FOCUS ACTIVE NEWS FEED PANEL
        st.markdown("---")
        st.markdown("### 📰 Routed Catalyst Streaming Feed")
        if focus_news:
            valid_articles_count = 0
            for item in focus_news:
                if valid_articles_count >= 3:
                    break
                title = item.get('title') or item.get('headline')
                link = item.get('link') or item.get('url') or "#"
                publisher = item.get('publisher') or item.get('source') or "Financial Feed"
                p_time = item.get('providerPublishTime') or item.get('pubdate') or item.get('publishDate')
                
                if not title:
                    continue
                
                time_str = "Recent"
                badge, txt_col = "📁 [TRACKING]", "#888888"
                if p_time:
                    try:
                        dt_pub = datetime.fromtimestamp(int(p_time), timezone.utc)
                        time_str = dt_pub.strftime('%H:%M:%S UTC')
                        h_diff = (datetime.now(timezone.utc) - dt_pub).total_seconds() / 3600.0
                        if h_diff <= 1.0: badge, txt_col = "💥 [CRIMSON FLASH]", "#ff3333"
                        elif h_diff <= 5.0: badge, txt_col = "🔥 [ORANGE CATALYST]", "#ff9933"
                    except: pass
                    
                st.markdown(f"""
                    <div style="padding:8px; border-left: 4px solid {txt_col}; background-color: #1e1e1e; margin-bottom:6px; border-radius:4px;">
                        <span style="color: {txt_col}; font-weight:bold;">{badge} ({time_str})</span><br/>
                        <a href="{link}" target="_blank" style="color: #ffffff; font-weight:500; text-decoration:none;">{title}</a><br/>
                        <span style="color: #888888; font-size:11px;">Source: {publisher}</span>
                    </div>
                """, unsafe_allow_html=True)
                valid_articles_count += 1

# 🔊 HTML5 Speech Synthesis Injection Pipeline
if audio_queue:
    speech_phrase = " Attention. ".join(audio_queue)
    st.markdown(f"""
        <script>
            var msg = new SpeechSynthesisUtterance('{speech_phrase}');
            msg.rate = 1.1; 
            window.speechSynthesis.speak(msg);
        </script>
    """, unsafe_allow_html=True)
