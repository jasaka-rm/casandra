"""
Fetches Google News RSS headlines for the REIT name (within a lookback window), runs VADER sentiment, and converts to a governance/controversy risk score (0–100).

MVP: Pull Google News RSS for the REIT name and compute VADER sentiment.
Score => invert to "governance/controversy risk" (more negative = higher risk).
"""

import time, feedparser
from datetime import datetime, timedelta, timezone
from typing import List
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from urllib.parse import quote_plus


try:
    _ = nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')


def fetch_news_titles(name: str, lookback_days: int):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=lookback_days)

    # Build and ENCODE the query
    q_raw = f"{name} REIT governance OR controversy OR lawsuit"
    q = quote_plus(q_raw)  # encodes spaces and control chars

    url = f"https://news.google.com/rss/search?q={q}&hl=en-GB&gl=GB&ceid=GB:en"

    # Optional: be polite with a UA; feedparser supports request headers
    d = feedparser.parse(url, request_headers={"User-Agent": "REITVision ESG (contact: your.email@domain.com)"})

    titles = []
    for e in d.entries[:50]:  # small cap to avoid runaway loops
        try:
            published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            published = now
        if published >= since:
            titles.append(e.title)
    return titles


def governance_risk_score_0_100(name: str, lookback_days: int) -> float:
    titles = fetch_news_titles(name, lookback_days)
    if not titles:
        return 50.0
    sia = SentimentIntensityAnalyzer()
    scores = [sia.polarity_scores(t)["compound"] for t in titles]
    avg = sum(scores) / len(scores)
    # Map compound (-1..1) to 0..100 where -1 -> 95 (high risk), +1 -> 5 (low risk)
    risk = 50 - avg * 45
    return max(0, min(100, risk))
