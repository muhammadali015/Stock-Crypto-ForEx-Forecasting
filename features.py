from __future__ import annotations

import pandas as pd


def build_feature_frame(price_df: pd.DataFrame, daily_news_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge price indicators and aggregated news sentiment by Date.

    Keeps a minimal set of columns necessary for next-day prediction tasks.
    """
    # Ensure Date as string for merge
    left = price_df.copy()
    left["Date"] = pd.to_datetime(left["Date"]).dt.date.astype(str)

    right = daily_news_df.copy()
    if not right.empty:
        right["Date"] = pd.to_datetime(right["Date"]).dt.date.astype(str)
    else:
        # Create empty DataFrame with expected columns if no news
        right = pd.DataFrame(columns=["Date", "news_count", "sent_compound_mean"])

    merged = pd.merge(left, right, on="Date", how="left")
    # Fill missing news with zeros (no news day)
    merged["news_count"] = merged["news_count"].fillna(0).astype(int)
    merged["sent_compound_mean"] = merged["sent_compound_mean"].fillna(0.0)

    # Minimal export columns
    columns = [
        "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume",
        "daily_return", "volatility_5d", "ma_5", "ma_10", "volume_zscore_5d",
        "news_count", "sent_compound_mean",
    ]
    existing = [c for c in columns if c in merged.columns]
    return merged[existing].sort_values("Date")


