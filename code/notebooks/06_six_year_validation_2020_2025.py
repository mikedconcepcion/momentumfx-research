"""
Six-Year Extended Multi-Instrument Validation (2020-2025)

This script provides the most robust validation to date:
- 6-year dataset including COVID-19 period (2020-2021)
- Multiple complete market cycles
- Extreme volatility events (COVID crash March 2020)
- Post-COVID normalization and rate hike cycles
- Current market conditions (2024-2025)

Period: January 1, 2020 - December 31, 2025 (6 years)
Purpose: Ultimate regime-robustness test including extreme events

Data Source: Dukascopy Bank SA (https://www.dukascopy.com)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import json

from data.data_loader import DataLoader
from zones.detector import ZoneDetector, ZoneType, ZoneFreshness
from zones.time_filter import PeriodicOBFilter, SessionFilter
from strategies.trend_analyzer import TrendAnalyzer, MultiTimeframeTrend

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 140)

print("="*120)
print("SIX-YEAR EXTENDED MULTI-INSTRUMENT VALIDATION (2020-2025)")
print("Ultimate Robustness Test - Including COVID-19 Period and Multiple Market Cycles")
print("="*120)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Data Source: Dukascopy Bank SA")
print("="*120)

# ============================================================================
# CONFIGURATION
# ============================================================================
INSTRUMENTS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAUUSD",
    "BTCUSD",
]

# Full 6-year period (2020-2025)
FULL_START = "2020-01-01"
FULL_END = "2025-12-31"

# Comparison periods
PERIODS = {
    "covid": ("2020-01-01", "2021-12-31"),  # COVID period
    "post_covid": ("2022-01-01", "2023-12-31"),  # Post-COVID
    "recent": ("2024-01-01", "2025-12-31"),  # Recent
    "full": (FULL_START, FULL_END),  # Full 6 years
}

TIMEFRAMES = ["M5", "M15", "H1"]

ZONE_PARAMS = {
    'lookback_periods': 100,
    'min_consolidation_candles': 2,
    'zone_width_atr': 0.5,
    'min_velocity_atr': 0.5,
    'freshness_max_age': 50
}

OB_PARAMS = {
    'hourly_window_mins': 5,
    'half_hour_window_mins': 3
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def analyze_period(instrument: str, start_date: str, end_date: str, period_name: str) -> Dict:
    """Analyze a single instrument for a specific period"""
    try:
        # Load data
        loader = DataLoader()
        df = loader.load(instrument, "M5", start_date, end_date)

        if df.empty:
            print(f"  [WARN] No data for {instrument} in period {period_name}")
            return None

        # Detect zones
        detector = ZoneDetector(**ZONE_PARAMS)
        zones = detector.detect_zones(df)

        if not zones:
            print(f"  [WARN] No zones detected for {instrument} in period {period_name}")
            return {
                'instrument': instrument,
                'period': period_name,
                'start': start_date,
                'end': end_date,
                'bars': len(df),
                'zones': 0,
                'ob_zones': 0,
                'ob_pct': 0.0,
                'concentration': 0.0,
            }

        # Classify by OB time
        ob_filter = PeriodicOBFilter(**OB_PARAMS)
        ob_zones = sum(1 for z in zones if ob_filter.is_ob_time(z.creation_time))

        # Calculate metrics
        total_zones = len(zones)
        ob_pct = (ob_zones / total_zones * 100) if total_zones > 0 else 0
        concentration = ob_pct / 33.3  # vs 33.3% baseline

        # Quarterly breakdown
        df_zones = pd.DataFrame([{
            'timestamp': z.creation_time,
            'type': z.zone_type.name,
            'is_ob': ob_filter.is_ob_time(z.creation_time)
        } for z in zones])

        df_zones['quarter'] = pd.to_datetime(df_zones['timestamp']).dt.to_period('Q')
        quarterly = df_zones.groupby('quarter').size().to_dict()

        return {
            'instrument': instrument,
            'period': period_name,
            'start': start_date,
            'end': end_date,
            'bars': len(df),
            'zones': total_zones,
            'ob_zones': ob_zones,
            'non_ob_zones': total_zones - ob_zones,
            'ob_pct': ob_pct,
            'concentration': concentration,
            'quarterly': {str(k): v for k, v in quarterly.items()},
            'supply_zones': sum(1 for z in zones if z.zone_type == ZoneType.SUPPLY),
            'demand_zones': sum(1 for z in zones if z.zone_type == ZoneType.DEMAND),
        }

    except Exception as e:
        print(f"  [ERROR] Failed to analyze {instrument} {period_name}: {e}")
        return None

def print_period_results(results: List[Dict], period_name: str):
    """Print formatted results for a period"""
    print(f"\n{'='*120}")
    print(f"{period_name.upper()} PERIOD RESULTS")
    print(f"{'='*120}")

    if not results:
        print("[WARN] No results to display")
        return

    # Summary table
    print(f"\n{'Instrument':<12} {'Bars':>10} {'Zones':>8} {'In OB':>8} {'OB %':>8} {'Conc.':>8} {'Supply':>8} {'Demand':>8}")
    print("-" * 120)

    total_bars = 0
    total_zones = 0
    total_ob = 0

    for r in results:
        if r is None:
            continue

        print(f"{r['instrument']:<12} {r['bars']:>10,} {r['zones']:>8} {r['ob_zones']:>8} "
              f"{r['ob_pct']:>7.1f}% {r['concentration']:>7.2f}x "
              f"{r['supply_zones']:>8} {r['demand_zones']:>8}")

        total_bars += r['bars']
        total_zones += r['zones']
        total_ob += r['ob_zones']

    print("-" * 120)

    if total_zones > 0:
        avg_ob_pct = (total_ob / total_zones * 100)
        avg_conc = avg_ob_pct / 33.3
        print(f"{'TOTAL':<12} {total_bars:>10,} {total_zones:>8} {total_ob:>8} "
              f"{avg_ob_pct:>7.1f}% {avg_conc:>7.2f}x")

    # Chi-square test
    if total_zones > 0:
        expected_ob = total_zones * 0.333
        chi_square = ((total_ob - expected_ob)**2 / expected_ob +
                     ((total_zones - total_ob) - (total_zones * 0.667))**2 / (total_zones * 0.667))
        print(f"\nChi-Square Test: X^2 = {chi_square:.2f}, p < 0.001" if chi_square > 10.83 else f"\nChi-Square Test: X^2 = {chi_square:.2f}, not significant")

def compare_periods(all_results: Dict):
    """Compare results across different periods"""
    print(f"\n{'='*120}")
    print("CROSS-PERIOD COMPARISON")
    print(f"{'='*120}")

    print(f"\n{'Period':<15} {'Years':>8} {'Bars':>12} {'Zones':>8} {'OB %':>8} {'Conc.':>8} {'p-value':>10}")
    print("-" * 120)

    for period_name, results in all_results.items():
        if not results:
            continue

        total_bars = sum(r['bars'] for r in results if r)
        total_zones = sum(r['zones'] for r in results if r)
        total_ob = sum(r['ob_zones'] for r in results if r)

        if total_zones == 0:
            continue

        ob_pct = (total_ob / total_zones * 100)
        conc = ob_pct / 33.3

        # Calculate years
        start = PERIODS[period_name][0]
        end = PERIODS[period_name][1]
        years = (pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25

        # Chi-square p-value approximation
        expected_ob = total_zones * 0.333
        chi_square = ((total_ob - expected_ob)**2 / expected_ob +
                     ((total_zones - total_ob) - (total_zones * 0.667))**2 / (total_zones * 0.667))
        p_value = "< 0.001" if chi_square > 10.83 else "> 0.05"

        print(f"{period_name:<15} {years:>8.1f} {total_bars:>12,} {total_zones:>8} "
              f"{ob_pct:>7.1f}% {conc:>7.2f}x {p_value:>10}")

def instrument_comparison(all_results: Dict):
    """Compare instruments across all periods"""
    print(f"\n{'='*120}")
    print("INSTRUMENT STABILITY ANALYSIS")
    print(f"{'='*120}")

    print(f"\n{'Instrument':<12} {'COVID':>10} {'Post-COVID':>12} {'Recent':>10} {'Full-6Y':>10} {'Stability':>12}")
    print("-" * 120)

    for instrument in INSTRUMENTS:
        concentrations = []
        for period_name in ["covid", "post_covid", "recent", "full"]:
            results = all_results.get(period_name, [])
            inst_result = next((r for r in results if r and r['instrument'] == instrument), None)
            if inst_result and inst_result['zones'] > 0:
                concentrations.append(inst_result['concentration'])
            else:
                concentrations.append(0.0)

        if all(c == 0.0 for c in concentrations):
            continue

        # Calculate stability (lower std dev = more stable)
        non_zero = [c for c in concentrations if c > 0]
        if len(non_zero) >= 2:
            stability = np.std(non_zero)
            stability_rating = "Excellent" if stability < 0.3 else "Good" if stability < 0.5 else "Moderate" if stability < 0.8 else "Poor"
        else:
            stability = 0.0
            stability_rating = "Insufficient"

        print(f"{instrument:<12} {concentrations[0]:>9.2f}x {concentrations[1]:>11.2f}x "
              f"{concentrations[2]:>9.2f}x {concentrations[3]:>9.2f}x {stability_rating:>12}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\nStarting 6-year validation...")

    all_results = {}

    # Analyze each period
    for period_name, (start, end) in PERIODS.items():
        print(f"\n{'='*120}")
        print(f"ANALYZING PERIOD: {period_name.upper()} ({start} to {end})")
        print(f"{'='*120}")

        period_results = []
        for instrument in INSTRUMENTS:
            print(f"\nProcessing {instrument}...")
            result = analyze_period(instrument, start, end, period_name)
            if result:
                period_results.append(result)

        all_results[period_name] = period_results
        print_period_results(period_results, period_name)

    # Cross-period comparison
    compare_periods(all_results)
    instrument_comparison(all_results)

    # Save results
    output_file = Path(__file__).parent.parent / "data" / "results" / "six_year_validation_2020_2025.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n{'='*120}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*120}")

if __name__ == "__main__":
    main()
