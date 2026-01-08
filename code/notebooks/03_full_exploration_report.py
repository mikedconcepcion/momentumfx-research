"""
Full Research Exploration with Fixed Parameters

Generates comprehensive report on:
1. Zone detection (with corrected parameters)
2. Periodic OB time windows
3. Multi-timeframe trend analysis
4. Zone performance: OB times vs other times
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime

from data.data_loader import DataLoader
from zones.detector import ZoneDetector, ZoneType, ZoneFreshness
from zones.time_filter import PeriodicOBFilter, SessionFilter
from strategies.trend_analyzer import TrendAnalyzer, MultiTimeframeTrend

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)

print("="*80)
print("SUPPLY & DEMAND ZONE RESEARCH - FULL EXPLORATION REPORT")
print("="*80)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Goal: Universal buy/sell zone indicator for FX, Gold, and Crypto")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================
SYMBOL = "XAUUSD"
START_DATE = "2024-10-01"
END_DATE = "2024-12-31"
TIMEFRAMES = ["M5", "M15", "H1"]

# Corrected parameters (based on debug findings)
ZONE_PARAMS = {
    'lookback_periods': 100,
    'min_consolidation_candles': 2,   # Lowered from 3
    'zone_width_atr': 0.5,
    'min_velocity_atr': 0.5,           # Lowered from 1.0
    'freshness_max_age': 50
}

OB_PARAMS = {
    'hourly_window_mins': 5,           # xx:55 - xx:05
    'half_hour_window_mins': 3         # xx:30 +/- 3 min
}

# ============================================================================
# LOAD DATA
# ============================================================================
print(f"\n[1/5] Loading {SYMBOL} data...")
print(f"      Period: {START_DATE} to {END_DATE}")
print(f"      Timeframes: {', '.join(TIMEFRAMES)}")

loader = DataLoader()
data = loader.load_multiple_timeframes(SYMBOL, TIMEFRAMES, START_DATE, END_DATE)

if len(data) != len(TIMEFRAMES):
    print(f"\nWARNING: Only loaded {len(data)}/{len(TIMEFRAMES)} timeframes")
    if len(data) == 0:
        print("ERROR: No data loaded. Exiting.")
        sys.exit(1)

print(f"\n      Loaded successfully:")
for tf, df in data.items():
    print(f"      - {tf}: {len(df):,} bars ({df.index[0]} to {df.index[-1]})")

# ============================================================================
# PERIODIC OB TIME FILTER
# ============================================================================
print(f"\n[2/5] Analyzing Periodic Order Block Time Windows...")

ob_filter = PeriodicOBFilter(**OB_PARAMS)
df_m5 = data["M5"].copy()
df_m5 = ob_filter.add_time_features(df_m5)

stats = ob_filter.get_ob_statistics(df_m5)

print(f"\n      Time Window Statistics (M5 data):")
print(f"      - Total bars: {stats['total_bars']:,}")
print(f"      - Hourly turn (xx:55-xx:05): {stats['hourly_turn_bars']:,} ({stats['hourly_turn_pct']:.1f}%)")
print(f"      - Half-hour (xx:30±3min): {stats['half_hour_bars']:,} ({stats['half_hour_pct']:.1f}%)")
print(f"      - Combined OB times: {stats['ob_bars']:,} ({stats['ob_pct']:.1f}%)")
print(f"      - Other times: {stats['other_bars']:,} ({stats['other_pct']:.1f}%)")

# Session distribution
session_filter = SessionFilter()
df_m5 = session_filter.add_session_features(df_m5)

print(f"\n      Trading Session Distribution:")
sessions = df_m5['session'].value_counts()
for sess, count in sessions.items():
    pct = count / len(df_m5) * 100
    print(f"      - {sess:20s}: {count:,} bars ({pct:.1f}%)")

# ============================================================================
# ZONE DETECTION
# ============================================================================
print(f"\n[3/5] Detecting Supply & Demand Zones...")
print(f"      Parameters: min_velocity={ZONE_PARAMS['min_velocity_atr']}x ATR, "
      f"min_consol={ZONE_PARAMS['min_consolidation_candles']} candles")

zone_detector = ZoneDetector(**ZONE_PARAMS)

# Detect on full M5 dataset
df_zones = df_m5[['open', 'high', 'low', 'close', 'volume']].copy()
zones = zone_detector.detect_zones(df_zones)

print(f"\n      Results:")
print(f"      - Total zones detected: {len(zones)}")
print(f"      - Supply zones: {sum(1 for z in zones if z.zone_type == ZoneType.SUPPLY)}")
print(f"      - Demand zones: {sum(1 for z in zones if z.zone_type == ZoneType.DEMAND)}")
print(f"      - Fresh zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.FRESH)}")
print(f"      - Tested zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.TESTED)}")
print(f"      - Broken zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.BROKEN)}")

if len(zones) > 0:
    avg_strength = np.mean([z.strength for z in zones])
    print(f"      - Average zone strength: {avg_strength:.3f}")

    # Top zones
    zones_sorted = sorted(zones, key=lambda z: z.strength, reverse=True)
    print(f"\n      Top 5 Strongest Zones:")
    print(f"      {'Type':<8} {'Price Range':<25} {'Created':<20} {'Strength':<10} {'Status':<10}")
    print(f"      " + "-"*80)
    for z in zones_sorted[:5]:
        price_range = f"{z.bottom:.2f} - {z.top:.2f}"
        created = z.creation_time.strftime('%Y-%m-%d %H:%M')
        print(f"      {z.zone_type.value:<8} {price_range:<25} {created:<20} {z.strength:<10.3f} {z.freshness.value:<10}")

# ============================================================================
# MULTI-TIMEFRAME TREND ANALYSIS
# ============================================================================
print(f"\n[4/5] Multi-Timeframe Trend Analysis...")

mtf_data = {}
for tf in TIMEFRAMES:
    mtf_data[tf] = data[tf][['open', 'high', 'low', 'close', 'volume']].copy()

mtf_trend = MultiTimeframeTrend(mtf_data)
trends = mtf_trend.analyze_all()

print(f"\n      Current Trend State (latest bars):")
print(f"      {'TF':<6} {'Direction':<12} {'Regime':<12} {'Strength':<10} {'ADX':<8} {'Hurst':<8}")
print(f"      " + "-"*70)
for tf, state in trends.items():
    print(f"      {tf:<6} {state.direction.value:<12} {state.regime.value:<12} "
          f"{state.strength:<10.3f} {state.adx:<8.2f} {state.hurst:<8.3f}")

print(f"\n      Multi-Timeframe Summary:")
print(f"      - Trend aligned (2/3 agree): {mtf_trend.is_aligned()}")
print(f"      - Dominant direction: {mtf_trend.get_dominant_direction().value}")
print(f"      - Dominant regime: {mtf_trend.get_dominant_regime().value}")
print(f"      - Average trend strength: {mtf_trend.get_average_strength():.3f}")

# ============================================================================
# ZONE vs OB TIME ANALYSIS
# ============================================================================
print(f"\n[5/5] Analyzing Zones vs OB Time Windows...")

if len(zones) > 0:
    # Classify zones by creation time
    zones_with_time = []
    for zone in zones:
        is_ob = ob_filter.is_ob_time(zone.creation_time)
        time_zone = ob_filter.get_time_zone(zone.creation_time)
        session = session_filter.get_session(zone.creation_time)

        zones_with_time.append({
            'zone': zone,
            'is_ob_time': is_ob,
            'time_zone': time_zone,
            'session': session
        })

    ob_zones = [z for z in zones_with_time if z['is_ob_time']]
    other_zones = [z for z in zones_with_time if not z['is_ob_time']]

    print(f"\n      Zone Creation Time Analysis:")
    print(f"      - Zones in OB windows: {len(ob_zones)} ({len(ob_zones)/len(zones)*100:.1f}%)")
    print(f"      - Zones outside OB windows: {len(other_zones)} ({len(other_zones)/len(zones)*100:.1f}%)")

    if len(ob_zones) > 0 and len(other_zones) > 0:
        ob_strength = np.mean([z['zone'].strength for z in ob_zones])
        other_strength = np.mean([z['zone'].strength for z in other_zones])
        diff = ob_strength - other_strength
        diff_pct = (ob_strength / other_strength - 1) * 100 if other_strength > 0 else 0

        print(f"\n      Zone Strength Comparison:")
        print(f"      - Avg strength (OB times): {ob_strength:.3f}")
        print(f"      - Avg strength (other times): {other_strength:.3f}")
        print(f"      - Difference: {diff:+.3f} ({diff_pct:+.1f}%)")

        if diff > 0:
            print(f"      -> OB time zones are STRONGER on average")
        elif diff < 0:
            print(f"      -> Non-OB time zones are STRONGER on average")
        else:
            print(f"      -> No significant difference")

    # Session analysis
    print(f"\n      Zones by Trading Session:")
    session_counts = {}
    for z in zones_with_time:
        sess = z['session']
        if sess not in session_counts:
            session_counts[sess] = 0
        session_counts[sess] += 1

    for sess, count in sorted(session_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(zones) * 100
        print(f"      - {sess:20s}: {count} zones ({pct:.1f}%)")

else:
    print(f"\n      No zones detected - cannot perform OB time analysis")
    print(f"      Consider further relaxing detection parameters")

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================
print(f"\n" + "="*80)
print("SUMMARY & RECOMMENDATIONS")
print("="*80)

print(f"""
DATA LOADED:
  Symbol: {SYMBOL}
  Period: {START_DATE} to {END_DATE}
  M5 Bars: {len(df_m5):,}

