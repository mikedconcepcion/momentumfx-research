# TradingView Indicator Validation

## Purpose

This validation system tests the **MomentumFX Order Block Zones indicator as a complete trading system** before release.

**Critical**: We validate to ensure the indicator doesn't lose traders' money. If backtest results are poor, we **DO NOT release** until improved.

---

## What Gets Tested

### 1. Zone Detection + Entry Logic
- Consolidation → breakout zone detection
- Zone retest entry simulation
- OB time window filter (xx:55-05, xx:30±3)
- H1 trend filter (ADX + Directional Indicators)

### 2. Risk Management
- Stop loss: 1.5 ATR beyond zone
- TP1: 1.0 ATR (close 50%, move to BE)
- TP2: 2.5 ATR (close remaining 50%)
- Position sizing: 1% risk per trade

### 3. Multiple Instruments
- XAUUSD (Gold) - Primary (95.3% OB concentration from research)
- EURUSD - Secondary (80% OB concentration)
- USDJPY - Secondary (71.4% OB concentration)

### 4. Multiple Time Periods
- COVID Period (2020-2021) - Highest volatility
- Post-COVID (2022-2023) - Ranging/consolidation
- Recent (2024-2025) - Current conditions
- Full 6-Year (2020-2025) - Complete dataset

### 5. Multiple Configurations
- Default: OB Filter + Trend Filter
- OB Filter Only
- Trend Filter Only
- No Filters (baseline)

---

## Files

### `backtest_engine.py`
Core backtesting engine that:
- Simulates zone detection on M5 data
- Applies OB time filter
- Applies H1 trend filter
- Simulates trade entry on zone retest
- Manages stops and targets
- Tracks P&L, equity curve, drawdown

### `run_validation.py`
Validation runner that:
- Loads historical M5 and H1 data
- Runs backtests across instruments and periods
- Generates comprehensive validation report
- Provides honest assessment of results

### `VALIDATION_REPORT.md`
Generated report showing:
- Win rate, profit factor, expectancy
- Maximum drawdown, Sharpe ratio
- Total return, trade count
- Configuration comparisons
- Period-by-period breakdown
- **Honest assessment**: ✅ Good / ⚠️ Acceptable / ❌ Poor

---

## How to Run

### Quick Start

```bash
cd tradingview/validation
python run_validation.py
```

This will:
1. Test XAUUSD, EURUSD, USDJPY
2. Test all 4 configurations per instrument
3. Test XAUUSD across 4 time periods
4. Generate `VALIDATION_REPORT.md`

### Custom Tests

```python
from run_validation import load_data, run_instrument_validation

# Test specific instrument and period
df_m5, df_h1 = load_data('XAUUSD', '2020-01-01', '2021-12-31')

# Run with custom config
from backtest_engine import BacktestEngine, BacktestConfig

config = BacktestConfig(
    enable_ob_filter=True,
    enable_trend_filter=True,
    risk_per_trade=1.0  # 1% risk
)

engine = BacktestEngine(config)
results = engine.run_backtest(df_m5, df_h1, 'XAUUSD')
```

---

## Interpreting Results

### Minimum Acceptable Metrics

For an indicator to be **safe to release**:

| Metric | Minimum | Preferred |
|--------|---------|-----------|
| **Profit Factor** | >= 1.2 | >= 1.5 |
| **Win Rate** | >= 40% | >= 50% |
| **Expectancy** | > 0 R | > 0.2 R |
| **Max Drawdown** | < 25% | < 15% |
| **Sample Size** | >= 30 trades | >= 100 trades |

### Status Indicators

**✅ GOOD**: Metric meets preferred threshold
**⚠️ ACCEPTABLE**: Metric meets minimum but below preferred
**❌ POOR**: Metric below minimum threshold

---

## What to Do Based on Results

### ✅ If All Metrics Are Good

**Proceed with release**:
1. Document actual backtest results in indicator guide
2. Add clear disclaimers about past performance
3. Recommend paper trading before live
4. Include backtest report in repository

### ⚠️ If Metrics Are Acceptable

**Conditional release**:
1. Clearly state metrics in documentation
2. Emphasize this is a **filter**, not complete system
3. Require strict confirmation signals
4. Recommend reduced position sizing
5. Extended paper trading period

