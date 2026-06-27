import time
# Import the official Alpaca Trading Client components
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Import your multi-asset macro engine
from router import StrategyRouter

# 🔑 PASTE YOUR SANDBOX KEYS HERE
ALPACA_KEY = "PK4UBGPSJ37KA3ZVZAAXW3KO4U"
ALPACA_SECRET = "7rgPShcUSkqfuhWjNLXRGGSwbk5niFUZQ9YfEzk6xGZr"

class LiveExecutionBot:
    def __init__(self):
        # Setting paper=True establishes the Sandbox Connection
        self.client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
        self.base_cash_size = 2000.0
        
        # Verify connectivity by fetching account equity
        account = self.client.get_account()
        print(f"🤖 Connected to Alpaca Sandbox Account Balance: ${float(account.equity):,.2f}")

    def execute_live_order(self, ticker, router_engine):
        """Checks the macro router switches and deploys real paper orders."""
        print(f"\n[Live Tape] Evaluator checking execution permissions for {ticker}...")
        
        # 1. Protection Check
        if not router_engine.trend_execution_allowed:
            print("❌ LIVE ENTRY DENIED: Core trend execution is frozen by the macro framework.")
            return

        # 2. Dynamic Sizing Math
        target_allocation = self.base_cash_size * router_engine.risk_multiplier
        print(f"✅ LIVE ENTRY PERMITTED | Allocating: ${target_allocation:.2f}")

        # 3. Create the real-time Market Order Payload
        order_details = MarketOrderRequest(
            symbol=ticker,
            notional=target_allocation, # Uses exact cash scaling amounts
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        
        try:
            # Send the order over the REST API to the live sandbox exchange matching engine
            submitted_order = self.client.submit_order(order_data=order_details)
            print(f"📦 [LIVE ORDER EXECUTED] ID: {submitted_order.id} | Status: {submitted_order.status}")
        except Exception as e:
            print(f"❌ Transmission Error: {e}")

if __name__ == "__main__":
    # Fire up the macro scanner engine
    macro_router = StrategyRouter()
    live_bot = LiveExecutionBot()
    
    print("\n🚀 Starting Live Engine Monitoring...")
    print("=" * 60)
    
    # Run a live test cycle
    macro_router.run_routing_engine()
    live_bot.execute_live_order("SPY", macro_router)