"""
Initial Data Exploration

1. Load XAUUSD data (M5, M15, H1)
2. Test periodic OB time filter
3. Test zone detector
4. Test trend analyzer
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from data.data_loader import DataLoader
from zones.detector import ZoneDetector, ZoneType, ZoneFreshness
from zones.time_filter import PeriodicOBFilter, SessionFilter
from strategies.trend_analyzer import TrendAnalyzer, MultiTimeframeTrend

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)

print("="*80)
print("SD_Trend_Universal_Research - Initial Data Exploration")
print("="*80)

# ============================================================================
# STEP 1: Load Data
# ============================================================================
print("\n[STEP 1] Loading XAUUSD data...")

loader = DataLoader()

# Check available data
print(f"\nAvailable timeframes: {loader.list_available_timeframes()}")
print(f"\nAvailable symbols (M5): {loader.list_available_symbols('M5')}")

# Load XAUUSD multi-timeframe
try:
    symbol = "XAUUSD"
    timeframes = ["M5", "M15", "H1"]

    # Load last 3 months of data for initial testing
    end_date = "2024-12-31"
    start_date = "2024-10-01"

    print(f"\nLoading {symbol} data: {start_date} to {end_date}")

    data = loader.load_multiple_timeframes(
        symbol,
        timeframes,
        start_date=start_date,
        end_date=end_date
    )

    print(f"\nLoaded {len(data)} timeframes:")
    for tf, df in data.items():
        print(f"  {tf}: {len(df):,} bars ({df.index[0]} to {df.index[-1]})")
        print(f"       Columns: {df.columns.tolist()}")

except Exception as e:
    print(f"Error loading data: {e}")
    print("\nTrying to find available files...")
    import os
    m5_path = Path("../MFX_Research_to_Prod/data/raw/parquet/M5")
    if m5_path.exists():
        files = list(m5_path.glob("*.parquet"))
        print(f"Found {len(files)} files in M5 directory")
        for f in files[:10]:
            print(f"  - {f.name}")
    sys.exit(1)

# ============================================================================
# STEP 2: Test Periodic OB Time Filter
# ============================================================================
print("\n\n" + "="*80)
print("[STEP 2] Testing Periodic OB Time Filter")
print("="*80)

ob_filter = PeriodicOBFilter(
    hourly_window_mins=5,      # xx:55 - xx:05
    half_hour_window_mins=3    # xx:30 ± 3 min
)

# Get statistics on M5 data
df_m5 = data["M5"]
stats = ob_filter.get_ob_statistics(df_m5)

print("\nTime Window Statistics (M5 data):")
print(f"  Total bars: {stats['total_bars']:,}")
print(f"  Hourly turn bars: {stats['hourly_turn_bars']:,} ({stats['hourly_turn_pct']:.1f}%)")
print(f"  Half-hour bars: {stats['half_hour_bars']:,} ({stats['half_hour_pct']:.1f}%)")
print(f"  All OB time bars: {stats['ob_bars']:,} ({stats['ob_pct']:.1f}%)")
print(f"  Other time bars: {stats['other_bars']:,} ({stats['other_pct']:.1f}%)")

# Add time features
df_m5 = ob_filter.add_time_features(df_m5)

# Show sample OB times
print("\n\nSample timestamps in OB windows:")
ob_samples = df_m5[df_m5['is_ob_time']].head(20)
for idx, row in ob_samples.iterrows():
    zone_type = row['time_zone'].value if hasattr(row['time_zone'], 'value') else row['time_zone']
    print(f"  {idx.strftime('%Y-%m-%d %H:%M')} - {zone_type}")

# Session analysis
session_filter = SessionFilter()
df_m5 = session_filter.add_session_features(df_m5)

print("\n\nSession distribution:")
session_counts = df_m5['session'].value_counts()
for session, count in session_counts.items():
    pct = count / len(df_m5) * 100
    print(f"  {session}: {count:,} bars ({pct:.1f}%)")

# ============================================================================
# STEP 3: Test Zone Detector
# ============================================================================
print("\n\n" + "="*80)
print("[STEP 3] Testing Zone Detector")
print("="*80)

zone_detector = ZoneDetector(
    lookback_periods=100,
    min_consolidation_candles=3,
    zone_width_atr=0.5,
    min_velocity_atr=1.0,
    freshness_max_age=50
)

print("\nDetecting zones on XAUUSD M5 data...")
print("(This may take a minute...)")

# Detect zones (use only first 1000 bars for speed)
df_test = df_m5.head(2000)[['open', 'high', 'low', 'close', 'volume']]
zones = zone_detector.detect_zones(df_test)

print(f"\n\nDetected {len(zones)} zones")
print(f"  Supply zones: {sum(1 for z in zones if z.zone_type == ZoneType.SUPPLY)}")
print(f"  Demand zones: {sum(1 for z in zones if z.zone_type == ZoneType.DEMAND)}")
print(f"\n  Fresh zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.FRESH)}")
print(f"  Tested zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.TESTED)}")
print(f"  Broken zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.BROKEN)}")

# Show top zones by strength
zones_by_strength = sorted(zones, key=lambda z: z.strength, reverse=True)

print("\n\nTop 10 strongest zones:")
print(f"{'Type':<8} {'Price Range':<20} {'Created':<20} {'Strength':<10} {'Status':<10}")
print("-" * 80)
for i, zone in enumerate(zones_by_strength[:10], 1):
    price_range = f"{zone.bottom:.2f} - {zone.top:.2f}"
    created = zone.creation_time.strftime('%Y-%m-%d %H:%M')
    print(f"{zone.zone_type.value:<8} {price_range:<20} {created:<20} {zone.strength:<10.3f} {zone.freshness.value:<10}")

# ============================================================================
# STEP 4: Test Trend Analyzer
# ============================================================================
print("\n\n" + "="*80)
print("[STEP 4] Testing Multi-Timeframe Trend Analyzer")
print("="*80)

# Prepare data for trend analysis (remove extra columns)
mtf_data = {}
for tf in ["M5", "M15", "H1"]:
    mtf_data[tf] = data[tf][['open', 'high', 'low', 'close', 'volume']].copy()

# Analyze trends
mtf_trend = MultiTimeframeTrend(mtf_data)
trends = mtf_trend.analyze_all()

print("\nTrend Analysis (latest state):")
print(f"{'Timeframe':<12} {'Direction':<12} {'Regime':<12} {'Strength':<10} {'ADX':<8} {'Hurst':<8}")
print("-" * 80)
for tf, state in trends.items():
    print(f"{tf:<12} {state.direction.value:<12} {state.regime.value:<12} "
          f"{state.strength:<10.3f} {state.adx:<8.2f} {state.hurst:<8.3f}")

print(f"\n\nMulti-Timeframe Summary:")
print(f"  Trend aligned: {mtf_trend.is_aligned(required_timeframes=2)}")
print(f"  Dominant direction: {mtf_trend.get_dominant_direction().value}")
print(f"  Dominant regime: {mtf_trend.get_dominant_regime().value}")
print(f"  Average strength: {mtf_trend.get_average_strength():.3f}")

# ============================================================================
# STEP 5: Combine Zones + OB Times
# ============================================================================
print("\n\n" + "="*80)
print("[STEP 5] Analyzing Zones Created During OB Times")
print("="*80)

# Check which zones were created during OB times
zones_with_time = []
for zone in zones:
    is_ob_time = ob_filter.is_ob_time(zone.creation_time)
    time_zone = ob_filter.get_time_zone(zone.creation_time)
    zones_with_time.append({
        'zone': zone,
        'is_ob_time': is_ob_time,
        'time_zone': time_zone
    })

ob_zones = [z for z in zones_with_time if z['is_ob_time']]
other_zones = [z for z in zones_with_time if not z['is_ob_time']]

print(f"\nZones created during OB times: {len(ob_zones)} ({len(ob_zones)/len(zones)*100:.1f}%)")
print(f"Zones created during other times: {len(other_zones)} ({len(other_zones)/len(zones)*100:.1f}%)")

# Compare average strength
ob_strength = np.mean([z['zone'].strength for z in ob_zones]) if ob_zones else 0
other_strength = np.mean([z['zone'].strength for z in other_zones]) if other_zones else 0

print(f"\nAverage zone strength:")
print(f"  OB times: {ob_strength:.3f}")
print(f"  Other times: {other_strength:.3f}")
print(f"  Difference: {ob_strength - other_strength:+.3f} ({(ob_strength/other_strength - 1)*100:+.1f}%)")

# ============================================================================
# Summary
# ============================================================================
print("\n\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"""
Data Loaded:
  - Symbol: {symbol}
  - Date Range: {start_date} to {end_date}
  - Timeframes: {', '.join(timeframes)}
  - Total M5 bars: {len(df_m5):,}

Periodic OB Times:
  - {stats['ob_pct']:.1f}% of bars fall in OB windows
  - Hourly turn: {stats['hourly_turn_pct']:.1f}%
  - Half-hour: {stats['half_hour_pct']:.1f}%

Zones Detected:
  - Total zones: {len(zones)}
  - Zones in OB times: {len(ob_zones)} ({len(ob_zones)/len(zones)*100:.1f}%)
  - Avg strength (OB): {ob_strength:.3f}
  - Avg strength (other): {other_strength:.3f}

Trend State:
  - Direction: {mtf_trend.get_dominant_direction().value}
  - Regime: {mtf_trend.get_dominant_regime().value}
  - Aligned: {mtf_trend.is_aligned()}
""")

print("\n" + "="*80)
print("Exploration complete! Next steps:")
print("  1. Create visualizations (zones on chart with OB time highlights)")
print("  2. Backtest zone trading (OB times vs other times)")
print("  3. Test on other instruments (EURUSD, GBPUSD, etc.)")
print("="*80)
