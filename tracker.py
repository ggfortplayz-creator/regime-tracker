import numpy as np
import pandas as pd
import yfinance as yf

TRENDING_REGIME = "Trending / High Efficiency"
CHOPPY_REGIME = "Choppy / Mean Reversion"


def calculate_adx(df, period=14):
    """Calculates the Average Directional Index (Trend Strength)"""
    df = df.copy()
    df["H-L"] = df["High"] - df["Low"]
    df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
    df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)

    df["+DM"] = np.where(
        (df["High"] - df["High"].shift(1)) > (df["Low"].shift(1) - df["Low"]),
        np.maximum(df["High"] - df["High"].shift(1), 0),
        0,
    )
    df["-DM"] = np.where(
        (df["Low"].shift(1) - df["Low"]) > (df["High"] - df["High"].shift(1)),
        np.maximum(df["Low"].shift(1) - df["Low"], 0),
        0,
    )

    df["TR_smooth"] = df["TR"].rolling(window=period).sum()
    df["+DM_smooth"] = df["+DM"].rolling(window=period).sum()
    df["-DM_smooth"] = df["-DM"].rolling(window=period).sum()

    df["+DI"] = 100 * (df["+DM_smooth"] / df["TR_smooth"])
    df["-DI"] = 100 * (df["-DM_smooth"] / df["TR_smooth"])
    df["DX"] = 100 * (abs(df["+DI"] - df["-DI"]) / (df["+DI"] + df["-DI"]))
    df["ADX"] = df["DX"].rolling(window=period).mean()

    return df["ADX"]


def calculate_choppiness(df, period=14):
    """Calculates the Choppiness Index (Market Efficiency / Sideways Tracker)"""
    df = df.copy()
    df["H-L"] = df["High"] - df["Low"]
    df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
    df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)

    tr_sum = df["TR"].rolling(window=period).sum()
    max_high = df["High"].rolling(window=period).max()
    min_low = df["Low"].rolling(window=period).min()

    # Mathematical formula for market fractals
    chop = 100 * (
        np.log10(tr_sum / (max_high - min_low)) / np.log10(period)
    )
    return chop


def classify_regime(row):
    """Classifies the market into 1 of 4 distinct structural regimes"""
    if pd.isna(row["ADX"]) or pd.isna(row["Chop"]):
        return "Insufficient Data"

    # Thresholds: ADX > 25 is Trending. Chop > 50 or < 35 marks efficiency bounds.
    if row["ADX"] >= 23 and row["Chop"] < 50:
        return TRENDING_REGIME
    elif row["ADX"] < 20 and row["Chop"] >= 50:
        return CHOPPY_REGIME
    elif row["ADX"] >= 23 and row["Chop"] >= 50:
        return "Volatile Breakout Environment"
    else:
        return "Low Volatility Drifting"


def notify_trending_to_choppy_shift(df, window=3):
    """
    Prints a warning if the market shifted from Trending to Choppy
    within the final `window` days of data.
    """
    recent = df[["Regime"]].tail(window)
    if len(recent) < 2:
        return False

    regimes = recent["Regime"].tolist()
    dates = recent.index.tolist()

    for i in range(len(regimes) - 1):
        if regimes[i] != TRENDING_REGIME:
            continue
        for j in range(i + 1, len(regimes)):
            if regimes[j] != CHOPPY_REGIME:
                continue

            from_date = dates[i].strftime("%Y-%m-%d")
            to_date = dates[j].strftime("%Y-%m-%d")
            print(
                "\n"
                "╔══════════════════════════════════════════════════════════════╗\n"
                "║                    ⚠  REGIME SHIFT WARNING  ⚠                 ║\n"
                "╠══════════════════════════════════════════════════════════════╣\n"
                f"║  Market shifted from TRENDING → CHOPPY in the last {window} days.{' ' * (18 - len(str(window)))}║\n"
                f"║  {from_date}: {TRENDING_REGIME:<43} ║\n"
                f"║  {to_date}: {CHOPPY_REGIME:<43} ║\n"
                "║                                                              ║\n"
                "║  Action: Review trend-following exposure; mean-reversion      ║\n"
                "║  conditions may dominate near-term price action.             ║\n"
                "╚══════════════════════════════════════════════════════════════╝"
            )
            return True

    return False


# ---- RUN THE ENGINE ----
if __name__ == "__main__":
    print("Fetching historical ticker data...")
    # Fetching SPY (S&P 500 ETF) daily data for analysis
    ticker_data = yf.download("SPY", start="2025-01-01", end="2026-06-01")

    # Clean the multi-index header if present in modern yfinance formats
    if isinstance(ticker_data.columns, pd.MultiIndex):
        ticker_data.columns = ticker_data.columns.get_level_values(0)

    print("Analyzing underlying micro-structure...")
    ticker_data["ADX"] = calculate_adx(ticker_data)
    ticker_data["Chop"] = calculate_choppiness(ticker_data)
    ticker_data["Regime"] = ticker_data.apply(classify_regime, axis=1)

    notify_trending_to_choppy_shift(ticker_data)

    # Output the latest data points to view current state
    print("\n--- LATEST REGIME RESULTS ---")
    print(ticker_data[["Close", "ADX", "Chop", "Regime"]].tail(10))
