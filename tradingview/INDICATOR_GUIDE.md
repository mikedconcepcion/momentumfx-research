# Momentum FX - Order Block Zones Indicator
## TradingView Pine Script v5

**Based on 6-Year Validation Study (2020-2025)**

---

## 📊 Research Foundation

This indicator is based on rigorous academic research validating periodic institutional order flow patterns:

- **Dataset**: 2.4 million bars across 6 years (2020-2025)
- **Statistical Confidence**: 99.9%+ (p < 0.001)
- **Key Finding**: Supply-demand zones form **2.56x more frequently** during Order Block (OB) time windows
- **COVID-19 Tested**: Pattern **strengthened** during March 2020 crash (2.80x concentration)
- **Best Instrument**: XAUUSD (Gold) with 95.3% OB concentration

📖 **Full Research**: https://mikedconcepcion.github.io/momentumfx-research/

---

## 🎯 What This Indicator Does

### Multi-Timeframe Approach (As Recommended by Research)

1. **M5 (5-min)**: Zone Detection
   - Detects supply (resistance) and demand (support) zones
   - Identifies consolidation → breakout patterns
   - Shows "BUY ZONE" and "SELL ZONE" labels

2. **M15 (15-min)**: Primary Analysis
   - Recommended primary timeframe for chart viewing
   - Balance between granularity and noise reduction

3. **H1 (1-hour)**: Trend Filter
   - Uses ADX and Directional Indicators
   - Filters zones to align with higher timeframe trend
   - Shows trend direction in dashboard

### Order Block (OB) Time Windows

The indicator highlights periodic time windows when zones form with highest probability:

**Hourly Turns**: `xx:55 - xx:05 UTC`
- 10 minutes per hour
- Covers major hourly transitions
- Most critical window

**Half-Hourly**: `xx:30 ± 3 UTC` (xx:27-xx:33)
- 7 minutes per hour
- Secondary window
- Additional zone formation periods

**Total Coverage**: 33.3% of time captures **85.4%** of quality zones

---

## ⚙️ Installation

1. **Open TradingView**
2. **Pine Editor**: Click "Pine Editor" at bottom of chart
3. **New Indicator**: Click "New" button
4. **Paste Code**: Delete template code, paste `MomentumFX_OrderBlock_Zones.pine`
5. **Save**: Click "Save" (give it a name)
6. **Add to Chart**: Click "Add to Chart"

---

## 🔧 Settings Guide

### 1. Zone Detection Settings

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| **Min Consolidation Candles** | 3 | 2-10 | Minimum bars in consolidation before breakout |
| **Zone Width (ATR)** | 0.5 | 0.1-2.0 | Zone height as ATR multiple (validated: 0.5) |
| **Min Breakout Velocity (ATR)** | 1.0 | 0.5-3.0 | Minimum breakout strength (validated: 1.0) |
| **Max Zone Age (bars)** | 50 | 10-200 | How long to display zones before removal |

**Recommendations**:
- **Keep defaults** for Gold (XAUUSD) - these are validated parameters
- For forex pairs: May reduce velocity to 0.7-0.8 for more zones
- For ranging markets: Increase consolidation to 4-5 candles

---

### 2. Order Block Windows

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Enable OB Time Filter** | ✓ ON | Only show zones formed during OB windows (2.56x concentration) |
| **Hourly Turn Window** | ±5 mins | xx:55-05 UTC window size |
| **Half-Hour Window** | ±3 mins | xx:30±3 UTC window size |
| **Show OB Background** | ✓ ON | Highlight background during OB windows |

**Critical Settings**:
- ✅ **Keep OB Filter ON** for highest quality zones (validated)
- ✅ **Show background** to visualize OB windows in real-time
- ⚠️ **Disable filter** only if you want ALL zones (lower quality)

---

### 3. Trend Filter (H1)

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Enable Trend Filter** | ✓ ON | Only show zones aligned with H1 trend |
| **ADX Period** | 14 | ADX calculation period |
| **ADX Threshold** | 25.0 | ADX > 25 = trending (validated) |
| **Trend Timeframe** | 60 (H1) | Timeframe for trend detection |

**How Trend Filter Works**:
- **Bullish Trend** (H1): Only show DEMAND zones (buy zones)
- **Bearish Trend** (H1): Only show SUPPLY zones (sell zones)
- **Neutral/Weak Trend**: Show both (when ADX < 25)

