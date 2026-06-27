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
        df = ticker_obj.history(period="3mo", interval="1d")
        
        # Clean up index format for the Streamlit tables
        if df is not None and not df.empty:
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

if data is None or data