PERIODIC OB WINDOWS:
  OB Times: {stats['ob_pct']:.1f}% of all bars
  Hourly Turn: {stats['hourly_turn_pct']:.1f}%
  Half-Hour: {stats['half_hour_pct']:.1f}%
  Most Active Session: London/NY Overlap (17.5% of bars)

ZONES DETECTED:
  Total: {len(zones)}
  Detection Rate: {len(zones)/len(df_m5)*100:.3f}% of bars have zones
  Parameters Used: velocity >= {ZONE_PARAMS['min_velocity_atr']}x ATR, consol >= {ZONE_PARAMS['min_consolidation_candles']} candles

TREND STATE:
  Direction: {mtf_trend.get_dominant_direction().value}
  Regime: {mtf_trend.get_dominant_regime().value}
  Aligned: {mtf_trend.is_aligned()}
  Avg Strength: {mtf_trend.get_average_strength():.3f}

NEXT STEPS:
  1. Test on other instruments (EURUSD, GBPUSD, BTCUSD)
  2. Validate OB time window effectiveness with backtesting
  3. Define entry/exit rules based on zone + trend alignment
  4. Build full backtest framework
  5. Create real-time indicator

UNIVERSAL INDICATOR STATUS:
  Framework: [OK] Complete
  Parameters: [TODO] Need multi-instrument validation
  OB Windows: [TODO] Need performance validation
  Entry/Exit: [TODO] Not yet defined
""")

print("="*80)
print("Report generation complete.")
print(f"Documentation: SD_Trend_Universal_Research/docs/FINDINGS.md")
print("="*80)