**Regime-Based Usage** (from research):

**Volatile Markets** (like COVID):
- ✅ Keep filter ON - pattern strongest (2.80x)
- ✅ Use tighter stops (1.0-1.2 ATR)
- ✅ Focus on all OB windows

**Trending Markets** (recent 2024-2025):
- ✅ Keep filter ON - strong concentration (2.50x)
- ✅ Standard stops (1.5 ATR)
- ⚠️ Can trade outside OB with strong trend confirmation

**Ranging Markets** (post-COVID 2022-2023):
- ⚠️ Consider disabling - pattern weakest (1.90x still significant)
- ⚠️ Reduce position sizes 50%
- ⚠️ Focus only on major session opens (08:55-09:05, 13:55-14:05 UTC)

---

### 4. Visual Settings

Customize colors and labels to your preference:
- **Demand Zone Color**: Default green (transparent)
- **Supply Zone Color**: Default red (transparent)
- **Border Colors**: Solid green/red
- **OB Window Background**: Orange (very transparent)
- **Show Labels**: "BUY ZONE" / "SELL ZONE" text
- **Show OB Labels**: "HOURLY OB WINDOW" / "HALF-HR OB WINDOW"

---

### 5. Alerts

Enable alerts to get notified when zones form during OB windows:

```
Alert Condition: "Zone formed during OB window"
Frequency: Once per bar
```

**Alert Setup**:
1. Click "Alert" button (clock icon)
2. Condition: Select indicator → "Any alert() function call"
3. Set frequency: "Once Per Bar Close"
4. Create alert

---

## 📈 How to Use the Indicator

### Recommended Setup

**Chart Timeframe**: M15 (15-minute)
- Balance between detail and clarity
- Validated as primary analysis timeframe

**Indicator Settings**:
1. ✅ Enable OB Time Filter (default ON)
2. ✅ Enable Trend Filter (default ON)
3. ✅ Show OB Background (default ON)
4. ✅ Show Labels (default ON)

**Additional Indicators** (optional):
- Volume profile
- Moving averages (20 EMA, 50 EMA, 200 EMA on H1)
- RSI for divergence

---

### Reading the Indicator

#### Dashboard (Top Right)

```
┌─────────────────────┐
│ MOMENTUM FX | 6Y   │
├─────────────────────┤
│ H1 Trend: BULLISH   │  ← Trend direction from H1
│ ADX: 32.5           │  ← Trend strength (>25 = trending)
│ OB Window: ACTIVE ✓ │  ← Currently in OB window
│ Active Zones: 5     │  ← Number of zones on chart
└─────────────────────┘
```

#### Zone Boxes

**Green Box (Demand Zone)**:
- Support area - potential BUY opportunity
- Formed after bullish breakout from consolidation
- Label: "BUY ZONE" or "BUY ZONE [OB]" if formed during OB window

**Red Box (Supply Zone)**:
- Resistance area - potential SELL opportunity
- Formed after bearish breakout from consolidation
- Label: "SELL ZONE" or "SELL ZONE [OB]" if formed during OB window

**[OB] Tag**: Zone formed during Order Block window (highest quality - 2.56x validated)

#### Background Highlighting

**Orange Background**: Currently in OB time window
- Pay **extra attention** to new zones forming
- These have 2.56x higher probability of being quality zones
- Label appears: "HOURLY OB WINDOW" or "HALF-HR OB WINDOW"

---

### Trading Strategy (Based on Research)

#### Entry Setup

1. **Wait for OB Window** (orange background)
   - Hourly: xx:55-05 UTC
   - Half-hourly: xx:27-33 UTC

2. **Zone Forms** (BUY or SELL)
   - Green box (demand) or Red box (supply)
   - Preferably with [OB] tag

3. **Check Trend Alignment** (Dashboard)
   - H1 Trend: Matches zone direction
   - ADX: > 25 (trending)

4. **Wait for Retest**
   - Price returns to zone
   - Ideally during another OB window
   - Look for rejection (wick/candle pattern)

5. **Enter Trade**
   - **Buy**: At demand zone retest (green box)
   - **Sell**: At supply zone retest (red box)

#### Stop Loss Placement

**Demand Zone (Buy)**:
```
Entry: Top of green box
Stop Loss: Below green box (1.5 ATR)
```

