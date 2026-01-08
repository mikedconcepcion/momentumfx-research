"""
Debug Zone Detector - Find out why no zones are detected
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from data.data_loader import DataLoader
from zones.detector import ZoneDetector

print("="*80)
print("Zone Detector Debug")
print("="*80)

# Load data
loader = DataLoader()
df = loader.load("XAUUSD", "M5", start_date="2024-10-01", end_date="2024-10-31")
print(f"\nLoaded {len(df):,} bars of XAUUSD M5 data")
print(f"Date range: {df.index[0]} to {df.index[-1]}")
print(f"Price range: {df['close'].min():.2f} to {df['close'].max():.2f}")

# Prepare data
df = df[['open', 'high', 'low', 'close', 'volume']].copy()

# Calculate ATR to understand typical volatility
high = df['high']
low = df['low']
close_prev = df['close'].shift(1)
tr1 = high - low
tr2 = abs(high - close_prev)
tr3 = abs(low - close_prev)
tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
atr = tr.rolling(window=14).mean()
df['atr'] = atr

print(f"\nAverage ATR: {atr.mean():.2f}")
print(f"ATR range: {atr.min():.2f} to {atr.max():.2f}")

# Test zone detector with different parameters
print("\n" + "="*80)
print("Testing Zone Detector with various parameters")
print("="*80)

param_sets = [
    {
        'name': 'Default (strict)',
        'lookback': 100,
        'min_consolidation': 3,
        'zone_width_atr': 0.5,
        'min_velocity_atr': 1.0
    },
    {
        'name': 'Relaxed velocity',
        'lookback': 100,
        'min_consolidation': 3,
        'zone_width_atr': 0.5,
        'min_velocity_atr': 0.5  # Lower threshold
    },
    {
        'name': 'Relaxed consolidation',
        'lookback': 100,
        'min_consolidation': 2,  # Fewer candles needed
        'zone_width_atr': 0.5,
        'min_velocity_atr': 0.5
    },
    {
        'name': 'Very relaxed',
        'lookback': 200,
        'min_consolidation': 2,
        'zone_width_atr': 0.8,  # Wider zones
        'min_velocity_atr': 0.3  # Much lower velocity requirement
    }
]

for params in param_sets:
    print(f"\n{params['name']}:")
    print(f"  lookback={params['lookback']}, min_consol={params['min_consolidation']}, "
          f"zone_width={params['zone_width_atr']}x ATR, min_velocity={params['min_velocity_atr']}x ATR")

    detector = ZoneDetector(
        lookback_periods=params['lookback'],
        min_consolidation_candles=params['min_consolidation'],
        zone_width_atr=params['zone_width_atr'],
        min_velocity_atr=params['min_velocity_atr']
    )

    # Test on subset of data
    test_df = df.head(1000).copy()
    zones = detector.detect_zones(test_df)

    print(f"  -> Found {len(zones)} zones")

    if len(zones) > 0:
        print(f"     Supply: {sum(1 for z in zones if z.zone_type.value == 'supply')}, "
              f"Demand: {sum(1 for z in zones if z.zone_type.value == 'demand')}")

        # Show top 3
        sorted_zones = sorted(zones, key=lambda z: z.strength, reverse=True)
        print("     Top 3 zones:")
        for i, zone in enumerate(sorted_zones[:3], 1):
            print(f"       {i}. {zone.zone_type.value.upper()}: "
                  f"{zone.bottom:.2f}-{zone.top:.2f}, "
                  f"strength={zone.strength:.3f}, "
                  f"velocity={zone.velocity:.2f}x ATR")

# Let's manually check for consolidation patterns
print("\n" + "="*80)
print("Manual Pattern Detection")
print("="*80)

# Look for periods of low volatility followed by sharp moves
print("\nScanning for consolidation -> breakout patterns...")

window = 10  # Look at 10-candle windows
breakouts = []

for i in range(100, len(df) - 10):
    # Get consolidation window
    consol = df.iloc[i-window:i]
    consol_range = consol['high'].max() - consol['low'].min()
    consol_atr = consol['atr'].mean()

    if pd.isna(consol_atr) or consol_atr == 0:
        continue

    # Check if consolidation (range < 0.8 ATR)
    if consol_range < consol_atr * 0.8:
        # Check for breakout in next 5 candles
        breakout = df.iloc[i:i+5]
        move_up = breakout['high'].max() - consol['high'].max()
        move_down = consol['low'].min() - breakout['low'].min()
        max_move = max(move_up, move_down)

        # If move > 0.5 ATR, it's a breakout
        if max_move > consol_atr * 0.5:
            direction = "UP" if move_up > move_down else "DOWN"
            breakouts.append({
                'timestamp': df.index[i],
                'direction': direction,
                'consol_range': consol_range,
                'atr': consol_atr,
                'move': max_move,
                'move_atr_multiple': max_move / consol_atr
            })

print(f"\nFound {len(breakouts)} consolidation -> breakout patterns")

if breakouts:
    print("\nSample patterns:")
    for i, b in enumerate(breakouts[:10], 1):
        print(f"  {i}. {b['timestamp'].strftime('%Y-%m-%d %H:%M')} - "
              f"{b['direction']} breakout, "
              f"move={b['move']:.2f} ({b['move_atr_multiple']:.2f}x ATR)")

print("\n" + "="*80)
print("Conclusion")
print("="*80)
print("""
If very relaxed parameters still find 0 zones:
  1. The detection algorithm may need refinement
  2. The consolidation detection logic may be too strict
  3. May need to adjust for XAUUSD's specific volatility profile

Manual pattern detection shows if consolidation->breakout patterns exist in the data.
""")
