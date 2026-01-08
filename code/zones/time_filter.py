"""
Time-Based Order Block Filter

Periodic Order Block (OB) patterns confirmed in XAUUSD:
- xx:55 - xx:05 (hourly turn zone)
- xx:30 +/- 2-3 minutes (half-hour zone)

These times show higher probability of institutional order blocks.
Aligns with State Space Ontology - temporal regimes matter.
"""

import pandas as pd
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum


class TimeZone(Enum):
    HOURLY_TURN = "hourly_turn"     # xx:55 - xx:05
    HALF_HOUR = "half_hour"          # xx:30 +/- 2-3 min
    OTHER = "other"


@dataclass
class TimeWindow:
    """Represents a periodic time window for OB detection"""
    name: str
    minute_ranges: List[Tuple[int, int]]  # List of (start_min, end_min) tuples
    zone_type: TimeZone

    def is_active(self, timestamp: pd.Timestamp) -> bool:
        """Check if timestamp falls within this time window"""
        minute = timestamp.minute

        for start, end in self.minute_ranges:
            if start <= end:
                # Normal range (e.g., 30-33)
                if start <= minute <= end:
                    return True
            else:
                # Range wraps around hour (e.g., 55-5)
                if minute >= start or minute <= end:
                    return True

        return False


class PeriodicOBFilter:
    """Filter for time-based Order Block patterns"""

    def __init__(
        self,
        hourly_window_mins: int = 5,    # xx:55 to xx:05 (5 mins each side)
        half_hour_window_mins: int = 3   # xx:30 +/- 3 mins
    ):
        """
        Args:
            hourly_window_mins: Minutes before/after hour turn
            half_hour_window_mins: Minutes around half-hour mark
        """
        self.hourly_window_mins = hourly_window_mins
        self.half_hour_window_mins = half_hour_window_mins

        # Define time windows
        self.windows = [
            TimeWindow(
                name="Hourly Turn",
                minute_ranges=[
                    (60 - hourly_window_mins, 59),  # xx:55-xx:59
                    (0, hourly_window_mins)          # xx:00-xx:05
                ],
                zone_type=TimeZone.HOURLY_TURN
            ),
            TimeWindow(
                name="Half Hour",
                minute_ranges=[
                    (30 - half_hour_window_mins, 30 + half_hour_window_mins)  # xx:27-xx:33
                ],
                zone_type=TimeZone.HALF_HOUR
            )
        ]

    def get_time_zone(self, timestamp: pd.Timestamp) -> TimeZone:
        """Identify which time zone a timestamp belongs to"""
        for window in self.windows:
            if window.is_active(timestamp):
                return window.zone_type

        return TimeZone.OTHER

    def is_ob_time(self, timestamp: pd.Timestamp) -> bool:
        """Check if timestamp falls within OB window"""
        return self.get_time_zone(timestamp) != TimeZone.OTHER

    def filter_dataframe(
        self,
        df: pd.DataFrame,
        only_ob_times: bool = True
    ) -> pd.DataFrame:
        """
        Filter dataframe by OB time windows

        Args:
            df: DataFrame with timestamp index
            only_ob_times: If True, keep only OB times; if False, exclude them

        Returns:
            Filtered DataFrame
        """
        df = df.copy()

        # Add time zone classification
        df['time_zone'] = df.index.map(self.get_time_zone)

        if only_ob_times:
            # Keep only OB times
            df = df[df['time_zone'] != TimeZone.OTHER]
        else:
            # Exclude OB times
            df = df[df['time_zone'] == TimeZone.OTHER]

        return df

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add time-based features to dataframe

        Args:
            df: DataFrame with timestamp index

        Returns:
            DataFrame with additional time features
        """
        df = df.copy()

        # Time zone classification
        df['time_zone'] = df.index.map(self.get_time_zone)

        # Binary flags
        df['is_hourly_turn'] = df['time_zone'] == TimeZone.HOURLY_TURN
        df['is_half_hour'] = df['time_zone'] == TimeZone.HALF_HOUR
        df['is_ob_time'] = df['time_zone'] != TimeZone.OTHER

        # Minute of hour
        df['minute'] = df.index.minute

        # Hour of day (for session analysis)
        df['hour'] = df.index.hour

        return df

    def get_ob_statistics(self, df: pd.DataFrame) -> dict:
        """
        Get statistics about OB time windows

        Args:
            df: DataFrame with timestamp index

        Returns:
            Dictionary with statistics
        """
        df = self.add_time_features(df)

        total_bars = len(df)
        hourly_turn_bars = df['is_hourly_turn'].sum()
        half_hour_bars = df['is_half_hour'].sum()
        ob_bars = df['is_ob_time'].sum()
        other_bars = total_bars - ob_bars

        stats = {
            'total_bars': total_bars,
            'hourly_turn_bars': hourly_turn_bars,
            'hourly_turn_pct': hourly_turn_bars / total_bars * 100,
            'half_hour_bars': half_hour_bars,
            'half_hour_pct': half_hour_bars / total_bars * 100,
            'ob_bars': ob_bars,
            'ob_pct': ob_bars / total_bars * 100,
            'other_bars': other_bars,
            'other_pct': other_bars / total_bars * 100
        }

        return stats


class SessionFilter:
    """Filter for trading session times (London, NY, Asia)"""

    def __init__(self, timezone: str = 'UTC'):
        """
        Args:
            timezone: Timezone for session times (default UTC)
        """
        self.timezone = timezone

        # Define major session times (UTC)
        self.sessions = {
            'asian': (0, 9),      # 00:00-09:00 UTC
            'london': (8, 17),    # 08:00-17:00 UTC
            'new_york': (13, 22), # 13:00-22:00 UTC
        }

    def get_session(self, timestamp: pd.Timestamp) -> str:
        """Get the trading session for a timestamp"""
        hour = timestamp.hour

        # Check for overlaps (priority to most active)
        if self.sessions['london'][0] <= hour < self.sessions['london'][1]:
            if self.sessions['new_york'][0] <= hour < self.sessions['new_york'][1]:
                return 'london_ny_overlap'
            return 'london'

        if self.sessions['new_york'][0] <= hour < self.sessions['new_york'][1]:
            return 'new_york'

        if self.sessions['asian'][0] <= hour < self.sessions['asian'][1]:
            return 'asian'

        return 'other'

    def add_session_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add session-based features to dataframe"""
        df = df.copy()

        df['session'] = df.index.map(self.get_session)
        df['is_london'] = df['session'].isin(['london', 'london_ny_overlap'])
        df['is_new_york'] = df['session'].isin(['new_york', 'london_ny_overlap'])
        df['is_overlap'] = df['session'] == 'london_ny_overlap'

        return df