**Supply Zone (Sell)**:
```
Entry: Bottom of red box
Stop Loss: Above red box (1.5 ATR)
```

**Regime Adjustments** (from research):
- **Volatile**: 1.0-1.2 ATR stop (tighter)
- **Trending**: 1.5 ATR stop (standard)
- **Ranging**: 1.5 ATR or wider (or avoid trading)

#### Take Profit Levels

**TP1**: 1.0 ATR (50% position)
- Move stop to breakeven

**TP2**: 2.5 ATR (remaining 50%)
- Trail stop by 1.0 ATR

---

### Multi-Timeframe Workflow

**Recommended 3-Chart Layout**:

1. **H1 Chart** (Top)
   - Trend direction and structure
   - Major support/resistance
   - ADX and trend indicators

2. **M15 Chart** (Middle - Main)
   - This indicator
   - Primary analysis timeframe
   - Entry/exit management

3. **M5 Chart** (Bottom - Optional)
   - Precise entry timing
   - Zone formation details
   - Micro-structure

**Workflow**:
1. **H1**: Identify trend → Bullish or Bearish
2. **M15**: Wait for zone formation during OB window
3. **M5**: Fine-tune entry on retest (optional)

---

## 📊 Instrument Recommendations (From Research)

Based on 6-year validation:

### PRIMARY (Best Performance)

**XAUUSD (Gold)** ⭐⭐⭐⭐⭐
- **95.3%** OB concentration (best of all instruments)
- **Position Size**: 1.5-2.0% risk per trade
- **Status**: PRIMARY instrument - use with full confidence
- **Notes**: Most reliable, highest OB concentration

### SECONDARY (Good Performance)

**EURUSD** ⭐⭐⭐⭐
- **80.0%** OB concentration
- **Position Size**: 1.0-1.5% risk per trade
- **Status**: Reliable secondary instrument

**USDJPY** ⭐⭐⭐⭐
- **71.4%** OB concentration
- **Position Size**: 1.0-1.5% risk per trade
- **Status**: Balanced performance

### USE WITH CAUTION

**BTCUSD (Bitcoin)** ⚠️
- **75.0%** OB concentration
- **Position Size**: 0.25-0.5% max
- **Status**: Crypto - higher volatility, use minimal exposure

### AVOID

**GBPUSD** ❌
- **16.7%** OB concentration (regime-sensitive)
- **Status**: Pattern unreliable on this pair
- **Recommendation**: Avoid or use minimal exposure (0.25% max)

---

## ⚠️ Important Disclaimers

### What This Indicator IS

✅ **Informational Filter**: Helps you focus analysis on high-probability time windows
✅ **Zone Detector**: Identifies supply-demand zones based on validated algorithm
✅ **Trend Confirmer**: Shows H1 trend alignment
✅ **Research-Based**: Built on 6-year empirical validation

### What This Indicator IS NOT

❌ **Complete Trading System**: Not a standalone entry/exit system
❌ **Holy Grail**: Requires confirmation with trend, price action, risk management
❌ **Future Guarantee**: Past 6-year validation ≠ guaranteed future performance
❌ **News-Proof**: Avoid major news events, wait for settlement

### Required Confirmations

**ALWAYS combine with**:
1. ✅ Trend analysis (H1 direction)
2. ✅ Zone strength assessment (retest quality)
3. ✅ Volume confirmation (if available)
4. ✅ Price action (candlestick patterns, wicks)
5. ✅ Risk management (position sizing, stop loss)

### Risk Warning

⚠️ **Trading carries high risk.**
- Past performance does not guarantee future results
- The 6-year validation does not ensure this pattern will persist
- Always use proper risk management
- Never risk more than you can afford to lose

---

## 🔧 Optimization Tips

### For Different Instruments

**Gold (XAUUSD)**:
- ✅ Keep ALL defaults (validated)
- ✅ Focus on OB windows exclusively
- ✅ Higher position sizing (1.5-2%)

**Forex Majors (EURUSD, USDJPY)**:
- Consider: Velocity 0.7-0.8 (more zones)
- Focus: London (08:00-17:00) and NY (13:00-22:00) sessions
- Position sizing: 1.0-1.5%

**Volatile Assets (Crypto)**:
- Increase: Min consolidation to 4-5 candles
- Increase: Zone width to 0.7-1.0 ATR
- Reduce: Position sizing to 0.25-0.5% max

