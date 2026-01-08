"""
TradingView Indicator Backtest Engine

Tests the MomentumFX Order Block Zones indicator as a complete trading system.

CRITICAL: This tests if the indicator actually makes money.
We need honest results before releasing to traders.

Simulates:
1. Zone detection (M5/M15)
2. OB time filter (xx:55-05, xx:30±3)
3. H1 trend filter (ADX + DI)
4. Entry on zone retest
5. Stop loss (1.5 ATR below/above zone)
6. Take profit (TP1: 1.0 ATR, TP2: 2.5 ATR)
7. Breakeven move after TP1
"""

import sys
import os

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, parent_dir)

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

# Import research code from absolute paths
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load detector module
detector_path = os.path.join(parent_dir, 'code', 'zones', 'detector.py')
detector_module = load_module_from_path('detector', detector_path)
ZoneDetector = detector_module.ZoneDetector
Zone = detector_module.Zone
ZoneType = detector_module.ZoneType
ZoneFreshness = detector_module.ZoneFreshness

# Load time filter module
time_filter_path = os.path.join(parent_dir, 'code', 'zones', 'time_filter.py')
time_filter_module = load_module_from_path('time_filter', time_filter_path)
PeriodicOBFilter = time_filter_module.PeriodicOBFilter

# Load trend analyzer module
trend_path = os.path.join(parent_dir, 'code', 'strategies', 'trend_analyzer.py')
trend_module = load_module_from_path('trend_analyzer', trend_path)
TrendAnalyzer = trend_module.TrendAnalyzer
TrendDirection = trend_module.TrendDirection
RegimeType = trend_module.RegimeType


class TradeStatus(Enum):
    OPEN = "open"
    TP1_HIT = "tp1_hit"
    TP2_HIT = "tp2_hit"
    SL_HIT = "sl_hit"
    BREAKEVEN_HIT = "breakeven_hit"


@dataclass
class Trade:
    """Represents a single trade"""
    entry_time: pd.Timestamp
    entry_price: float
    direction: str  # 'long' or 'short'
    zone: Zone

    # Risk parameters
    stop_loss: float
    tp1: float
    tp2: float
    position_size: float  # % of account

    # Trade tracking
    status: TradeStatus = TradeStatus.OPEN
    exit_time: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    mae: float = 0.0  # Max Adverse Excursion
    mfe: float = 0.0  # Max Favorable Excursion

    # Metadata
    formed_in_ob: bool = False
    h1_trend: str = ""
    h1_adx: float = 0.0
    regime: str = ""

    def calculate_pnl(self, exit_price: float, atr: float) -> float:
        """Calculate PnL in R multiples"""
        risk = abs(self.entry_price - self.stop_loss)

        if self.direction == 'long':
            pnl_points = exit_price - self.entry_price
        else:  # short
            pnl_points = self.entry_price - exit_price

        r_multiple = pnl_points / risk if risk > 0 else 0
        return r_multiple

    def update_excursion(self, current_price: float):
        """Update MAE and MFE"""
        if self.direction == 'long':
            excursion = current_price - self.entry_price
        else:
            excursion = self.entry_price - current_price

        if excursion > 0:
            self.mfe = max(self.mfe, excursion)
        else:
            self.mae = min(self.mae, excursion)


@dataclass
class BacktestConfig:
    """Backtest configuration"""
    # Zone detection
    min_consolidation: int = 3
    zone_width_atr: float = 0.5
    min_velocity_atr: float = 1.0

    # Filters
    enable_ob_filter: bool = True
    enable_trend_filter: bool = True

    # Risk management
    risk_per_trade: float = 1.0  # % of account
    tp1_atr: float = 1.0
    tp2_atr: float = 2.5
    sl_atr: float = 1.5
    tp1_close_pct: float = 0.5  # Close 50% at TP1
    move_to_breakeven_at_tp1: bool = True

    # Trade management
    max_zone_age: int = 50  # bars
    retest_tolerance: float = 0.1  # % tolerance for zone retest

    # Account
    initial_capital: float = 10000.0
    max_trades_per_day: int = 3
    max_open_trades: int = 2


