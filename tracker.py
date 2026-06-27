import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go

TRENDING_REGIME = "Trending / High Efficiency"
CHOPPY_REGIME = "Choppy / Mean Reversion"

# 🔄 1. Cache the data request to prevent Yahoo Finance Rate Limits
@st.cache_data(ttl=600)
def fetch_market_data(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="6mo", interval="1d")
        if df is not None and not df.empty:
            df = df.dropna(subset=['Close'])
            df.index = pd.to_datetime(df.index).date
        return df
    except Exception as e:
        return None

# 📊 2. Technical Indicator Calculations
def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_choppiness(df, period=14):
    high = df['High'].rolling(window=period).max()
    low = df['Low'].rolling(window=period).min()
    close = df['Close']
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - close.shift(1)).abs()
    tr3 = (df['Low'] - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    sum_tr = tr.rolling(window=period).sum()
    range_high_low = high - low
    return 100 * (np.log10(sum_tr / range_high_low) / np.log10(period))

def calculate_adx(df, period=14):
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff()
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift(1)).abs()
    tr3 = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
    return dx.rolling(window=period).mean()

# 🛠️ 3. Main Streamlit Execution Flow
st.set_page_config(layout="wide") # Spreads the app out for a wide dashboard feel
st.title("📈 Macro Market Regime Radar")
st.write("Real-time structural volatility and efficiency analyzer.")

target_ticker = st.text_input("Enter Ticker to Scan:", value="SPY").upper()

with st.spinner(f"Fetching structural tape for {target_ticker}..."):
    data = fetch_market_data(target_ticker)

if data is None or data.empty:
    st.error("🚦 Market Data Portal Busy. Please refresh in a moment.")
else:
    # Run indicators
    data['ATR'] = calculate_atr(data)
    data['CHOP'] = calculate_choppiness(data)
    data['ADX'] = calculate_adx(data)
    
    clean_data = data.dropna(subset=['ATR', 'CHOP', 'ADX']).copy()
    
    # Historical Regime Mapping
    clean_data['Regime'] = np.where((clean_data['ADX'] >= 23.0) & (clean_data['CHOP'] < 50.0), TRENDING_REGIME, CHOPPY_REGIME)
    
    # Extract latest readings
    latest = clean_data.iloc[-1]
    regime = latest['Regime']
    color = "green" if regime == TRENDING_REGIME else "orange"
        
    st.markdown("---")
    st.markdown(f"### Current Market Regime: <span style='color:{color};'>{regime}</span>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Last Price", f"${latest['Close']:,.2f}")
    col2.metric("Choppiness Index", f"{latest['CHOP']:.2f}")
    col3.metric("ADX Strength", f"{latest['ADX']:.2f}")
    col4.metric("ATR Volatility", f"${latest['ATR']:.2f}")
    
    # 📊 4. Plotly Interactive Historical Timeline Chart
    st.markdown("### 📊 Historical Regime Map Timeline")
    
    fig = go.Figure()
    
    # Split historical data into segments for color-coding the line chart
    for current_regime, group_df in clean_data.groupby('Regime'):
        line_color = '#2ca02c' if current_regime == TRENDING_REGIME else '#ff7f0e'
        
        # We plot scatter markers connected by lines for each environment type
        fig.add_trace(go.Scatter(
            x=group_df.index,
            y=group_df['Close'],
            mode='markers+lines',
            name=current_regime,
            line=dict(color=line_color, width=2),
            marker=dict(size=4)
        ))
        
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        margin=dict(l=20, r=20, t=20, b=20),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show underlying data preview
    st.markdown("### Recent Technical Tape Data")
    st.dataframe(clean_data[['Close', 'ATR', 'CHOP', 'ADX', 'Regime']].tail(10), use_container_width=True)
