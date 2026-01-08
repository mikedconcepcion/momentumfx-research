"""
Multi-Timeframe Trend Analyzer

Identifies trend direction and strength across multiple timeframes.
Aligns with State Space Ontology - regime-conditional analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from enum import Enum
from dataclasses import dataclass


class TrendDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class RegimeType(Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"


@dataclass
class TrendState:
    """Represents trend state on a specific timeframe"""
    direction: TrendDirection
    regime: RegimeType
    strength: float  # 0-1
    adx: float
    hurst: float = 0.5


class TrendAnalyzer:
    """Multi-timeframe trend detection"""

    def __init__(
        self,
        adx_period: int = 14,
        adx_threshold: float = 25.0,
        hurst_period: int = 100,
        hurst_trending: float = 0.55,
        hurst_ranging: float = 0.45
    ):
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.hurst_period = hurst_period
        self.hurst_trending = hurst_trending
        self.hurst_ranging = hurst_ranging

    def analyze(self, df: pd.DataFrame) -> TrendState:
        """
        Analyze trend for a single timeframe

        Args:
            df: DataFrame with OHLC data

        Returns:
            TrendState object
        """
        # Calculate indicators
        df = self._add_adx(df)
        df = self._add_moving_averages(df)

        # Get latest values
        latest_adx = df['adx'].iloc[-1]
        latest_plus_di = df['plus_di'].iloc[-1]
        latest_minus_di = df['minus_di'].iloc[-1]

        # Determine trend direction
        if latest_plus_di > latest_minus_di:
            direction = TrendDirection.BULLISH
        elif latest_minus_di > latest_plus_di:
            direction = TrendDirection.BEARISH
        else:
            direction = TrendDirection.NEUTRAL

        # Calculate Hurst exponent for regime
        hurst = self._calculate_hurst(df['close'].values[-self.hurst_period:])

        # Determine regime
        if latest_adx > self.adx_threshold and hurst > self.hurst_trending:
            regime = RegimeType.TRENDING
        elif latest_adx < self.adx_threshold and hurst < self.hurst_ranging:
            regime = RegimeType.RANGING
        else:
            regime = RegimeType.VOLATILE

        # Trend strength (normalized ADX)
        strength = min(latest_adx / 50.0, 1.0)  # Normalize to 0-1

        return TrendState(
            direction=direction,
            regime=regime,
            strength=strength,
            adx=latest_adx,
            hurst=hurst
        )

    def _add_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX and directional indicators"""
        df = df.copy()

        # True Range
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = pd.Series(0.0, index=df.index)
        minus_dm = pd.Series(0.0, index=df.index)

        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

        # Smoothed indicators
        atr = tr.rolling(window=self.adx_period).mean()
        plus_di = 100 * (plus_dm.rolling(window=self.adx_period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=self.adx_period).mean() / atr)

        # ADX calculation
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=self.adx_period).mean()

        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        df['adx'] = adx
        df['atr'] = atr

        return df

    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add moving averages for trend confirmation"""
        df = df.copy()

        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()

        return df

    def _calculate_hurst(self, prices: np.ndarray) -> float:
        """
        Calculate Hurst exponent for mean reversion/trending detection

        H < 0.5: Mean reverting
        H = 0.5: Random walk
        H > 0.5: Trending
        """
        if len(prices) < 20:
            return 0.5

        # Use rescaled range analysis
        lags = range(2, min(100, len(prices) // 2))
        tau = []
        rs = []

        for lag in lags:
            # Split into chunks
            chunks = [prices[i:i+lag] for i in range(0, len(prices), lag) if len(prices[i:i+lag]) == lag]

            if len(chunks) == 0:
                continue

            rs_values = []
            for chunk in chunks:
                mean = np.mean(chunk)
                deviation = chunk - mean
                cumdev = np.cumsum(deviation)

                R = np.max(cumdev) - np.min(cumdev)
                S = np.std(chunk)

                if S > 0:
                    rs_values.append(R / S)

            if len(rs_values) > 0:
                tau.append(lag)
                rs.append(np.mean(rs_values))

        if len(tau) < 2:
            return 0.5

        # Linear regression in log-log space
        log_tau = np.log10(tau)
        log_rs = np.log10(rs)

        # Hurst exponent is the slope
        hurst = np.polyfit(log_tau, log_rs, 1)[0]

        # Clamp to reasonable range
        return max(0.0, min(1.0, hurst))


class MultiTimeframeTrend:
    """Analyze trend across multiple timeframes"""

    def __init__(
        self,
        timeframes: Dict[str, pd.DataFrame],
        analyzer: TrendAnalyzer = None
    ):
        """
        Args:
            timeframes: Dict mapping timeframe name to DataFrame
                       e.g., {'M15': df_m15, 'H1': df_h1, 'H4': df_h4}
            analyzer: TrendAnalyzer instance (creates default if None)
        """
        self.timeframes = timeframes
        self.analyzer = analyzer or TrendAnalyzer()
        self.trends: Dict[str, TrendState] = {}

    def analyze_all(self) -> Dict[str, TrendState]:
        """Analyze trend on all timeframes"""
        for tf_name, df in self.timeframes.items():
            self.trends[tf_name] = self.analyzer.analyze(df)
        return self.trends

    def is_aligned(self, required_timeframes: int = 2) -> bool:
        """Check if trend is aligned across timeframes"""
        if len(self.trends) < required_timeframes:
            return False

        directions = [t.direction for t in self.trends.values()]

        # Count dominant direction
        bullish_count = directions.count(TrendDirection.BULLISH)
        bearish_count = directions.count(TrendDirection.BEARISH)

        return max(bullish_count, bearish_count) >= required_timeframes

    def get_dominant_direction(self) -> TrendDirection:
        """Get the dominant trend direction across timeframes"""
        if not self.trends:
            return TrendDirection.NEUTRAL

        directions = [t.direction for t in self.trends.values()]
        bullish = directions.count(TrendDirection.BULLISH)
        bearish = directions.count(TrendDirection.BEARISH)

        if bullish > bearish:
            return TrendDirection.BULLISH
        elif bearish > bullish:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.NEUTRAL

    def get_dominant_regime(self) -> RegimeType:
        """Get the dominant regime across timeframes"""
        if not self.trends:
            return RegimeType.RANGING

        regimes = [t.regime for t in self.trends.values()]

        # Higher timeframe regime takes precedence
        # Assume timeframes are ordered from lower to higher
        return list(self.trends.values())[-1].regime

    def get_average_strength(self) -> float:
        """Get average trend strength across timeframes"""
        if not self.trends:
            return 0.0
        return np.mean([t.strength for t in self.trends.values()])


def main():
    """Example usage"""
    # Generate sample data
    dates = pd.date_range('2024-01-01', periods=500, freq='15min')
    np.random.seed(42)

    # Create trending data
    trend = np.linspace(0, 0.01, 500)
    noise = np.random.randn(500) * 0.0001

    df = pd.DataFrame({
        'open': 1.1000 + trend + noise,
        'high': 1.1000 + trend + noise + 0.0005,
        'low': 1.1000 + trend + noise - 0.0005,
        'close': 1.1000 + trend + noise,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)

    # Fix OHLC relationships
    df['high'] = df[['open', 'close']].max(axis=1) + abs(np.random.randn(500)) * 0.0002
    df['low'] = df[['open', 'close']].min(axis=1) - abs(np.random.randn(500)) * 0.0002

    # Single timeframe analysis
    analyzer = TrendAnalyzer()
    trend_state = analyzer.analyze(df)

    print("Single Timeframe Analysis:")
    print(f"Direction: {trend_state.direction.value}")
    print(f"Regime: {trend_state.regime.value}")
    print(f"Strength: {trend_state.strength:.3f}")
    print(f"ADX: {trend_state.adx:.2f}")
    print(f"Hurst: {trend_state.hurst:.3f}")

    # Multi-timeframe (demo with same data)
    mtf = MultiTimeframeTrend({
        'M15': df,
        'H1': df.resample('1H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna(),
        'H4': df.resample('4H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    })

    mtf.analyze_all()

    print("\n\nMulti-Timeframe Analysis:")
    print(f"Aligned: {mtf.is_aligned()}")
    print(f"Dominant Direction: {mtf.get_dominant_direction().value}")
    print(f"Dominant Regime: {mtf.get_dominant_regime().value}")
    print(f"Average Strength: {mtf.get_average_strength():.3f}")

    print("\nPer-Timeframe:")
    for tf, state in mtf.trends.items():
        print(f"  {tf}: {state.direction.value} ({state.regime.value}) - "
              f"Strength: {state.strength:.3f}")


if __name__ == "__main__":
    main()
