import pandas as pd
import sys
import os

# Ensure we can import locally
sys.path.append('/Users/misrori/codes/goldhand')

try:
    from goldhand import GoldHand
    from goldhand.strategies import show_indicator_goldhand_line_strategy, show_indicator_rsi_strategy
    from goldhand.data import Data
    
    print("Imports successful.")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_goldhand_basic():
    print("\n--- Testing GoldHand Basic ---")
    gh = GoldHand('AAPL', range='1y')
    
    if gh.df is None or gh.df.empty:
        print("ERROR: DataFrame is empty.")
        return False
        
    print(f"Data downloaded. Shape: {gh.df.shape}")
    print(f"Columns: {gh.df.columns.tolist()}")
    
    if 'rsi' not in gh.df.columns:
        print("ERROR: RSI not calculated.")
        return False
        
    if 'sma_50' not in gh.df.columns:
        print("ERROR: SMA not calculated.")
        return False
        
    print("Indicators calculated successfully.")
    
    fig = gh.plotly_last_year("Test Plot")
    if fig is None:
        print("ERROR: Plotly figure not created.")
        return False
    print("Plotly figure created.")
    return True

def test_strategies():
    print("\n--- Testing Strategies ---")
    try:
        # Test GoldHand Line
        print("Testing GoldHand Line Strategy...")
        fig_gh = show_indicator_goldhand_line_strategy('AAPL', plot_title='GH Line Test', ndays=100, add_strategy_summary=False)
        if fig_gh is None:
             print("Warning: show_indicator_goldhand_line_strategy returned None (might differ based on implementation return type).")
        else:
             print("GH Line Strategy plot created.")
             
        # Test RSI
        print("Testing RSI Strategy...")
        fig_rsi = show_indicator_rsi_strategy('AAPL', plot_title='RSI Test', ndays=100, add_strategy_summary=False)
        if fig_rsi is None:
             print("Warning: show_indicator_rsi_strategy returned None.")
        else:
             print("RSI Strategy plot created.")

        # Test Adaptive Trend V3
        print("Testing Adaptive Trend V3 Strategy...")
        from goldhand.strategies import show_indicator_adaptive_trend_strategy
        fig_adaptive = show_indicator_adaptive_trend_strategy('BTC-USD', is_crypto=True, plot_title='Adaptive Test', ndays=100)
        if fig_adaptive is None:
             print("Warning: show_indicator_adaptive_trend_strategy returned None.")
        else:
             print("Adaptive Trend Strategy plot created.")
             
        return True
    except Exception as e:
        print(f"Strategy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = True
    if not test_goldhand_basic():
        success = False
    
    if not test_strategies():
        success = False
        
    if success:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed.")
        sys.exit(1)
