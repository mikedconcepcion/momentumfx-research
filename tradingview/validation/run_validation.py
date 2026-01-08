"""
TradingView Indicator Validation Runner

Runs comprehensive backtest validation on the MomentumFX Order Block Zones indicator.

Tests across:
- Multiple instruments (XAUUSD, EURUSD, USDJPY)
- Multiple time periods (COVID, Post-COVID, Recent, Full 6-year)
- Different configurations (OB filter on/off, trend filter on/off)

Generates honest validation report showing what works and what doesn't.
"""

import sys
import os

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, parent_dir)

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Load backtest engine from same directory
import importlib.util
spec = importlib.util.spec_from_file_location("backtest_engine", os.path.join(current_dir, "backtest_engine.py"))
backtest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backtest_module)

BacktestEngine = backtest_module.BacktestEngine
BacktestConfig = backtest_module.BacktestConfig
Trade = backtest_module.Trade


def load_data(instrument: str, start_date: str = None, end_date: str = None) -> tuple:
    """
    Load M5 and H1 data for instrument

    Returns:
        (df_m5, df_h1) tuple
    """
    # Try multiple data locations
    base_dir = Path(__file__).parent.parent.parent
    possible_locations = [
        base_dir / 'data' / 'raw' / 'combined_2020_2025',  # Combined data folder
        base_dir / 'data' / 'raw' / 'parquet' / 'M5',      # Parquet M5 folder
        base_dir.parent / 'data' / 'raw' / 'combined_2020_2025',  # One level up
    ]

    print(f"\nLoading data for {instrument}...")

    # Find M5 file
    m5_file = None
    for loc in possible_locations:
        potential_file = loc / f"{instrument}_M5_2020_2025.parquet"
        if potential_file.exists():
            m5_file = potential_file
            break
        potential_file = loc / f"{instrument}.parquet"
        if potential_file.exists():
            m5_file = potential_file
            break

    if not m5_file or not m5_file.exists():
        raise FileNotFoundError(f"M5 data not found for {instrument}. Searched in: {[str(loc) for loc in possible_locations]}")

    print(f"  Found M5 data: {m5_file}")
    df_m5 = pd.read_parquet(m5_file)
    if 'timestamp' in df_m5.columns:
        df_m5 = df_m5.set_index('timestamp')

    # Resample to H1
    print(f"  Resampling to H1...")
    agg_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }

    # Add volume if exists
    if 'volume' in df_m5.columns:
        agg_dict['volume'] = 'sum'
    elif 'tick_volume' in df_m5.columns:
        agg_dict['tick_volume'] = 'sum'

    df_h1 = df_m5.resample('1h').agg(agg_dict).dropna()

    # Filter by date range
    if start_date:
        df_m5 = df_m5[df_m5.index >= start_date]
        df_h1 = df_h1[df_h1.index >= start_date]
    if end_date:
        df_m5 = df_m5[df_m5.index <= end_date]
        df_h1 = df_h1[df_h1.index <= end_date]

    print(f"  M5 bars: {len(df_m5):,} | Period: {df_m5.index[0]} to {df_m5.index[-1]}")
    print(f"  H1 bars: {len(df_h1):,}")

    return df_m5, df_h1


