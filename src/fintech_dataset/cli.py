from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from .prices import fetch_price_history, compute_minimal_indicators
from .news import fetch_news_items, score_sentiment, aggregate_daily_sentiment
from .features import build_feature_frame
from .align import align_and_save


def run(exchange: str, ticker: str, days: int, out_dir: str) -> int:
    try:
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        price_df = fetch_price_history(ticker, period_days=days)
        price_df = compute_minimal_indicators(price_df)

        news_items = fetch_news_items(ticker)
        news_scored = score_sentiment(news_items)
        news_daily = pd.DataFrame(aggregate_daily_sentiment(news_scored))

        features_df = build_feature_frame(price_df, news_daily if not news_daily.empty else pd.DataFrame())

        csv_path = str(Path(out_dir) / f"{exchange}_{ticker}_dataset.csv")
        json_path = str(Path(out_dir) / f"{exchange}_{ticker}_dataset.json")
        align_and_save(features_df, out_csv_path=csv_path, out_json_path=json_path)

        print(f"Saved dataset: {csv_path}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Curate minimal FinTech dataset with prices and news")
    parser.add_argument("exchange", type=str, help="Exchange name, e.g., NYSE, NASDAQ, PSX, CRYPTO")
    parser.add_argument("ticker", type=str, help="Stock or crypto ticker, e.g., AAPL, MSFT, BTC-USD")
    parser.add_argument("--days", type=int, default=30, help="How many recent days to fetch (default 30)")
    parser.add_argument("--out", type=str, default="outputs", help="Output directory (default outputs)")
    args = parser.parse_args()

    code = run(args.exchange, args.ticker, args.days, args.out)
    sys.exit(code)


if __name__ == "__main__":
    main()


