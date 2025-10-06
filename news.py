from __future__ import annotations

import re
from typing import List, Dict

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
from dateutil import parser as dateparser


YAHOO_FINANCE_RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
REUTERS_RSS = "https://feeds.reuters.com/reuters/INbusinessNews"  # general business; filtered by ticker keyword


def _parse_date(date_str: str) -> datetime:
    try:
        return dateparser.parse(date_str)
    except Exception:
        return datetime.utcnow()


def fetch_news_items(ticker: str, max_items: int = 50) -> List[Dict]:
    """
    Fetch recent news items for a ticker from Yahoo Finance RSS and Reuters (broad),
    returning a list of dicts with keys: [date, source, title, summary, link].
    """
    feeds = [YAHOO_FINANCE_RSS.format(ticker=ticker), REUTERS_RSS]
    items: List[Dict] = []
    for url in feeds:
        parsed = feedparser.parse(url)
        for entry in parsed.entries[:max_items]:
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            link = getattr(entry, "link", "") or ""
            published = getattr(entry, "published", getattr(entry, "updated", ""))
            dt_obj = _parse_date(published)
            # Filter Reuters feed roughly by ticker appearing in title or summary
            if url == REUTERS_RSS:
                if ticker.lower() not in (title + " " + summary).lower():
                    continue
            items.append({
                "date": dt_obj.date().isoformat(),
                "source": "YahooFinance" if url != REUTERS_RSS else "Reuters",
                "title": title,
                "summary": summary,
                "link": link,
            })
    return items


def score_sentiment(items: List[Dict]) -> List[Dict]:
    analyzer = SentimentIntensityAnalyzer()
    scored = []
    for it in items:
        text = f"{it.get('title','')} {it.get('summary','')}".strip()
        text = re.sub(r"\s+", " ", text)
        vs = analyzer.polarity_scores(text or "")
        scored.append({**it, "sent_neg": vs["neg"], "sent_neu": vs["neu"], "sent_pos": vs["pos"], "sent_compound": vs["compound"]})
    return scored


def aggregate_daily_sentiment(items: List[Dict]) -> List[Dict]:
    """
    Aggregate per-date mean of compound sentiment and counts.
    Output keys: [Date, news_count, sent_compound_mean]
    """
    from collections import defaultdict
    by_date = defaultdict(list)
    for it in items:
        by_date[it["date"]].append(it.get("sent_compound", 0.0))
    out = []
    for date_str, vals in sorted(by_date.items()):
        if len(vals) == 0:
            continue
        out.append({
            "Date": date_str,
            "news_count": len(vals),
            "sent_compound_mean": sum(vals) / max(len(vals), 1),
        })
    return out


