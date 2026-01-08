"""Quick test of the backtesting system"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from run_validation import load_data, print_results
import importlib.util

# Load backtest engine
spec = importlib.util.spec_from_file_location("backtest_engine", os.path.join(current_dir, "backtest_engine.py"))
backtest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backtest_module)

BacktestEngine = backtest_module.BacktestEngine
BacktestConfig = backtest_module.BacktestConfig

print("="*80)
print("QUICK VALIDATION TEST - XAUUSD (2024-2025)")
print("="*80)

# Load data
df_m5, df_h1 = load_data('XAUUSD', '2024-01-01', '2025-12-31')

# Create config
config = BacktestConfig(
    enable_ob_filter=True,
    enable_trend_filter=True
)

# Run backtest
engine = BacktestEngine(config)
results = engine.run_backtest(df_m5, df_h1, "XAUUSD (2024-2025)")

# Print results
print_results(results, "OB + Trend Filter")

print("\n" + "="*80)
print("QUICK TEST COMPLETE")
print("="*80)

# Save summary
if results['total_trades'] > 0:
    print(f"\nSUMMARY:")
    print(f"  Trades: {results['total_trades']}")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Profit Factor: {results['profit_factor']:.2f}")
    print(f"  Expectancy: {results['expectancy_r']:.3f}R")
    print(f"  Max DD: {results['max_drawdown_pct']:.2f}%")
    print(f"  Return: {results['total_return_pct']:.2f}%")

    if results['profit_factor'] >= 1.2 and results['win_rate'] >= 40:
        print(f"\n[OK] Indicator shows promise! Run full validation.")
    else:
        print(f"\n[!] Warning: Indicator metrics below minimum. Needs improvement.")
else:
    print("\n[X] ERROR: No trades generated. Check indicator logic.")
