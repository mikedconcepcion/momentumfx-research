"""
Supply & Demand Zone Detector

Identifies price zones where institutional orders cluster based on:
- Price consolidation areas
- Sharp moves away from zones (velocity)
- Volume characteristics
- Zone freshness (untested vs tested)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class ZoneType(Enum):
    SUPPLY = "supply"      # Resistance / selling zone
    DEMAND = "demand"      # Support / buying zone


class ZoneFreshness(Enum):
    FRESH = "fresh"        # Never retested
    TESTED = "tested"      # Retested but held
    BROKEN = "broken"      # Zone invalidated


@dataclass
class Zone:
    """Represents a supply or demand zone"""
    zone_type: ZoneType
    top: float             # Upper boundary
    bottom: float          # Lower boundary
    creation_time: pd.Timestamp
    creation_idx: int      # Index in dataframe
    touches: int = 0       # Number of times retested
    freshness: ZoneFreshness = ZoneFreshness.FRESH
    strength: float = 0.0  # Strength score 0-1

    # Metrics for strength calculation
    velocity: float = 0.0  # Price velocity leaving zone
    volume: float = 0.0    # Volume in zone
    time_in_zone: int = 0  # Candles spent consolidating

    @property
    def width(self) -> float:
        return self.top - self.bottom

    @property
    def midpoint(self) -> float:
        return (self.top + self.bottom) / 2

    def contains(self, price: float, penetration_pct: float = 0.0) -> bool:
        """Check if price is within zone (with optional penetration tolerance)"""
        zone_height = self.width
        penetration = zone_height * penetration_pct

        return (self.bottom - penetration) <= price <= (self.top + penetration)

    def is_fresh(self, current_idx: int, max_age: int) -> bool:
        """Check if zone is still fresh"""
        age = current_idx - self.creation_idx
        return self.freshness == ZoneFreshness.FRESH and age <= max_age


class ZoneDetector:
    """Detects supply and demand zones in price data"""

    def __init__(
        self,
        lookback_periods: int = 100,
        min_consolidation_candles: int = 3,
        zone_width_atr: float = 0.5,
        min_velocity_atr: float = 1.0,
        freshness_max_age: int = 50,
        strength_weights: Dict[str, float] = None
    ):
        self.lookback_periods = lookback_periods
        self.min_consolidation_candles = min_consolidation_candles
        self.zone_width_atr = zone_width_atr
        self.min_velocity_atr = min_velocity_atr
        self.freshness_max_age = freshness_max_age

        # Weights for strength calculation
        self.strength_weights = strength_weights or {
            'volume': 0.3,
            'velocity': 0.3,
            'time': 0.2,
            'touch': 0.2
        }

    def detect_zones(self, df: pd.DataFrame) -> List[Zone]:
        """
        Detect supply and demand zones in price data

        Args:
            df: DataFrame with columns: open, high, low, close, volume
                Index should be timestamp

        Returns:
            List of Zone objects
        """
        # Calculate ATR for zone sizing
        df = self._add_atr(df)

        zones = []

        # Look for consolidation areas followed by sharp moves
        for i in range(self.lookback_periods, len(df)):
            # Check for consolidation
            consolidation_start = i - self.min_consolidation_candles - 10
            consolidation_end = i - 1

            if consolidation_start < 0:
                continue

            consol_data = df.iloc[consolidation_start:consolidation_end + 1]

            # Identify consolidation (low volatility)
            consol_range = consol_data['high'].max() - consol_data['low'].min()
            avg_atr = df['atr'].iloc[consolidation_end]

            if consol_range > avg_atr * 1.5:  # Too wide to be consolidation
                continue

            # Check for sharp move away from consolidation
            move_start = consolidation_end + 1
            move_end = min(move_start + 5, len(df) - 1)
            move_data = df.iloc[move_start:move_end + 1]

            # Bullish move = demand zone created
            bullish_move = move_data['close'].iloc[-1] - consol_data['close'].iloc[-1]
            # Bearish move = supply zone created
            bearish_move = consol_data['close'].iloc[-1] - move_data['close'].iloc[-1]

            velocity = max(bullish_move, bearish_move)

            if velocity < avg_atr * self.min_velocity_atr:
                continue  # Move not strong enough

            # Create zone
            if bullish_move > bearish_move:
                # Demand zone (support)
                zone_type = ZoneType.DEMAND
                zone_bottom = consol_data['low'].min()
                zone_top = zone_bottom + (avg_atr * self.zone_width_atr)
            else:
                # Supply zone (resistance)
                zone_type = ZoneType.SUPPLY
                zone_top = consol_data['high'].max()
                zone_bottom = zone_top - (avg_atr * self.zone_width_atr)

            # Calculate strength metrics
            volume = consol_data['volume'].sum() if 'volume' in consol_data else 0
            time_in_zone = len(consol_data)

            zone = Zone(
                zone_type=zone_type,
                top=zone_top,
                bottom=zone_bottom,
                creation_time=df.index[consolidation_end],
                creation_idx=consolidation_end,
                velocity=velocity / avg_atr,  # Normalized velocity
                volume=volume,
                time_in_zone=time_in_zone
            )

            # Calculate strength score
            zone.strength = self._calculate_strength(zone, df, consolidation_end)

            zones.append(zone)

        # Update zone freshness based on retests
        zones = self._update_zone_freshness(zones, df)

        return zones

    def _add_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add ATR (Average True Range) to dataframe"""
        df = df.copy()

        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=period).mean()

        return df

    def _calculate_strength(
        self,
        zone: Zone,
        df: pd.DataFrame,
        creation_idx: int
    ) -> float:
        """Calculate zone strength score (0-1)"""

        # Normalize metrics
        max_velocity = 5.0  # ATR multiples
        velocity_score = min(zone.velocity / max_velocity, 1.0)

        max_time = 20  # candles
        time_score = min(zone.time_in_zone / max_time, 1.0)

        # Volume score (relative to recent average)
        if 'volume' in df.columns:
            recent_vol = df['volume'].iloc[max(0, creation_idx-50):creation_idx].mean()
            volume_score = min(zone.volume / (recent_vol * zone.time_in_zone + 1e-8), 1.0)
        else:
            volume_score = 0.5  # Neutral if no volume data

        # Touch score (initially 0, updated during retests)
        touch_score = 0.0

        # Weighted combination
        weights = self.strength_weights
        strength = (
            weights['velocity'] * velocity_score +
            weights['time'] * time_score +
            weights['volume'] * volume_score +
            weights['touch'] * touch_score
        )

        return strength

    def _update_zone_freshness(
        self,
        zones: List[Zone],
        df: pd.DataFrame
    ) -> List[Zone]:
        """Update zone freshness based on price retests"""

        for zone in zones:
            # Check all candles after zone creation
            test_data = df.iloc[zone.creation_idx + 1:]

            for idx, row in test_data.iterrows():
                if zone.zone_type == ZoneType.DEMAND:
                    # Price touched zone from above
                    if row['low'] <= zone.top and row['close'] > zone.bottom:
                        zone.touches += 1
                        zone.freshness = ZoneFreshness.TESTED
                    # Price broke through zone
                    elif row['close'] < zone.bottom:
                        zone.freshness = ZoneFreshness.BROKEN
                        break

                elif zone.zone_type == ZoneType.SUPPLY:
                    # Price touched zone from below
                    if row['high'] >= zone.bottom and row['close'] < zone.top:
                        zone.touches += 1
                        zone.freshness = ZoneFreshness.TESTED
                    # Price broke through zone
                    elif row['close'] > zone.top:
                        zone.freshness = ZoneFreshness.BROKEN
                        break

        return zones

    def get_active_zones(
        self,
        zones: List[Zone],
        current_idx: int,
        only_fresh: bool = False
    ) -> List[Zone]:
        """Get zones that are still active (not broken)"""

        active = [
            z for z in zones
            if z.freshness != ZoneFreshness.BROKEN
        ]

        if only_fresh:
            active = [
                z for z in active
                if z.is_fresh(current_idx, self.freshness_max_age)
            ]

        return active