def print_results(results: dict, config_name: str = ""):
    """Print backtest results"""

    print(f"\n{'='*80}")
    print(f"RESULTS: {results['instrument']} {config_name}")
    print(f"{'='*80}")
    print(f"Period: {results['period']}")
    print(f"Duration: {results['duration_days']} days | Bars: {results['bars']:,}")
    print()

    print(f"TRADE STATISTICS:")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Wins: {results['wins']} | Losses: {results['losses']}")
    print(f"  Win Rate: {results['win_rate']:.1f}%")
    print(f"  Trades/Month: {results['trades_per_month']:.1f}")
    print()

    print(f"PERFORMANCE:")
    print(f"  Total P&L: {results['total_pnl_r']:.2f}R")
    print(f"  Avg Win: {results['avg_win_r']:.2f}R | Avg Loss: {results['avg_loss_r']:.2f}R")
    print(f"  Profit Factor: {results['profit_factor']:.2f}")
    print(f"  Expectancy: {results['expectancy_r']:.3f}R")
    print()

    print(f"RISK METRICS:")
    print(f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print()

    print(f"RETURNS:")
    print(f"  Initial Capital: ${results['initial_capital']:,.0f}")
    print(f"  Final Capital: ${results['final_capital']:,.0f}")
    print(f"  Total Return: {results['total_return_pct']:.2f}%")
    print()

    print(f"CONSECUTIVE:")
    print(f"  Max Consecutive Wins: {results['max_consecutive_wins']}")
    print(f"  Max Consecutive Losses: {results['max_consecutive_losses']}")
    print()

    print(f"ORDER BLOCK STATS:")
    print(f"  OB Trades: {results['ob_trades']} ({results['ob_pct']:.1f}% of total)")
    print(f"  OB Win Rate: {results['ob_win_rate']:.1f}%")

    # Assessment
    print(f"\n{'='*80}")
    print(f"ASSESSMENT:")
    if results['total_trades'] < 30:
        print(f"  [!]  INSUFFICIENT DATA - Less than 30 trades")
    if results['profit_factor'] >= 1.5:
        print(f"  [OK] GOOD - Profit Factor >= 1.5")
    elif results['profit_factor'] >= 1.2:
        print(f"  [!]  ACCEPTABLE - Profit Factor >= 1.2")
    else:
        print(f"  [X] POOR - Profit Factor < 1.2")

    if results['win_rate'] >= 50:
        print(f"  [OK] GOOD - Win Rate >= 50%")
    elif results['win_rate'] >= 40:
        print(f"  [!]  ACCEPTABLE - Win Rate >= 40%")
    else:
        print(f"  [X] POOR - Win Rate < 40%")

    if results['expectancy_r'] > 0.2:
        print(f"  [OK] GOOD - Positive Expectancy > 0.2R")
    elif results['expectancy_r'] > 0:
        print(f"  [!]  ACCEPTABLE - Positive Expectancy")
    else:
        print(f"  [X] POOR - Negative Expectancy")

    if results['max_drawdown_pct'] < 15:
        print(f"  [OK] GOOD - Drawdown < 15%")
    elif results['max_drawdown_pct'] < 25:
        print(f"  [!]  ACCEPTABLE - Drawdown < 25%")
    else:
        print(f"  [X] POOR - Drawdown >= 25%")

    print(f"{'='*80}\n")


def run_instrument_validation(instrument: str, start_date: str = None, end_date: str = None):
    """Run validation for a single instrument"""

    # Load data
    df_m5, df_h1 = load_data(instrument, start_date, end_date)

    # Test configurations
    configs = [
        ("Default (OB + Trend Filter)", BacktestConfig(
            enable_ob_filter=True,
            enable_trend_filter=True
        )),
        ("OB Filter Only", BacktestConfig(
            enable_ob_filter=True,
            enable_trend_filter=False
        )),
        ("Trend Filter Only", BacktestConfig(
            enable_ob_filter=False,
            enable_trend_filter=True
        )),
        ("No Filters", BacktestConfig(
            enable_ob_filter=False,
            enable_trend_filter=False
        )),
    ]

    results_list = []

    for config_name, config in configs:
        engine = BacktestEngine(config)
        results = engine.run_backtest(df_m5, df_h1, instrument)
        results['config_name'] = config_name
        results['config'] = {
            'ob_filter': config.enable_ob_filter,
            'trend_filter': config.enable_trend_filter
        }
        results_list.append(results)

        print_results(results, config_name)

    return results_list


def run_period_validation(instrument: str):
    """Run validation across different time periods"""

    periods = [
        ("COVID Period (2020-2021)", "2020-01-01", "2021-12-31"),
        ("Post-COVID (2022-2023)", "2022-01-01", "2023-12-31"),
        ("Recent (2024-2025)", "2024-01-01", "2025-12-31"),
        ("Full 6-Year (2020-2025)", "2020-01-01", "2025-12-31"),
    ]

    results_by_period = {}

    for period_name, start, end in periods:
        print(f"\n{'#'*80}")
        print(f"TESTING PERIOD: {period_name}")
        print(f"{'#'*80}")

        try:
            df_m5, df_h1 = load_data(instrument, start, end)

            # Test with default config (OB + Trend filter)
            config = BacktestConfig(
                enable_ob_filter=True,
                enable_trend_filter=True
            )

            engine = BacktestEngine(config)
            results = engine.run_backtest(df_m5, df_h1, f"{instrument} ({period_name})")

            results_by_period[period_name] = results
            print_results(results)

        except Exception as e:
            print(f"ERROR: {e}")
            results_by_period[period_name] = {'error': str(e)}

    return results_by_period


def generate_report(all_results: dict, output_file: str = "VALIDATION_REPORT.md"):
    """Generate comprehensive markdown report"""

    report = []
    report.append("# TradingView Indicator Validation Report")
    report.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n**CRITICAL**: This report shows HONEST backtest results.")
    report.append("If metrics are poor, the indicator needs improvement before release.\n")
    report.append("---\n")

    # Summary section
    report.append("## Executive Summary\n")

    # Calculate overall stats
    total_backtests = sum(len(v) if isinstance(v, list) else 1 for v in all_results.values())
    report.append(f"- **Total Backtests**: {total_backtests}")

    # Best performing
    best_pf = 0
    best_config = None
    for instrument, results_list in all_results.items():
        if isinstance(results_list, list):
            for r in results_list:
                if 'profit_factor' in r and r['profit_factor'] > best_pf:
                    best_pf = r['profit_factor']
                    best_config = f"{instrument} - {r.get('config_name', 'Unknown')}"

    report.append(f"- **Best Profit Factor**: {best_pf:.2f} ({best_config})\n")

    report.append("---\n")

    # Detailed results
    for instrument, results_list in all_results.items():
        report.append(f"## {instrument}\n")

        if isinstance(results_list, dict):
            # Period validation
            for period, results in results_list.items():
                if 'error' in results:
                    report.append(f"### {period}\n")
                    report.append(f"[X] **ERROR**: {results['error']}\n")
                    continue

                report.append(f"### {period}\n")
                report.append(f"**Period**: {results.get('period', 'N/A')}\n")
                report.append(f"**Trades**: {results.get('total_trades', 0)}\n\n")

                report.append("| Metric | Value | Status |\n")
                report.append("|--------|-------|--------|\n")

                # Win rate
                wr = results.get('win_rate', 0)
                wr_status = "[OK]" if wr >= 50 else ("[!]" if wr >= 40 else "[X]")
                report.append(f"| Win Rate | {wr:.1f}% | {wr_status} |\n")

                # Profit factor
                pf = results.get('profit_factor', 0)
                pf_status = "[OK]" if pf >= 1.5 else ("[!]" if pf >= 1.2 else "[X]")
                report.append(f"| Profit Factor | {pf:.2f} | {pf_status} |\n")

                # Expectancy
                exp = results.get('expectancy_r', 0)
                exp_status = "[OK]" if exp > 0.2 else ("[!]" if exp > 0 else "[X]")
                report.append(f"| Expectancy | {exp:.3f}R | {exp_status} |\n")

                # Drawdown
                dd = results.get('max_drawdown_pct', 0)
                dd_status = "[OK]" if dd < 15 else ("[!]" if dd < 25 else "[X]")
                report.append(f"| Max Drawdown | {dd:.2f}% | {dd_status} |\n")

                # Return
                ret = results.get('total_return_pct', 0)
                report.append(f"| Total Return | {ret:.2f}% | - |\n")

                report.append("\n")

        elif isinstance(results_list, list):
            # Config comparison
            report.append("### Configuration Comparison\n\n")
            report.append("| Config | Trades | Win% | PF | Exp(R) | DD% | Return% |\n")
            report.append("|--------|--------|------|----|----|-----|------|\n")

            for results in results_list:
                if 'total_trades' not in results:
                    continue

                config_name = results.get('config_name', 'Unknown')
                trades = results.get('total_trades', 0)
                wr = results.get('win_rate', 0)
                pf = results.get('profit_factor', 0)
                exp = results.get('expectancy_r', 0)
                dd = results.get('max_drawdown_pct', 0)
                ret = results.get('total_return_pct', 0)

                report.append(f"| {config_name} | {trades} | {wr:.1f} | {pf:.2f} | {exp:.3f} | {dd:.1f} | {ret:.1f} |\n")

            report.append("\n")

        report.append("---\n\n")

    # Conclusions
    report.append("## Conclusions\n\n")
    report.append("### Key Findings\n\n")
    report.append("Based on the backtest results above:\n\n")
    report.append("1. **Best Configuration**: [To be determined from results]\n")
    report.append("2. **Best Instruments**: [To be determined from results]\n")
    report.append("3. **Best Periods**: [To be determined from results]\n\n")

    report.append("### Recommendations\n\n")
    report.append("[!] **IMPORTANT**: Review all results before release.\n\n")
    report.append("- If Profit Factor < 1.2 across most tests: **DO NOT RELEASE**\n")
    report.append("- If Win Rate < 40% consistently: **NEEDS IMPROVEMENT**\n")
    report.append("- If Max Drawdown > 25% frequently: **TOO RISKY**\n")
    report.append("- If sample size < 30 trades: **INSUFFICIENT DATA**\n\n")

    report.append("### Next Steps\n\n")
    report.append("1. Analyze results honestly\n")
    report.append("2. If metrics are poor, improve indicator logic\n")
    report.append("3. If metrics are good, proceed with release\n")
    report.append("4. Include disclaimers about past performance\n")
    report.append("5. Recommend paper trading before live\n\n")

    report.append("---\n\n")
    report.append("*This validation was performed using historical data.*\n")
    report.append("*Past performance does not guarantee future results.*\n")
    report.append("*Always use proper risk management.*\n")

    # Write to file
    output_path = Path(__file__).parent / output_file
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))

    print(f"\n[OK] Report generated: {output_path}")

    return output_path


