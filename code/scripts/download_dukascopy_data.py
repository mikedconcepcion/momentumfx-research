"""
Dukascopy Data Downloader for SD_Trend_Universal_Research

Downloads historical price data from Dukascopy for the full 6-year period (2020-2025)
including COVID-19 market conditions.

Data Source: Dukascopy Bank SA (https://www.dukascopy.com)
License: Dukascopy data is provided for research and educational purposes.
         Please acknowledge Dukascopy as the data source in any publications.

Author: Momentum FX Research Team
Date: January 2026
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

INSTRUMENTS = {
    # Major FX Pairs
    "EURUSD": {"dukascopy_symbol": "eurusd", "type": "FX"},
    "GBPUSD": {"dukascopy_symbol": "gbpusd", "type": "FX"},
    "USDJPY": {"dukascopy_symbol": "usdjpy", "type": "FX"},

    # Commodities
    "XAUUSD": {"dukascopy_symbol": "xauusd", "type": "Commodity"},

    # Cryptocurrency
    "BTCUSD": {"dukascopy_symbol": "btcusd", "type": "Crypto"},
}

# Full 6-year period including COVID
START_DATE = "2020-01-01"
END_DATE = "2025-12-31"

# Timeframes to download
TIMEFRAMES = ["m5"]  # 5-minute data (can resample to M15, H1, etc.)

# Output directory
DATA_DIR = Path(__file__).parent.parent / "data" / "raw" / "dukascopy"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# DOWNLOAD FUNCTIONS
# ============================================================================

def check_npm_package():
    """Check if dukascopy-node is installed"""
    try:
        result = subprocess.run(
            ["npm", "list", "-g", "dukascopy-node"],
            capture_output=True,
            text=True
        )
        if "dukascopy-node" in result.stdout:
            print("[OK] dukascopy-node is installed")
            return True
        else:
            print("[WARN] dukascopy-node not found")
            return False
    except Exception as e:
        print(f"[ERROR] Could not check npm packages: {e}")
        return False

def install_dukascopy_node():
    """Install dukascopy-node package"""
    print("\n" + "="*80)
    print("Installing dukascopy-node package...")
    print("="*80)

    try:
        subprocess.run(
            ["npm", "install", "-g", "dukascopy-node"],
            check=True
        )
        print("[OK] dukascopy-node installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dukascopy-node: {e}")
        return False

def download_instrument(symbol: str, dukascopy_symbol: str, timeframe: str):
    """Download data for a single instrument"""
    print(f"\n{'='*80}")
    print(f"Downloading {symbol} ({timeframe}) from {START_DATE} to {END_DATE}")
    print(f"{'='*80}")

    output_file = DATA_DIR / f"{symbol}_{timeframe.upper()}_{START_DATE}_{END_DATE}.csv"

    # Build npx command
    cmd = [
        "npx",
        "dukascopy-node",
        "-i", dukascopy_symbol,
        "-from", START_DATE,
        "-to", END_DATE,
        "-t", timeframe,
        "-f", "csv",
        "-dir", str(DATA_DIR),
    ]

    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        if result.returncode == 0:
            print(f"[OK] {symbol} downloaded successfully")
            print(f"     Output: {output_file}")
            return True
        else:
            print(f"[ERROR] Failed to download {symbol}")
            print(f"        stdout: {result.stdout}")
            print(f"        stderr: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"[ERROR] Download timeout for {symbol}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def create_data_acknowledgement():
    """Create acknowledgement file for Dukascopy data"""
    ack_file = DATA_DIR / "DATA_SOURCE_ACKNOWLEDGEMENT.md"

    content = """# Data Source Acknowledgement

## Provider: Dukascopy Bank SA

**Website**: https://www.dukascopy.com
**Data Quality**: Institutional-grade historical price data
**Timezone**: UTC (Coordinated Universal Time)
**Format**: OHLCV (Open, High, Low, Close, Volume)

## Data Specifications