def main():
    """Example usage"""
    # Generate sample M5 data
    dates = pd.date_range('2024-01-01', periods=1000, freq='5min')
    df = pd.DataFrame({
        'close': 1.1000 + pd.Series(range(1000)) * 0.00001
    }, index=dates)

    print("Periodic OB Filter Demo\n")

    # Initialize filter
    ob_filter = PeriodicOBFilter(
        hourly_window_mins=5,
        half_hour_window_mins=3
    )

    # Get statistics
    stats = ob_filter.get_ob_statistics(df)
    print("Time Window Statistics:")
    print(f"  Total bars: {stats['total_bars']}")
    print(f"  Hourly turn bars: {stats['hourly_turn_bars']} ({stats['hourly_turn_pct']:.1f}%)")
    print(f"  Half-hour bars: {stats['half_hour_bars']} ({stats['half_hour_pct']:.1f}%)")
    print(f"  All OB bars: {stats['ob_bars']} ({stats['ob_pct']:.1f}%)")
    print(f"  Other bars: {stats['other_bars']} ({stats['other_pct']:.1f}%)")

    # Add features
    df = ob_filter.add_time_features(df)

    print("\n\nSample timestamps and their time zones:")
    sample_times = [
        pd.Timestamp('2024-01-01 00:00:00'),
        pd.Timestamp('2024-01-01 00:03:00'),
        pd.Timestamp('2024-01-01 00:10:00'),
        pd.Timestamp('2024-01-01 00:28:00'),
        pd.Timestamp('2024-01-01 00:30:00'),
        pd.Timestamp('2024-01-01 00:33:00'),
        pd.Timestamp('2024-01-01 00:55:00'),
        pd.Timestamp('2024-01-01 01:02:00'),
    ]

    for ts in sample_times:
        zone = ob_filter.get_time_zone(ts)
        print(f"  {ts.strftime('%H:%M')} -> {zone.value}")

    # Session filter demo
    print("\n\nSession Filter Demo\n")
    session_filter = SessionFilter()

    df = session_filter.add_session_features(df)

    session_counts = df['session'].value_counts()
    print("Session distribution:")
    for session, count in session_counts.items():
        pct = count / len(df) * 100
        print(f"  {session}: {count} bars ({pct:.1f}%)")

    # Filter only OB times
    ob_only = ob_filter.filter_dataframe(df, only_ob_times=True)
    print(f"\n\nFiltered to OB times only: {len(ob_only)} / {len(df)} bars ({len(ob_only)/len(df)*100:.1f}%)")


if __name__ == "__main__":
    main()
