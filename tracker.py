import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st

TRENDING_REGIME = "Trending / High Efficiency"
CHOPPY_REGIME = "Choppy / Mean Reversion"

# 🔄 1. Cache the data request to prevent Yahoo Finance Rate Limits and Multi-index Column Issues
@st.cache_data(ttl=600)  # Caches the data for 10 minutes
def fetch_market_data(ticker):
    try:
        # Using Ticker().history() ensures a flat, single-level column DataFrame (Open, High, Low, Close)
        ticker_obj = yf.Ticker(ticker)
        # Fetch 6 months of data to ensure indicators have enough history to stabilize accurately
        df = ticker_obj.history(period="6mo", interval="1d")
        
        if df is not None and not df.empty:
            # Drop empty placeholder rows (like weekend rows) immediately
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
    atr = tr.rolling(window=period).mean()
    return atr

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
    
    chop = 100 * (np.log10(sum_tr / range_high_low) / np.log10(period))
    return chop

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
    adx = dx.rolling(window=period).mean()
    return adx

# 🛠️ 3. Main Streamlit Execution Flow
st.title("📈 Macro Market Regime Radar")
st.write("Real-time structural volatility and efficiency analyzer.")

target_ticker = st.text_input("Enter Ticker to Scan:", value="SPY").upper()

with st.spinner(f"Fetching structural tape for {target_ticker}..."):
    data = fetch_market_data(target_ticker)

if data is None or data.empty:
    st.error("🚦 Yahoo Finance is currently rate-limiting this cloud server's IP address. Please wait a few moments and refresh the app to retry.")
else:
    st.success(f"📦 Successfully parsed data for {target_ticker}!")
    
    # Run the math engine
    data['ATR'] = calculate_atr(data)
    data['CHOP'] = calculate_choppiness(data)
    data['ADX'] = calculate_adx(data)
    
    # Double-check we drop any calculation NaN rows before grabbing metrics
    clean_data = data.dropna(subset=['ATR', 'CHOP', 'ADX'])
    
    # Extract latest valid readings
    latest_chop = float(clean_data['CHOP'].iloc[-1])
    latest_adx = float(clean_data['ADX'].iloc[-1])
    latest_atr = float(clean_data['ATR'].iloc[-1])
    latest_price = float(clean_data['Close'].iloc[-1])
    
    # Classify State
    if latest_adx >= 23.0 and latest_chop < 50.0:
        regime = TRENDING_REGIME
        color = "green"
    else:
        regime = CHOPPY_REGIME
        color = "orange"
        
    # 🖥️ Render beautiful UI Cards
    st.markdown("---")
    st.markdown(f"### Current Market Regime: <span style='color:{color};'>{regime}</span>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Last Price", f"${latest_price:,.2f}")
    col2.metric("Choppiness Index", f"{latest_chop:.2f}")
    col3.metric("ADX Strength", f"{latest_adx:.2f}")
    col4.metric("ATR Volatility", f"${latest_atr:.2f}")
    
    # Show underlying data preview
    st.markdown("### Recent Technical Tape Data")
    st.dataframe(clean_data[['Close', 'ATR', 'CHOP', 'ADX']].tail(10))