### For Different Market Regimes

**Volatile (High ADX, Big moves)**:
- ✅ Keep OB filter ON
- ✅ Tighter stops: 1.0-1.2 ATR
- ✅ Focus ALL analysis on OB windows
- ✅ Best performance (2.80x concentration)

**Trending (ADX > 25, Clear direction)**:
- ✅ Keep trend filter ON
- ✅ Standard stops: 1.5 ATR
- ⚠️ Can trade outside OB with strong confirmation
- ✅ Strong performance (2.50x concentration)

**Ranging (ADX < 20, Choppy)**:
- ⚠️ Consider disabling OB filter (more zones)
- ⚠️ Reduce position sizing by 50%
- ⚠️ Focus only on major session opens
- ⚠️ Weakest performance (1.90x, still significant)

---

## 🐛 Troubleshooting

### "No zones appearing"

**Check**:
1. ✅ OB Filter: Try disabling temporarily to see if zones appear
2. ✅ Trend Filter: Disable to see if trend is filtering all zones
3. ✅ Timeframe: Make sure you're on M5, M15, or M30 (not H1+)
4. ✅ Velocity: Reduce to 0.7 if markets are calm

### "Too many zones"

**Solutions**:
1. ✅ Enable OB Filter (if disabled)
2. ✅ Enable Trend Filter
3. ✅ Increase min velocity to 1.2-1.5 ATR
4. ✅ Increase min consolidation to 4-5 candles
5. ✅ Reduce max zone age to 30-40 bars

### "Zones disappear too quickly"

**Solution**:
- Increase "Max Zone Age" to 100-150 bars

### "Background always highlighted"

**Check**:
- Your timezone vs UTC
- OB windows: xx:55-05 and xx:27-33 are in **UTC**
- Convert your local time to UTC

### "Trend shows neutral always"

**Check**:
1. ADX Threshold: Lower to 20 if markets less trendy
2. Trend Timeframe: Make sure set to "60" (H1)
3. Chart has enough history: Need 200+ bars for ADX calculation

---

## 📞 Support & Research

**Email**: momentumfxtrading25@gmail.com
**Research Site**: https://mikedconcepcion.github.io/momentumfx-research/
**GitHub**: https://github.com/mikedconcepcion/momentumfx-research

**Research Team**: Momentum FX | Prime Verse
**Research & Technical Officer**: Mike Concepcion

---

## 📚 Additional Resources

### From the Research

1. **Academic Paper** (55KB, peer-review ready)
   - Complete methodology
   - Statistical validation
   - Regime analysis

2. **6-Year Validation Report**
   - Period-by-period breakdown
   - Instrument rankings
   - COVID crash analysis

3. **Trading Hours by Regime**
   - Specific UTC times for each regime
   - Session-based guidance
   - Position sizing recommendations

4. **Full Source Code** (Python)
   - Zone detection algorithm
   - Time filter implementation
   - Trend analyzer

All available at: https://mikedconcepcion.github.io/momentumfx-research/

---

## ✅ Quick Start Checklist

For first-time users:

- [ ] Install indicator on TradingView
- [ ] Set chart to M15 timeframe
- [ ] Keep ALL default settings (validated)
- [ ] Test on XAUUSD (Gold) first
- [ ] Wait for orange background (OB window)
- [ ] Watch for zone formation with [OB] tag
- [ ] Check H1 trend in dashboard
- [ ] Wait for retest during OB window
- [ ] Use proper stop loss (1.5 ATR below/above zone)
- [ ] Set TP1 (1.0 ATR) and TP2 (2.5 ATR)
- [ ] Start with 1% risk per trade maximum
- [ ] Keep a trading journal

---

## 📈 Version History

**v1.0.0** (January 2026)
- Initial release
- Based on 6-year validation (2020-2025)
- Supports all validated parameters
- Multi-timeframe analysis (M5/M15/H1)
- Order Block time window detection
- Trend filtering with ADX
- Real-time dashboard
- Alert system

---

**Built with 🧠 by Momentum FX Research Team | Prime Verse**

**Validated with 2.4M bars | 99.9%+ Confidence | COVID-19 Tested ✓**

---

*This indicator is provided for educational and research purposes. Trading involves substantial risk. Always use proper risk management and never risk more than you can afford to lose.*