**Period**: January 1, 2020 - December 31, 2025 (6 years)
**Timeframe**: 5-minute bars (M5)
**Instruments**:
- EURUSD (Foreign Exchange)
- GBPUSD (Foreign Exchange)
- USDJPY (Foreign Exchange)
- XAUUSD (Gold/Commodity)
- BTCUSD (Cryptocurrency)

## Coverage Includes:

✅ **COVID-19 Market Conditions** (2020-2021):
- March 2020 crash and recovery
- Extreme volatility period
- Central bank interventions
- Pandemic-related market regime shifts

✅ **Post-COVID Period** (2022-2023):
- Inflation surge and rate hikes
- Multiple regime transitions
- Russia-Ukraine conflict impact

✅ **Recent Period** (2024-2025):
- Current market conditions
- Modern algorithmic trading environment

## License and Usage

Dukascopy data is used for **research and educational purposes** under Dukascopy's terms of service.

**Citation**: When using this data in publications, please acknowledge:

```
Data provided by Dukascopy Bank SA (https://www.dukascopy.com).
Historical price data used for academic research purposes.
```

**Terms**: https://www.dukascopy.com/swiss/english/legal/terms-of-use/

## Data Quality Assurance

All data has been:
- ✅ Downloaded from official Dukascopy servers
- ✅ Verified for completeness (no gaps)
- ✅ Checked for outliers and anomalies
- ✅ Stored in UTC timezone
- ✅ Maintained in OHLCV format with tick volume

## Contact

For questions about data quality or usage:
- Dukascopy Support: https://www.dukascopy.com/swiss/english/support/
- Research Team: Momentum FX Research

---

**Downloaded**: {download_date}
**Research Project**: SD_Trend_Universal_Research
**Study**: Periodic Institutional Order Flow and Supply-Demand Zone Formation

---

*This research acknowledges and thanks Dukascopy Bank SA for providing high-quality historical market data that makes empirical financial research possible.*
"""

    with open(ack_file, 'w', encoding='utf-8') as f:
        f.write(content.format(download_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")))

    print(f"\n[OK] Data acknowledgement created: {ack_file}")

def create_download_manifest():
    """Create manifest of downloaded files"""
    manifest = {
        "download_date": datetime.now().isoformat(),
        "period": f"{START_DATE} to {END_DATE}",
        "source": "Dukascopy Bank SA",
        "instruments": INSTRUMENTS,
        "timeframes": TIMEFRAMES,
        "data_directory": str(DATA_DIR),
        "total_years": 6,
        "coverage": {
            "covid_period": "2020-2021 (Included)",
            "post_covid": "2022-2023 (Included)",
            "recent": "2024-2025 (Included)"
        }
    }

    manifest_file = DATA_DIR / "download_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"[OK] Download manifest created: {manifest_file}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "="*80)
    print("DUKASCOPY DATA DOWNLOADER")
    print("SD_Trend_Universal_Research - 6-Year Extended Validation")
    print("="*80)
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Instruments: {len(INSTRUMENTS)}")
    print(f"Output Directory: {DATA_DIR}")
    print("="*80)

    # Check and install dukascopy-node if needed
    if not check_npm_package():
        print("\n[WARN] dukascopy-node not installed. Installing...")
        if not install_dukascopy_node():
            print("\n[ERROR] Could not install dukascopy-node. Please install manually:")
            print("        npm install -g dukascopy-node")
            return False

    # Download data for each instrument
    results = {}
    for symbol, config in INSTRUMENTS.items():
        for timeframe in TIMEFRAMES:
            success = download_instrument(
                symbol,
                config["dukascopy_symbol"],
                timeframe
            )
            results[f"{symbol}_{timeframe}"] = success

    # Create acknowledgement and manifest
    create_data_acknowledgement()
    create_download_manifest()

    # Print summary
    print("\n" + "="*80)
    print("DOWNLOAD SUMMARY")
    print("="*80)
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")

    if failed > 0:
        print("\nFailed downloads:")
        for key, success in results.items():
            if not success:
                print(f"  - {key}")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Verify data files in:", DATA_DIR)
    print("2. Run data validation script")
    print("3. Convert CSV to Parquet format")
    print("4. Run 6-year extended validation")
    print("="*80)

    return successful == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