def main():
    """Example usage"""
    # This would normally load from parquet files
    # For demo, create sample data
    dates = pd.date_range('2024-01-01', periods=500, freq='15min')
    np.random.seed(42)

    df = pd.DataFrame({
        'open': 1.1000 + np.random.randn(500).cumsum() * 0.0001,
        'high': 1.1000 + np.random.randn(500).cumsum() * 0.0001 + 0.0005,
        'low': 1.1000 + np.random.randn(500).cumsum() * 0.0001 - 0.0005,
        'close': 1.1000 + np.random.randn(500).cumsum() * 0.0001,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)

    # Ensure OHLC relationships
    df['high'] = df[['open', 'close']].max(axis=1) + abs(np.random.randn(500)) * 0.0002
    df['low'] = df[['open', 'close']].min(axis=1) - abs(np.random.randn(500)) * 0.0002

    # Detect zones
    detector = ZoneDetector()
    zones = detector.detect_zones(df)

    print(f"\nDetected {len(zones)} zones")
    print(f"Supply zones: {sum(1 for z in zones if z.zone_type == ZoneType.SUPPLY)}")
    print(f"Demand zones: {sum(1 for z in zones if z.zone_type == ZoneType.DEMAND)}")
    print(f"Fresh zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.FRESH)}")
    print(f"Tested zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.TESTED)}")
    print(f"Broken zones: {sum(1 for z in zones if z.freshness == ZoneFreshness.BROKEN)}")

    # Show strongest zones
    zones_by_strength = sorted(zones, key=lambda z: z.strength, reverse=True)
    print("\nTop 5 strongest zones:")
    for i, zone in enumerate(zones_by_strength[:5], 1):
        print(f"{i}. {zone.zone_type.value.upper()} - "
              f"Strength: {zone.strength:.3f}, "
              f"Touches: {zone.touches}, "
              f"Status: {zone.freshness.value}")


if __name__ == "__main__":
    main()
