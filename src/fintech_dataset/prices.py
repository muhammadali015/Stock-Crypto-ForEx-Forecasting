from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd
import numpy as np
import yfinance as yf


def fetch_price_history(ticker: str, period_days: int = 30, interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a `ticker` using yfinance.

    Returns columns: [Date, Open, High, Low, Close, Adj Close, Volume]
    """
    if period_days < 5:
        period_days = 5
    period = f"{period_days}d"
    data = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
    if data is None or data.empty:
        raise RuntimeError(f"No price data returned for {ticker}.")

    data = data.reset_index()
    # Normalize date column name from yfinance (Date or Datetime)
    if "Date" not in data.columns and "Datetime" in data.columns:
        data = data.rename(columns={"Datetime": "Date"})

    # Flatten MultiIndex columns if they exist
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Ensure timezone-naive dates (for alignment)
    data["Date"] = pd.to_datetime(data["Date"]).dt.tz_localize(None).dt.date

    # Enforce expected columns
    expected = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for col in expected:
        if col not in data.columns:
            data[col] = np.nan

    return data[["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]]


def compute_minimal_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a minimal set of indicators that commonly help next-day prediction:
    - daily_return: (Close/Close.shift(1) - 1)
    - volatility_5d: rolling std of daily_return over 5 days
    - ma_5, ma_10: simple moving averages of Close
    - volume_zscore_5d: z-score of volume over 5 days
    """
    out = df.copy()
    out = out.sort_values("Date")

    out["daily_return"] = out["Close"].pct_change()
    out["volatility_5d"] = out["daily_return"].rolling(window=5, min_periods=3).std()
    out["ma_5"] = out["Close"].rolling(window=5, min_periods=3).mean()
    out["ma_10"] = out["Close"].rolling(window=10, min_periods=5).mean()

    vol_roll = out["Volume"].rolling(window=5, min_periods=3)
    out["volume_zscore_5d"] = (out["Volume"] - vol_roll.mean()) / (vol_roll.std(ddof=0) + 1e-9)

    return out


