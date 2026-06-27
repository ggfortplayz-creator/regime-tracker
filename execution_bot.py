import time
import pandas as pd
from router import StrategyRouter

class MockExecutionBot:
    def __init__(self, initial_capital=10000.0):
        self.capital = initial_capital
        self.base_trade_size = 2000.0  
        print(f"🤖 Execution Bot Initialized | Starting Paper Bankroll: ${self.capital:,.2f}")

    def execute_momentum_strategy(self, current_price, router_engine):
        """
        Simulates a momentum strategy trying to execute a buy order.
        It must pass through the Router framework before routing to the market.
        """
        print(f"\n[Strategy Matrix] Scalper scanning tape... Current Price: ${current_price:.2f}")

        # THE SECURITY CHECK
        if not router_engine.trend_execution_allowed:
            print("❌ ORDER BLOCKED BY ENGINE: Trend trading is currently frozen due to market regime filters.")
            return False

        # THE RISK ADJUSTER
        allowed_trade_size = self.base_trade_size * router_engine.risk_multiplier
        
        print(f"✅ ORDER APPROVED: Regime allows trend entries.")
        print(f"💰 Sizing Profile: Base Size ${self.base_trade_size} x Multiplier {router_engine.risk_multiplier} = Allocation: ${allowed_trade_size:.2f}")
        
        shares = allowed_trade_size / current_price
        print(f"📦 [MOCK ORDER SENT] Bought {shares:.2f} shares of SPY at ${current_price:.2f}")
        return True

if __name__ == "__main__":
    market_router = StrategyRouter()
    bot = MockExecutionBot()
    
    print("\n🚨 Starting Defensive Stress-Test Loop (With ATR Upgrades)...")
    print("=" * 60)
    
    for cycle in range(1, 4):
        print(f"\n--- TESTING EXECUTION CYCLE {cycle} ---")
        
        if cycle == 1:
            # Cycle 1 pulls the real data (which now requires 20 days for the ATR baseline)
            market_router.run_routing_engine("SPY")
            
        elif cycle == 2:
            print("🧪 [SIMULATION] Injecting a sudden high-risk liquidity crash into the engine...")
            market_router.update_switches("Choppy / Mean Reversion")
            market_router.last_regime = "Choppy / Mean Reversion"
            
        elif cycle == 3:
            print("🧪 [SIMULATION] Injecting an absolute low-volatility drift event...")
            market_router.update_switches("Low Volatility Drifting")
            market_router.last_regime = "Low Volatility Drifting"

        mock_current_price = 540.00 
        bot.execute_momentum_strategy(mock_current_price, market_router)
        
        time.sleep(2)