### ❌ If Metrics Are Poor

**DO NOT RELEASE**:
1. Analyze why performance is poor
2. Improve indicator logic:
   - Adjust zone detection parameters
   - Improve entry timing
   - Better trend filtering
   - Optimize stop loss / take profit levels
3. Re-run validation
4. Only release when metrics improve

---

## Common Issues and Solutions

### Issue: Very Few Trades Generated

**Causes**:
- Filters too strict (OB + Trend together)
- Zone detection parameters too conservative
- Entry logic too selective

**Solutions**:
- Test with filters off to see baseline
- Adjust `min_velocity_atr` down to 0.7-0.8
- Reduce `min_consolidation` to 2 candles
- Increase `retest_tolerance` to 0.2

### Issue: Win Rate < 40%

**Causes**:
- Entry timing poor
- Stop loss too tight
- Trend filter not effective

**Solutions**:
- Analyze losing trades for patterns
- Increase stop loss to 2.0 ATR
- Strengthen trend filter (ADX > 30)
- Add additional confirmation signals

### Issue: Profit Factor < 1.2

**Causes**:
- Risk:Reward ratio poor
- Not riding winners
- Cutting winners too early

**Solutions**:
- Extend TP2 to 3.0+ ATR
- Trail stop more conservatively
- Only take trades with 2:1+ R:R potential
- Add partial position sizing

### Issue: Max Drawdown > 25%

**Causes**:
- Position sizing too aggressive
- No maximum exposure limits
- Consecutive losses not managed

**Solutions**:
- Reduce `risk_per_trade` to 0.5-0.75%
- Implement `max_open_trades` limit
- Add daily/weekly loss limits
- Require stronger trend confirmation

---

## Understanding Trade Data

Each trade object contains:

```python
@dataclass
class Trade:
    entry_time: timestamp
    entry_price: float
    direction: 'long' or 'short'

    # Levels
    stop_loss: float
    tp1: float (1.0 ATR)
    tp2: float (2.5 ATR)

    # Results
    exit_time: timestamp
    exit_price: float
    pnl: float (in R multiples)
    status: 'tp1_hit', 'tp2_hit', 'sl_hit', etc.

    # Analysis
    mae: Max Adverse Excursion
    mfe: Max Favorable Excursion
    formed_in_ob: bool (zone formed during OB window)
    h1_trend: 'bullish', 'bearish', 'neutral'
    h1_adx: float
    regime: 'trending', 'ranging', 'volatile'
```

---

## Export Results for Analysis

```python
# After running validation
import pandas as pd

# Convert trades to DataFrame
trades_df = pd.DataFrame([vars(t) for t in engine.trades])

# Export to CSV
trades_df.to_csv('trade_log.csv', index=False)

# Equity curve
equity_df = pd.DataFrame(engine.equity_curve)
equity_df.to_csv('equity_curve.csv', index=False)

# Analyze by regime
regime_stats = trades_df.groupby('regime').agg({
    'pnl': ['count', 'mean', 'sum'],
    'formed_in_ob': 'mean'
})
print(regime_stats)
```

---

## Validation Checklist

Before releasing indicator:

- [ ] Run full validation suite
- [ ] Review `VALIDATION_REPORT.md`
- [ ] Check all instruments meet minimums
- [ ] Verify sample sizes adequate (>30 trades)
- [ ] Test best configuration on out-of-sample data
- [ ] Document honest results in indicator guide
- [ ] Add disclaimers about past performance
- [ ] Recommend paper trading period
- [ ] If metrics poor, improve and re-validate

---

## Honesty Policy

**We do NOT**:
- Cherry-pick favorable periods
- Hide poor results
- Over-optimize on test data
- Release indicators that lose money
- Make guarantees about future performance

**We DO**:
- Show all results (good and bad)
- Test across multiple periods and instruments
- Report drawdowns and losing streaks
- Acknowledge limitations
- Recommend paper trading
- Warn about risks

---

## Contact

If validation reveals issues or you need help improving the indicator:

**Email**: momentumfxtrading25@gmail.com
**Research**: https://mikedconcepcion.github.io/momentumfx-research/

---

**Remember**: The goal is to release a tool that HELPS traders, not one that loses them money.

If backtest results are poor, we improve the indicator or don't release it.

Integrity > Everything.
