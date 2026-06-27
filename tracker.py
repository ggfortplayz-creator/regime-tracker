import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go

# 🏢 Page Config
st.set_page_config(layout="wide", page_title="Macro Volatility Pulse")
st.title("⚡ Macro Volatility Pulse & Breakout Radar")
st.write("Tracking institutional capital compression and regime shifts across global asset classes.")

# 📋 The Elite Watchlist (Spanning global macro cross-currents)
WATCHLIST = {
    "S&P 500 (Market Core)": "SPY",
    "Nasdaq 100 (Tech/Growth)": "QQQ",
    "Russell 2000 (Risk-On Small Caps)": "IWM",
    "Bitcoin (Digital Liquidity)": "BTC-USD",
    "Gold (Safe Haven/Inflation)": "GLD",
    "Crude Oil (Energy/Commodity)": "USO",
    "Treasury Bonds (Fixed Income Vol)": "TLT"
}

# 🔄 Caching Core Math Data
@st.cache_data(ttl=900)
def fetch_matrix_data(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="6mo", interval="1d")
        if df is not None and not df.empty:
            df = df.dropna(subset=['Close'])
            # Basic calculation variables
            high, low, close = df['High'], df['Low'], df['Close']
            close_prev = close.shift(1)
            
            # 1. True Range & ATR
            tr = pd.concat([high - low, (high - close_prev).abs(), (low - close_prev).abs()], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=14).mean()
            
            # 2. Choppiness Index
            sum_tr = tr.rolling(window=14).sum()
            range_hl = high.rolling(window=14).max() - low.rolling(window=14).min()
            df['CHOP'] = 100 * (np.log10(sum_tr / range_hl) / np.log10(14))
            
            # 3. Directional Movement Index (Simplified ADX)
            plus_dm = np.where((high.diff() > low.diff().abs()) & (high.diff() > 0), high.diff(), 0.0)
            minus_dm = np.where((low.diff() > high.diff()) & (low.diff() > 0), low.diff(), 0.0)
            plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=14).mean() / df['ATR'])
            minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=14).mean() / df['ATR'])
            dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
            df['ADX'] = dx.rolling(window=14).mean()
            
            return df.dropna(subset=['ATR', 'CHOP', 'ADX'])
    except:
        return None
    return None

# 🚀 Compile Matrix Metrics
matrix_results = []

with st.spinner("Analyzing institutional market matrix..."):
    for name, ticker in WATCHLIST.items():
        data = fetch_matrix_data(ticker)
        if data is not None and not data.empty:
            latest = data.iloc[-1]
            
            # Math logic for Explosion/Compression Potential
            # High Chop + Low ADX = High Compression (Coiled Spring)
            compression_score = (latest['CHOP'] * 1.5) - (latest['ADX'] * 0.5)
            compression_score = max(0.0, min(100.0, compression_score)) # Bound it 0-100
            
            # Structural Regime Classification
            if latest['ADX'] >= 23.0 and latest['CHOP'] < 50.0:
                regime = "🎯 Trending / Efficient"
                action_playbook = "Trend-Follow (Buy breakouts/chase momentum)"
            elif latest['CHOP'] >= 58.0:
                regime = "⚡ High Compression Squeeze"
                action_playbook = "Alert: Coiled Spring (Deploy breakout straddles)"
            else:
                regime = "🔄 Choppy / Mean Reverting"
                action_playbook = "Range-Trade (Buy support, sell resistance)"
                
            matrix_results.append({
                "Asset Group": name,
                "Ticker": ticker,
                "Current Price": f"${latest['Close']:,.2f}",
                "Trend Strength (ADX)": round(latest['ADX'], 2),
                "Consolidation (CHOP)": round(latest['CHOP'], 2),
                "Breakout Potential %": round(compression_score, 1),
                "Market Structure": regime,
                "Recommended Tactical Playbook": action_playbook
            })

# Convert compile to clean DataFrame
matrix_df = pd.DataFrame(matrix_results).sort_values(by="Breakout Potential %", ascending=False)

# 🖥️ Render Dashboard Front-end
st.markdown("---")
st.subheader("🚨 Institutional Expansion Leaderboard")
st.write("Assets ranked by **Breakout Potential**. High percentage readings highlight compressed asset frameworks primed for structural expansion.")

# Highlight or style data frame column outputs beautifully
st.dataframe(
    matrix_df, 
    column_config={
        "Breakout Potential %": st.column_config.ProgressColumn(
            "Breakout Potential %",
            help="Higher scores signify deeply coiled volatility ranges primed to break out.",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        )
    },
    use_container_width=True,
    hide_index=True
)

# 📊 Visual Focus Interactive Chart Module
st.markdown("---")
st.subheader("🔍 Single Asset Deep Dive Diagnostic")
selected_asset = st.selectbox("Select Target Framework to Visualize:", list(WATCHLIST.keys()))
target_ticker = WATCHLIST[selected_asset]

plot_df = fetch_matrix_data(target_ticker)
if plot_df is not None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['Close'], name='Price', line=dict(color='#00ffcc', width=2)))
    fig.update_layout(
        template="plotly_dark", 
        title=f"{selected_asset} ({target_ticker}) Price Structure Tracker",
        xaxis_title="Timeline", yaxis_title="Price ($)", height=350,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