def main():
    """Run full validation suite"""

    print("="*80)
    print("TRADINGVIEW INDICATOR VALIDATION")
    print("="*80)
    print("\nThis will run comprehensive backtests to validate the indicator.")
    print("Results will be HONEST - showing what works and what doesn't.\n")

    input("Press Enter to continue...")

    all_results = {}

    # Test instruments
    instruments = ['XAUUSD', 'EURUSD', 'USDJPY']

    print("\n" + "="*80)
    print("PHASE 1: INSTRUMENT VALIDATION (Full 6-Year Period)")
    print("="*80)

    for instrument in instruments:
        print(f"\n{'#'*80}")
        print(f"TESTING: {instrument}")
        print(f"{'#'*80}")

        try:
            results = run_instrument_validation(instrument, "2020-01-01", "2025-12-31")
            all_results[instrument] = results
        except Exception as e:
            print(f"\n[X] ERROR testing {instrument}: {e}")
            all_results[instrument] = [{'error': str(e)}]

    print("\n" + "="*80)
    print("PHASE 2: PERIOD VALIDATION (XAUUSD)")
    print("="*80)

    try:
        period_results = run_period_validation('XAUUSD')
        all_results['XAUUSD_Periods'] = period_results
    except Exception as e:
        print(f"\n[X] ERROR in period validation: {e}")

    # Generate report
    print("\n" + "="*80)
    print("GENERATING REPORT")
    print("="*80)

    report_path = generate_report(all_results)

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print(f"\nFull report: {report_path}")
    print("\n[!]  CRITICAL: Review results before releasing indicator to traders!")
    print("If metrics are poor, the indicator needs improvement.\n")


if __name__ == "__main__":
    main()