class BacktestEngine:
    """Backtests the TradingView indicator as a trading system"""

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()

        # Components
        self.zone_detector = ZoneDetector(
            min_consolidation_candles=self.config.min_consolidation,
            zone_width_atr=self.config.zone_width_atr,
            min_velocity_atr=self.config.min_velocity_atr,
            freshness_max_age=self.config.max_zone_age
        )
        self.ob_filter = PeriodicOBFilter(hourly_window_mins=5, half_hour_window_mins=3)
        self.trend_analyzer = TrendAnalyzer()

        # Trade tracking
        self.trades: List[Trade] = []
        self.open_trades: List[Trade] = []
        self.zones: List[Zone] = []

        # Account tracking
        self.capital = self.config.initial_capital
        self.equity_curve = []
        self.peak = self.config.initial_capital
        self.drawdown_curve = []

    def run_backtest(
        self,
        df_m5: pd.DataFrame,
        df_h1: pd.DataFrame,
        instrument: str = "UNKNOWN"
    ) -> Dict:
        """
        Run backtest on M5 data with H1 trend filter

        Args:
            df_m5: M5 OHLCV data
            df_h1: H1 OHLCV data for trend
            instrument: Instrument name

        Returns:
            Dictionary with backtest results
        """
        print(f"\n{'='*60}")
        print(f"BACKTESTING: {instrument}")
        print(f"Period: {df_m5.index[0]} to {df_m5.index[-1]}")
        print(f"Bars: {len(df_m5):,}")
        print(f"{'='*60}\n")

        # Reset
        self.trades = []
        self.open_trades = []
        self.zones = []
        self.capital = self.config.initial_capital
        self.equity_curve = []
        self.peak = self.config.initial_capital
        self.drawdown_curve = []

        # Step 1: Detect all zones
        print("Detecting zones...")
        all_zones = self.zone_detector.detect_zones(df_m5)
        print(f"  Total zones detected: {len(all_zones)}")

        # Filter by OB time if enabled
        if self.config.enable_ob_filter:
            ob_zones = [z for z in all_zones if self.ob_filter.is_ob_time(z.creation_time)]
            print(f"  Zones in OB windows: {len(ob_zones)} ({len(ob_zones)/len(all_zones)*100:.1f}%)")
            self.zones = ob_zones
        else:
            self.zones = all_zones

        # Step 2: Simulate trading
        print("\nSimulating trades...")
        trades_today = 0
        last_date = None

        for i in range(100, len(df_m5)):  # Start after warmup
            current_bar = df_m5.iloc[i]
            current_time = df_m5.index[i]
            current_date = current_time.date()

            # Reset daily trade counter
            if current_date != last_date:
                trades_today = 0
                last_date = current_date

            # Get H1 trend
            h1_idx = self._get_h1_index(df_h1, current_time)
            if h1_idx is None or h1_idx < 100:
                continue

            h1_trend = self.trend_analyzer.analyze(df_h1.iloc[:h1_idx+1])

            # Update open trades
            self._update_open_trades(current_bar, df_m5.iloc[i])

            # Check for new entries (zone retests)
            if (trades_today < self.config.max_trades_per_day and
                len(self.open_trades) < self.config.max_open_trades):

                new_trade = self._check_zone_retest(
                    current_bar=current_bar,
                    current_idx=i,
                    df=df_m5,
                    h1_trend=h1_trend
                )

                if new_trade:
                    self.open_trades.append(new_trade)
                    trades_today += 1

            # Update equity curve
            equity = self._calculate_equity(current_bar)
            self.equity_curve.append({
                'time': current_time,
                'equity': equity,
                'trades': len(self.trades),
                'open_trades': len(self.open_trades)
            })

            # Update drawdown
            self.peak = max(self.peak, equity)
            dd = (self.peak - equity) / self.peak * 100 if self.peak > 0 else 0
            self.drawdown_curve.append(dd)

        # Close any remaining open trades at end
        if self.open_trades:
            print(f"\nClosing {len(self.open_trades)} open trades at end...")
            final_bar = df_m5.iloc[-1]
            for trade in self.open_trades[:]:
                self._close_trade(trade, final_bar['close'], final_bar.name, "end_of_data")

        print(f"\n✓ Backtest complete!")
        print(f"  Total trades: {len(self.trades)}")

        # Calculate metrics
        results = self._calculate_metrics(instrument, df_m5)

        return results

    def _get_h1_index(self, df_h1: pd.DataFrame, current_time: pd.Timestamp) -> Optional[int]:
        """Get corresponding H1 bar index for current M5 time"""
        try:
            # Find the last H1 bar before or at current time
            h1_bars = df_h1[df_h1.index <= current_time]
            if len(h1_bars) > 0:
                return len(h1_bars) - 1
        except:
            pass
        return None

    def _check_zone_retest(
        self,
        current_bar: pd.Series,
        current_idx: int,
        df: pd.DataFrame,
        h1_trend: any
    ) -> Optional[Trade]:
        """Check if current bar retests a zone"""

        for zone in self.zones:
            # Zone too old?
            zone_age = current_idx - zone.creation_idx
            if zone_age > self.config.max_zone_age or zone_age < 5:
                continue

            # Zone already broken?
            if zone.freshness == ZoneFreshness.BROKEN:
                continue

            # Check if price is retesting zone
            is_retesting = False

            if zone.zone_type == ZoneType.DEMAND:
                # Long setup: price dips into demand zone
                if (current_bar['low'] <= zone.top and
                    current_bar['close'] > zone.bottom):

                    # Trend filter
                    if self.config.enable_trend_filter:
                        if h1_trend.direction != TrendDirection.BULLISH:
                            continue

                    # This is a buy setup
                    is_retesting = True
                    direction = 'long'
                    entry = zone.top  # Enter at top of zone
                    atr = df['atr'].iloc[current_idx]
                    sl = zone.bottom - (atr * self.config.sl_atr)
                    tp1 = entry + (atr * self.config.tp1_atr)
                    tp2 = entry + (atr * self.config.tp2_atr)

            elif zone.zone_type == ZoneType.SUPPLY:
                # Short setup: price rallies into supply zone
                if (current_bar['high'] >= zone.bottom and
                    current_bar['close'] < zone.top):

                    # Trend filter
                    if self.config.enable_trend_filter:
                        if h1_trend.direction != TrendDirection.BEARISH:
                            continue

                    # This is a sell setup
                    is_retesting = True
                    direction = 'short'
                    entry = zone.bottom  # Enter at bottom of zone
                    atr = df['atr'].iloc[current_idx]
                    sl = zone.top + (atr * self.config.sl_atr)
                    tp1 = entry - (atr * self.config.tp1_atr)
                    tp2 = entry - (atr * self.config.tp2_atr)

            if is_retesting:
                # Create trade
                trade = Trade(
                    entry_time=current_bar.name,
                    entry_price=entry,
                    direction=direction,
                    zone=zone,
                    stop_loss=sl,
                    tp1=tp1,
                    tp2=tp2,
                    position_size=self.config.risk_per_trade,
                    formed_in_ob=self.ob_filter.is_ob_time(zone.creation_time),
                    h1_trend=h1_trend.direction.value,
                    h1_adx=h1_trend.adx,
                    regime=h1_trend.regime.value
                )

                return trade

        return None

    def _update_open_trades(self, current_bar: pd.Series, bar_data: pd.Series):
        """Update all open trades (check SL/TP)"""

        for trade in self.open_trades[:]:  # Copy list to allow removal
            # Update MAE/MFE
            trade.update_excursion(current_bar['close'])

            # Check exits
            if trade.direction == 'long':
                # Check stop loss
                if current_bar['low'] <= trade.stop_loss:
                    self._close_trade(trade, trade.stop_loss, current_bar.name, "stop_loss")
                    continue

                # Check TP2
                if current_bar['high'] >= trade.tp2 and trade.status != TradeStatus.TP2_HIT:
                    self._close_trade(trade, trade.tp2, current_bar.name, "tp2")
                    continue

                # Check TP1
                if current_bar['high'] >= trade.tp1 and trade.status == TradeStatus.OPEN:
                    # Close 50%, move SL to breakeven
                    trade.status = TradeStatus.TP1_HIT
                    trade.position_size *= (1 - self.config.tp1_close_pct)

                    if self.config.move_to_breakeven_at_tp1:
                        trade.stop_loss = trade.entry_price

            else:  # short
                # Check stop loss
                if current_bar['high'] >= trade.stop_loss:
                    self._close_trade(trade, trade.stop_loss, current_bar.name, "stop_loss")
                    continue

                # Check TP2
                if current_bar['low'] <= trade.tp2 and trade.status != TradeStatus.TP2_HIT:
                    self._close_trade(trade, trade.tp2, current_bar.name, "tp2")
                    continue

                # Check TP1
                if current_bar['low'] <= trade.tp1 and trade.status == TradeStatus.OPEN:
                    # Close 50%, move SL to breakeven
                    trade.status = TradeStatus.TP1_HIT
                    trade.position_size *= (1 - self.config.tp1_close_pct)

                    if self.config.move_to_breakeven_at_tp1:
                        trade.stop_loss = trade.entry_price

    def _close_trade(self, trade: Trade, exit_price: float, exit_time: pd.Timestamp, reason: str):
        """Close a trade and update account"""

        trade.exit_time = exit_time
        trade.exit_price = exit_price

        # Calculate PnL in R
        risk = abs(trade.entry_price - trade.stop_loss)
        if trade.direction == 'long':
            pnl_points = exit_price - trade.entry_price
        else:
            pnl_points = trade.entry_price - exit_price

        r_multiple = pnl_points / risk if risk > 0 else 0
        trade.pnl = r_multiple

        # Update capital (R multiples * risk per trade)
        capital_risked = self.capital * (trade.position_size / 100)
        pnl_dollars = r_multiple * capital_risked
        self.capital += pnl_dollars

        # Mark as closed
        if reason == "stop_loss":
            trade.status = TradeStatus.SL_HIT
        elif reason == "tp2":
            trade.status = TradeStatus.TP2_HIT

        # Remove from open trades
        if trade in self.open_trades:
            self.open_trades.remove(trade)

        # Add to closed trades
        self.trades.append(trade)

    def _calculate_equity(self, current_bar: pd.Series) -> float:
        """Calculate current equity including open trades"""
        equity = self.capital

        # Add unrealized P&L from open trades
        for trade in self.open_trades:
            risk = abs(trade.entry_price - trade.stop_loss)
            if trade.direction == 'long':
                pnl_points = current_bar['close'] - trade.entry_price
            else:
                pnl_points = trade.entry_price - current_bar['close']

            r_multiple = pnl_points / risk if risk > 0 else 0
            capital_risked = self.config.initial_capital * (trade.position_size / 100)
            unrealized_pnl = r_multiple * capital_risked
            equity += unrealized_pnl

        return equity

    def _calculate_metrics(self, instrument: str, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive backtest metrics"""

        if len(self.trades) == 0:
            return {
                'instrument': instrument,
                'total_trades': 0,
                'error': 'No trades generated'
            }

        # Basic stats
        total_trades = len(self.trades)
        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl <= 0]

        win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0

        # P&L stats
        total_pnl_r = sum(t.pnl for t in self.trades)
        avg_win_r = np.mean([t.pnl for t in wins]) if wins else 0
        avg_loss_r = np.mean([t.pnl for t in losses]) if losses else 0

        # Profit factor
        gross_profit = sum(t.pnl for t in wins) if wins else 0
        gross_loss = abs(sum(t.pnl for t in losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Expectancy
        expectancy = (win_rate/100 * avg_win_r) + ((1 - win_rate/100) * avg_loss_r)

        # Drawdown
        max_dd = max(self.drawdown_curve) if self.drawdown_curve else 0

        # Consecutive stats
        consecutive_wins = self._max_consecutive(wins, all_trades=self.trades)
        consecutive_losses = self._max_consecutive(losses, all_trades=self.trades)

        # Return
        final_capital = self.equity_curve[-1]['equity'] if self.equity_curve else self.config.initial_capital
        total_return_pct = (final_capital - self.config.initial_capital) / self.config.initial_capital * 100

        # Sharpe (simplified - using trade returns)
        trade_returns = [t.pnl for t in self.trades]
        sharpe = np.mean(trade_returns) / np.std(trade_returns) if len(trade_returns) > 1 and np.std(trade_returns) > 0 else 0

        # OB zone stats
        ob_trades = [t for t in self.trades if t.formed_in_ob]
        ob_win_rate = len([t for t in ob_trades if t.pnl > 0]) / len(ob_trades) * 100 if ob_trades else 0

        # Duration
        duration_days = (df.index[-1] - df.index[0]).days
        trades_per_month = total_trades / (duration_days / 30) if duration_days > 0 else 0

        results = {
            'instrument': instrument,
            'period': f"{df.index[0].date()} to {df.index[-1].date()}",
            'duration_days': duration_days,
            'bars': len(df),

            # Trade stats
            'total_trades': total_trades,
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'trades_per_month': trades_per_month,

            # P&L
            'total_pnl_r': total_pnl_r,
            'avg_win_r': avg_win_r,
            'avg_loss_r': avg_loss_r,
            'profit_factor': profit_factor,
            'expectancy_r': expectancy,

            # Risk metrics
            'max_drawdown_pct': max_dd,
            'sharpe_ratio': sharpe,

            # Return
            'initial_capital': self.config.initial_capital,
            'final_capital': final_capital,
            'total_return_pct': total_return_pct,

            # Consecutive
            'max_consecutive_wins': consecutive_wins,
            'max_consecutive_losses': consecutive_losses,

            # OB stats
            'ob_trades': len(ob_trades),
            'ob_pct': len(ob_trades) / total_trades * 100 if total_trades > 0 else 0,
            'ob_win_rate': ob_win_rate,

            # Trade lists
            'all_trades': self.trades,
            'equity_curve': self.equity_curve
        }

        return results

    def _max_consecutive(self, subset: List[Trade], all_trades: List[Trade]) -> int:
        """Calculate max consecutive wins or losses"""
        if not all_trades:
            return 0

        max_consecutive = 0
        current_consecutive = 0

        for trade in all_trades:
            if trade in subset:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive


def main():
    """Example usage"""
    # This would load actual M5 and H1 data
    print("Backtest Engine Ready")
    print("\nTo use:")
    print("1. Load M5 and H1 data")
    print("2. Create BacktestConfig")
    print("3. Run backtest")
    print("4. Analyze results")


if __name__ == "__main__":
    main()
