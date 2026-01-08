# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-08

### Added
- Complete 6-year validation study (2020-2025)
- COVID-19 period analysis (March 2020 crash and recovery)
- Academic research paper (55KB, 1,400 lines)
- Extended validation reports (2-year and 6-year)
- Interactive GitHub Pages with SVG visualizations
- Complete source code with zone detection algorithm
- Data download scripts for Dukascopy
- Dukascopy data acknowledgement and licensing
- MIT License for open research
- Citation in BibTeX format

### Validated
- 5 instruments across 3 asset classes (FX, Gold, Crypto)
- **2,417,398 bars** analyzed (2.4 million M5 bars)
- **130 supply/demand zones** detected (fast detector with stride sampling)
- Pattern **strengthened** during COVID-19 crash (2.80x vs 2.56x average)
- **Gold (XAUUSD)** confirmed as best instrument:
  - 95.3% OB concentration (highest)
  - 65% of all detected zones
  - Most consistent across all regimes

### Statistical Findings
- **Full 6-year** (2020-2025): **2.56x concentration**, Chi² = 158.78 (p < 0.001)
- **COVID period** (2020-2021): **2.80x concentration**, Chi² = 142.07 (p < 0.001)
- **Post-COVID** (2022-2023): **1.90x concentration**, Chi² = 12.18 (p < 0.001)
- **Recent** (2024-2025): **2.50x concentration**, Chi² = 13.52 (p < 0.001)
- **ALL periods statistically significant** (p < 0.001) ✓

## [0.2.0] - 2024-12-15

### Added
- Extended 2-year validation (2023-2025)
- 318 zones analyzed across 699,674 bars
- Seasonality analysis (8 quarters)
- Regime dependency documentation

## [0.1.0] - 2024-10-01

### Added
- Initial 3-month validation (Oct-Dec 2024)
- 25 zones analyzed across 88,243 bars
- Zone detection algorithm with ATR normalization
- Multi-timeframe trend analysis
- Periodic OB time window classification

---

For detailed changes, see Git commit history.
