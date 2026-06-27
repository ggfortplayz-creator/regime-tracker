import time
import pandas as pd
# Import your calculations directly from your first tracker script
from tracker import calculate_adx, calculate_choppiness, classify_regime, yf

class StrategyRouter:
    def __init__(self):
        # Master switches your execution bots will read before taking trades
        self.trend_execution_allowed = True
        self.mean_reversion_allowed = True
        self.risk_multiplier = 1.0  # 1.0 = normal size, 0.5 = cut size in half
        self.last_regime = None

    def update_switches(self, current_regime):
        """Dynamically flips system switches based on the market state."""
        
        if current_regime == "Choppy / Mean Reversion":
            self.trend_execution_allowed = False
            self.mean_reversion_allowed = True
            self.risk_multiplier = 0.5  # Protect capital in chop
            print("🛑 [ROUTER ACTION] Trend entries FROZEN. Sizing cut to 50%. Mean Reversion ONLY.")

        elif current_regime == "Trending / High Efficiency":
            self.trend_execution_allowed = True
            self.mean_reversion_allowed = False
            self.risk_multiplier = 1.0  # Full sizing allowed
            print("🚀 [ROUTER ACTION] Trend entries ENABLED. Full position sizing allowed.")

        elif current_regime == "Volatile Breakout Environment":
            self.trend_execution_allowed = True
            self.mean_reversion_allowed = False
            self.risk_multiplier = 0.25  # High risk, scale way back
            print("⚡ [ROUTER ACTION] High Volatility Breakout! Scaling risk down to 25%.")

        elif current_regime == "Low Volatility Drifting":
            self.trend_execution_allowed = False
            self.mean_reversion_allowed = False
            self.risk_multiplier = 0.0  # Absolute halt
            print("💤 [ROUTER ACTION] Market is drifting. All entries FROZEN to avoid premium decay.")

    def run_routing_engine(self, ticker="SPY"):
        """Pulls fresh data and feeds the state machine."""
        # Fetching latest 5-minute data
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
            
        df['ADX'] = calculate_adx(df)
        df['Chop'] = calculate_choppiness(df)
        df['Regime'] = df.apply(classify_regime, axis=1)
        
        # Get the absolute newest state
        current_regime = df['Regime'].iloc[-1]
        
        # Only log or change variables if the market actually shifts states
        if current_regime != self.last_regime:
            print(f"\n🔄 REGIME SHIFT DETECTED: {self.last_regime} ➡️ {current_regime}")
            self.update_switches(current_regime)
            self.last_regime = current_regime
        else:
            print(f"⚡ Regime stable [{current_regime}]. Switches unchanged.")

if __name__ == "__main__":
    router = StrategyRouter()
    print("🚀 Starting Automated Intraday Strategy Router Engine...")
    print("Press Ctrl + C in the terminal to stop the engine at any time.\n")
    
    # Infinite loop to keep monitoring the market live
    while True:
        try:
            # Run the scanning and routing math
            router.run_routing_engine("SPY")
            
            # Pause the engine for 60 seconds before checking for the next tick/candle update
            print("⏳ Sleeping for 60 seconds before next scan...")
            time.sleep(60)
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n🛑 Strategy Router safely shut down by user.")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error encountered: {e}")
            print("Retrying in 10 seconds...")
            time.sleep(10)
    
    # Run a single production check against live asset data
    router.run_routing_engine("SPY")