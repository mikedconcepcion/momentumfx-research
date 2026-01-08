"""
Data Loader for Supply & Demand Research

Loads OHLCV data from MFX_Research_to_Prod parquet files
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional


class DataLoader:
    """Load and manage OHLCV data for backtesting and research"""

    def __init__(self, data_path: str = None):
        """
        Args:
            data_path: Path to parquet data directory
                      Defaults to combined_2020_2025 folder
        """
        if data_path is None:
            # Default to combined 2020-2025 data
            current_dir = Path(__file__).parent.parent
            data_path = current_dir / "data" / "raw" / "combined_2020_2025"

        self.data_path = Path(data_path)

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Data path not found: {self.data_path}\n"
                "Please ensure data is available. Run scripts/combine_data_2020_2025.py first."
            )

    def load(
        self,
        symbol: str,
        timeframe: str = "M15",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load OHLCV data for a symbol

        Args:
            symbol: Symbol name (e.g., "EURUSD", "XAUUSD")
            timeframe: Timeframe (M1, M5, M15, H1, H4, D1)
            start_date: Start date (YYYY-MM-DD format), optional
            end_date: End date (YYYY-MM-DD format), optional

        Returns:
            DataFrame with timestamp index and OHLCV columns
        """
        # Try different file naming conventions
        # 1. Combined 2020-2025 format: EURUSD_M5_2020_2025.parquet (in root)
        file_path = self.data_path / f"{symbol}_{timeframe}_2020_2025.parquet"

        # 2. If not found, try subfolder format: M5/EURUSD.parquet
        if not file_path.exists():
            file_path = self.data_path / timeframe / f"{symbol}.parquet"

        # 3. If not found, try with timeframe suffix: M5/EURUSD_M5.parquet
        if not file_path.exists():
            file_path = self.data_path / timeframe / f"{symbol}_{timeframe}.parquet"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Data file not found for {symbol} {timeframe}\n"
                f"Available instruments: {self.list_available_symbols(timeframe)}"
            )

        df = pd.read_parquet(file_path)

        # Set timestamp as index if not already
        if 'timestamp' in df.columns:
            df = df.set_index('timestamp')

        # Filter by symbol if column exists
        if 'pair' in df.columns:
            df = df[df['pair'] == symbol]

        # Filter by date range
        if start_date:
            df = df[df.index >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df.index <= pd.Timestamp(end_date)]

        # Ensure index is sorted
        df = df.sort_index()

        # Rename columns to standard format
        column_mapping = {
            'tick_volume': 'volume'
        }
        df = df.rename(columns=column_mapping)

        # Ensure we have required columns
        required = ['open', 'high', 'low', 'close']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return df

    def load_multiple_timeframes(
        self,
        symbol: str,
        timeframes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Load data for multiple timeframes

        Args:
            symbol: Symbol name
            timeframes: List of timeframes (e.g., ['M15', 'H1', 'H4'])
            start_date: Start date, optional
            end_date: End date, optional

        Returns:
            Dict mapping timeframe to DataFrame
        """
        data = {}
        for tf in timeframes:
            try:
                data[tf] = self.load(symbol, tf, start_date, end_date)
            except FileNotFoundError as e:
                print(f"Warning: Could not load {symbol} {tf}: {e}")

        return data

    def load_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str = "M15",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Load data for multiple symbols

        Args:
            symbols: List of symbols
            timeframe: Timeframe
            start_date: Start date, optional
            end_date: End date, optional

        Returns:
            Dict mapping symbol to DataFrame
        """
        data = {}
        for symbol in symbols:
            try:
                data[symbol] = self.load(symbol, timeframe, start_date, end_date)
            except FileNotFoundError as e:
                print(f"Warning: Could not load {symbol}: {e}")

        return data

    def list_available_timeframes(self) -> List[str]:
        """List all available timeframes"""
        timeframes = []
        for path in self.data_path.iterdir():
            if path.is_dir():
                timeframes.append(path.name)
        return sorted(timeframes)

    def list_available_symbols(self, timeframe: str = "M15") -> List[str]:
        """List all available symbols for a timeframe"""
        tf_path = self.data_path / timeframe
        if not tf_path.exists():
            return []

        symbols = []
        for file_path in tf_path.glob("*.parquet"):
            # Remove timeframe suffix if present (e.g., XAUUSD_M5 -> XAUUSD)
            stem = file_path.stem
            if stem.endswith(f"_{timeframe}"):
                stem = stem[:-len(f"_{timeframe}")]
            symbols.append(stem)
        return sorted(set(symbols))  # Remove duplicates

    def get_date_range(
        self,
        symbol: str,
        timeframe: str = "M15"
    ) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Get the available date range for a symbol"""
        df = self.load(symbol, timeframe)
        return df.index.min(), df.index.max()


def main():
    """Example usage"""
    loader = DataLoader()

    print("Available timeframes:", loader.list_available_timeframes())
    print("Available symbols (M15):", loader.list_available_symbols("M15"))

    # Load single symbol
    try:
        df = loader.load("EURUSD", "M15", start_date="2024-01-01", end_date="2024-12-31")
        print(f"\nLoaded EURUSD M15: {len(df)} bars")
        print(f"Date range: {df.index[0]} to {df.index[-1]}")
        print(f"Columns: {df.columns.tolist()}")
        print("\nFirst 5 rows:")
        print(df.head())

        # Get date range
        start, end = loader.get_date_range("EURUSD", "M15")
        print(f"\nFull data range: {start} to {end}")

    except FileNotFoundError as e:
        print(f"Error: {e}")

    # Load multiple timeframes
    mtf_data = loader.load_multiple_timeframes(
        "EURUSD",
        ["M15", "H1", "H4"],
        start_date="2024-01-01"
    )
    print(f"\nLoaded {len(mtf_data)} timeframes")
    for tf, df in mtf_data.items():
        print(f"  {tf}: {len(df)} bars")


if __name__ == "__main__":
    main()
