import pandas as pd
import numpy as np
from tracker import calculate_adx, calculate_choppiness, calculate_atr, classify_regime, yf

class RegimeBacktester:
    def __init__(self, ticker="SPY", start_date="2024-01-01", end_date="2026-06-01"):
        self.ticker = ticker
        self.start = start_date
        self.end = end_date
        self.df = None

    def load_and_prepare_data(self):
        """Pulls a deep historical dataset and processes indicators across the timeline."""
        print(f"📥 Downloading historical data for {self.ticker}...")
        self.df = yf.download(self.ticker, start=self.start, end=self.end, progress=False)
        if isinstance(self.df.columns, pd.MultiIndex): 
            self.df.columns = self.df.columns.get_level_values(0)

        # Build indicators over history
        self.df['ADX'] = calculate_adx(self.df)
        self.df['Chop'] = calculate_choppiness(self.df)
        self.df['ATR'] = calculate_atr(self.df)
        self.df['ATR_Baseline'] = self.df['ATR'].rolling(window=50).mean()
        self.df['Regime'] = self.df.apply(classify_regime, axis=1)
        
        # Calculate standard log returns of the asset
        self.df['Market_Returns'] = np.log(self.df['Close'] / self.df['Close'].shift(1))
        self.df.dropna(inplace=True)

    def run_backtest(self):
        """Simulates trading strategies based on structural regimes."""
        print("⚙️ Running backtest performance matrices...")
        
        # Strategy 1: Standard Unfiltered Momentum (Always buy/hold trend directions)
        # For simplicity, we assume a basic baseline strategy: catching everyday market motion.
        self.df['Unfiltered_Strategy'] = self.df['Market_Returns']
        
        # Strategy 2: Filtered Regime Allocation
        # If the market flips into Chop or Low Vol Drift, our router dials position sizing to zero/halved.
        self.df['Size_Multiplier'] = 1.0
        self.df.loc[self.df['Regime'] == "Choppy / Mean Reversion", 'Size_Multiplier'] = 0.5
        self.df.loc[self.df['Regime'] == "Low Volatility Drifting", 'Size_Multiplier'] = 0.0
        self.df.loc[self.df['Regime'] == "Volatile Breakout Environment", 'Size_Multiplier'] = 0.25
        
        # Calculated returns scaled dynamically by our router rules
        self.df['Regime_Filtered_Strategy'] = self.df['Market_Returns'] * self.df['Size_Multiplier']
        
        # Compound the returns over time to show final bankroll growth
        unfiltered_final = np.exp(self.df['Unfiltered_Strategy'].sum()) - 1
        filtered_final = np.exp(self.df['Regime_Filtered_Strategy'].sum()) - 1
        
        print("\n" + "="*45)
        print(f"📈 HISTORICAL PERFORMANCE RESULTS ({self.ticker})")
        print(f"Timeline: {self.start} to {self.end}")
        print("="*45)
        print(f"🔴 Unfiltered Buy/Hold Return:   {unfiltered_final*100:.2f}%")
        print(f"🟢 Regime-Filtered Return:     {filtered_final*100:.2f}%")
        
        # Drawdown preservation proof
        market_max_drop = (self.df['Close'].cummax() - self.df['Close']) / self.df['Close'].cummax()
        print(f"🛡️ Peak Historical Asset Drawdown: {market_max_drop.max()*100:.2f}%")
        print("="*45)

if __name__ == "__main__":
    # Test across the structural data timeline
    backtester = RegimeBacktester(ticker="SPY")
    backtester.load_and_prepare_data()
    backtester.run_backtest()