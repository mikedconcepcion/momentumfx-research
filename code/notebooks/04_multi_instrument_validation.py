"""
Multi-Instrument Validation

Tests zone detection and OB time windows across:
- EURUSD (baseline FX)
- GBPUSD (high volatility FX)
- USDJPY (JPY pairs - different pip structure)
- BTCUSD (crypto - very high volatility)
- XAUUSD (gold - reference)

Validates:
1. Zone detection parameters across instruments
2. OB time window effectiveness
3. Multi-timeframe trend analysis
4. Parameter universality
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List

from data.data_loader import DataLoader
from zones.detector import ZoneDetector, ZoneType, ZoneFreshness
from zones.time_filter import PeriodicOBFilter, SessionFilter
from strategies.trend_analyzer import TrendAnalyzer, MultiTimeframeTrend

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 140)

print("="*100)
print("MULTI-INSTRUMENT VALIDATION - Universal Buy/Sell Zone Indicator")
print("="*100)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# ============================================================================
# CONFIGURATION
# ============================================================================
INSTRUMENTS = [
    "EURUSD",   # Baseline FX - most liquid
    "GBPUSD",   # High volatility FX
    "USDJPY",   # JPY pair - different pip structure
    "XAUUSD",   # Gold - reference (already tested)
    "BTCUSD",   # Crypto - very high volatility
]

START_DATE = "2024-10-01"
END_DATE = "2024-12-31"
TIMEFRAMES = ["M5", "M15", "H1"]

# Zone detection parameters (calibrated for XAUUSD)
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

# Store results
results = {}

# ============================================================================
# VALIDATION LOOP
# ============================================================================
loader = DataLoader()
ob_filter = PeriodicOBFilter(**OB_PARAMS)
session_filter = SessionFilter()

for symbol in INSTRUMENTS:
    print(f"\n{'='*100}")
    print(f"VALIDATING: {symbol}")
    print(f"{'='*100}")

    try:
        # Load data
        print(f"\n[1/4] Loading {symbol} data...")
        data = loader.load_multiple_timeframes(symbol, TIMEFRAMES, START_DATE, END_DATE)

        if len(data) == 0:
            print(f"  ERROR: No data available for {symbol}")
            results[symbol] = {'error': 'No data available'}
            continue

        print(f"  Loaded {len(data)} timeframes:")
        for tf, df in data.items():
            print(f"    - {tf}: {len(df):,} bars")

        # Get M5 data for zone detection
        if "M5" not in data:
            print(f"  ERROR: M5 data not available for {symbol}")
            results[symbol] = {'error': 'M5 data missing'}
            continue

        df_m5 = data["M5"].copy()

        # Calculate basic statistics
        df_m5 = ob_filter.add_time_features(df_m5)
        df_m5 = session_filter.add_session_features(df_m5)

        # Calculate ATR
        high = df_m5['high']
        low = df_m5['low']
        close_prev = df_m5['close'].shift(1)
        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()

        avg_atr = atr.mean()
        price_range = df_m5['close'].max() - df_m5['close'].min()

        print(f"\n[2/4] Price & Volatility Statistics:")
        print(f"  Price range: {df_m5['close'].min():.5f} - {df_m5['close'].max():.5f}")
        print(f"  Average ATR: {avg_atr:.5f}")
        print(f"  ATR/Price ratio: {avg_atr/df_m5['close'].mean()*100:.3f}%")

        # OB time statistics
        stats = ob_filter.get_ob_statistics(df_m5)

        print(f"\n[3/4] OB Time Window Analysis:")
        print(f"  Total bars: {stats['total_bars']:,}")
        print(f"  OB time bars: {stats['ob_bars']:,} ({stats['ob_pct']:.1f}%)")
        print(f"    - Hourly turn: {stats['hourly_turn_bars']:,} ({stats['hourly_turn_pct']:.1f}%)")
        print(f"    - Half-hour: {stats['half_hour_bars']:,} ({stats['half_hour_pct']:.1f}%)")

        # Zone detection
        print(f"\n[4/4] Zone Detection (params: velocity={ZONE_PARAMS['min_velocity_atr']}x ATR, "
              f"consol={ZONE_PARAMS['min_consolidation_candles']} candles):")

        zone_detector = ZoneDetector(**ZONE_PARAMS)
        df_zones = df_m5[['open', 'high', 'low', 'close', 'volume']].copy()
        zones = zone_detector.detect_zones(df_zones)

        print(f"  Total zones: {len(zones)}")

        if len(zones) > 0:
            supply_zones = sum(1 for z in zones if z.zone_type == ZoneType.SUPPLY)
            demand_zones = sum(1 for z in zones if z.zone_type == ZoneType.DEMAND)
            fresh_zones = sum(1 for z in zones if z.freshness == ZoneFreshness.FRESH)

            print(f"    - Supply: {supply_zones}, Demand: {demand_zones}")
            print(f"    - Fresh: {fresh_zones}, Tested: {len(zones)-fresh_zones}")

            # Classify by OB time
            zones_with_time = []
            for zone in zones:
                is_ob = ob_filter.is_ob_time(zone.creation_time)
                zones_with_time.append({
                    'zone': zone,
                    'is_ob_time': is_ob
                })

            ob_zones = [z for z in zones_with_time if z['is_ob_time']]
            other_zones = [z for z in zones_with_time if not z['is_ob_time']]

            ob_pct = len(ob_zones) / len(zones) * 100 if len(zones) > 0 else 0

            # Calculate strengths
            avg_strength = np.mean([z.strength for z in zones])
            ob_strength = np.mean([z['zone'].strength for z in ob_zones]) if ob_zones else 0
            other_strength = np.mean([z['zone'].strength for z in other_zones]) if other_zones else 0

            print(f"\n  OB Time Correlation:")
            print(f"    - Zones in OB windows: {len(ob_zones)} ({ob_pct:.1f}%)")
            print(f"    - Expected (baseline): {stats['ob_pct']:.1f}%")
            print(f"    - Concentration factor: {ob_pct/stats['ob_pct']:.2f}x" if stats['ob_pct'] > 0 else "    - N/A")

            if ob_zones and other_zones:
                strength_diff = ob_strength - other_strength
                strength_diff_pct = (ob_strength / other_strength - 1) * 100 if other_strength > 0 else 0
                print(f"\n  Zone Strength:")
                print(f"    - Average: {avg_strength:.3f}")
                print(f"    - OB times: {ob_strength:.3f}")
                print(f"    - Other times: {other_strength:.3f}")
                print(f"    - Difference: {strength_diff:+.3f} ({strength_diff_pct:+.1f}%)")

            # Top zones
            zones_sorted = sorted(zones, key=lambda z: z.strength, reverse=True)[:3]
            print(f"\n  Top 3 Zones:")
            for i, z in enumerate(zones_sorted, 1):
                ob_flag = "[OB]" if ob_filter.is_ob_time(z.creation_time) else "    "
                print(f"    {i}. {ob_flag} {z.zone_type.value.upper()}: "
                      f"{z.bottom:.5f}-{z.top:.5f}, strength={z.strength:.3f}")

        # Multi-timeframe trend
        mtf_data = {}
        for tf in TIMEFRAMES:
            if tf in data:
                mtf_data[tf] = data[tf][['open', 'high', 'low', 'close', 'volume']].copy()

        if len(mtf_data) >= 2:
            mtf_trend = MultiTimeframeTrend(mtf_data)
            trends = mtf_trend.analyze_all()

            print(f"\n  Multi-Timeframe Trend (latest):")
            for tf, state in trends.items():
                print(f"    {tf}: {state.direction.value} ({state.regime.value}), "
                      f"strength={state.strength:.3f}, ADX={state.adx:.1f}")

            print(f"    Aligned: {mtf_trend.is_aligned()}, "
                  f"Dominant: {mtf_trend.get_dominant_direction().value}")

        # Store results
        results[symbol] = {
            'bars': len(df_m5),
            'avg_atr': avg_atr,
            'price_range': price_range,
            'ob_pct': stats['ob_pct'],
            'zones_total': len(zones),
            'zones_supply': supply_zones if len(zones) > 0 else 0,
            'zones_demand': demand_zones if len(zones) > 0 else 0,
            'zones_ob': len(ob_zones) if len(zones) > 0 else 0,
            'zones_ob_pct': ob_pct if len(zones) > 0 else 0,
            'concentration_factor': ob_pct / stats['ob_pct'] if (len(zones) > 0 and stats['ob_pct'] > 0) else 0,
            'avg_strength': avg_strength if len(zones) > 0 else 0,
            'ob_strength': ob_strength if len(zones) > 0 else 0,
            'other_strength': other_strength if len(zones) > 0 else 0,
            'strength_boost_pct': strength_diff_pct if (len(zones) > 0 and ob_zones and other_zones) else 0,
            'trend_aligned': mtf_trend.is_aligned() if len(mtf_data) >= 2 else None,
            'dominant_direction': mtf_trend.get_dominant_direction().value if len(mtf_data) >= 2 else None,
        }

    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        results[symbol] = {'error': str(e)}

# ============================================================================
# COMPARATIVE ANALYSIS
# ============================================================================
print(f"\n\n{'='*100}")
print("COMPARATIVE ANALYSIS - All Instruments")
print(f"{'='*100}")

# Create comparison table
print(f"\n{'Instrument':<10} {'Bars':>8} {'Avg ATR':>10} {'Zones':>7} {'OB%':>6} {'Conc':>6} {'Strength+':>10} {'Trend':>10}")
print("-"*100)

for symbol, data in results.items():
    if 'error' in data:
        print(f"{symbol:<10} ERROR: {data['error']}")
    else:
        bars = f"{data['bars']:,}"
        atr = f"{data['avg_atr']:.5f}"
        zones = f"{data['zones_total']}"
        ob_pct = f"{data['zones_ob_pct']:.1f}%" if data['zones_total'] > 0 else "N/A"
        conc = f"{data['concentration_factor']:.2f}x" if data['concentration_factor'] > 0 else "N/A"
        boost = f"{data['strength_boost_pct']:+.1f}%" if data['strength_boost_pct'] != 0 else "N/A"
        trend = f"{data['dominant_direction']}" if data['dominant_direction'] else "N/A"

        print(f"{symbol:<10} {bars:>8} {atr:>10} {zones:>7} {ob_pct:>6} {conc:>6} {boost:>10} {trend:>10}")

# ============================================================================
# SUMMARY & CONCLUSIONS
# ============================================================================
print(f"\n\n{'='*100}")
print("SUMMARY & CONCLUSIONS")
print(f"{'='*100}")

# Filter valid results
valid_results = {k: v for k, v in results.items() if 'error' not in v and v['zones_total'] > 0}

if len(valid_results) > 0:
    print(f"\nInstruments with zones detected: {len(valid_results)}/{len(INSTRUMENTS)}")

    # Average statistics
    avg_concentration = np.mean([v['concentration_factor'] for v in valid_results.values() if v['concentration_factor'] > 0])
    avg_strength_boost = np.mean([v['strength_boost_pct'] for v in valid_results.values() if v['strength_boost_pct'] != 0])

    print(f"\nOB Time Window Performance:")
    print(f"  Average concentration factor: {avg_concentration:.2f}x")
    print(f"  Average strength boost: {avg_strength_boost:+.1f}%")

    # Check if OB windows are universal
    ob_effective = sum(1 for v in valid_results.values() if v['concentration_factor'] > 1.5)

    print(f"\nUniversality Assessment:")
    print(f"  Instruments with OB concentration >1.5x: {ob_effective}/{len(valid_results)}")

    if ob_effective >= len(valid_results) * 0.7:
        print(f"  -> OB time windows appear UNIVERSAL (70%+ effective)")
    elif ob_effective >= len(valid_results) * 0.5:
        print(f"  -> OB time windows are PARTIALLY universal (50-70% effective)")
    else:
        print(f"  -> OB time windows may be INSTRUMENT-SPECIFIC (<50% effective)")

    # Parameter universality
    instruments_with_zones = [k for k, v in valid_results.items()]
    print(f"\nParameter Universality:")
    print(f"  Same parameters work for: {', '.join(instruments_with_zones)}")

    # Recommendations
    print(f"\nRECOMMENDATIONS:")

    if avg_concentration >= 2.0:
        print(f"  1. OB time windows are HIGHLY EFFECTIVE - use as primary filter")
    elif avg_concentration >= 1.5:
        print(f"  1. OB time windows are EFFECTIVE - use as confluence factor")
    else:
        print(f"  1. OB time windows show WEAK signal - may need refinement")

    if len(valid_results) >= 3:
        print(f"  2. Zone detection parameters are reasonably UNIVERSAL")
    else:
        print(f"  2. Zone detection may need INSTRUMENT-SPECIFIC tuning")

    print(f"  3. Next: Build backtest framework with entry/exit rules")
    print(f"  4. Next: Create visualization tools")

else:
    print(f"\nWARNING: No zones detected on any instrument!")
    print(f"Consider:")
    print(f"  - Further relaxing detection parameters")
    print(f"  - Using longer data period")
    print(f"  - Different zone detection algorithm")

print(f"\n{'='*100}")
print(f"Validation complete. Results saved to results dictionary.")
print(f"Documentation: See docs/VALIDATION_RESULTS.md")
print(f"{'='*100}")

# Save results to file
output_file = Path(__file__).parent.parent / "docs" / "validation_results.txt"
with open(output_file, 'w') as f:
    f.write("MULTI-INSTRUMENT VALIDATION RESULTS\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*100 + "\n\n")

    for symbol, data in results.items():
        f.write(f"{symbol}:\n")
        for key, value in data.items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

print(f"\nDetailed results saved to: {output_file}")
