import os
from datetime import datetime, timedelta, timezone

import requests

NEWS_URL = "https://data.alpaca.markets/v1beta1/news"

def recent_news(symbol, minutes=120, limit=20):
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)

    headers = {
        "APCA-API-KEY-ID": os.environ["APCA_API_KEY_ID"],
        "APCA-API-SECRET-KEY": os.environ["APCA_API_SECRET_KEY"],
    }

    params = {
        "symbols": symbol,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "limit": limit,
        "sort": "desc",
        "include_content": "false",
    }

    response = requests.get(
        NEWS_URL,
        headers=headers,
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("news", [])

def has_major_catalyst(symbol):
    articles = recent_news(symbol)
    risky_words = (
        "earnings", "guidance", "merger", "acquisition",
        "offering", "bankruptcy", "sec", "investigation",
        "fda", "lawsuit", "downgrade", "upgrade"
    )

    for article in articles:
        headline = (article.get("headline") or "").lower()
        if any(word in headline for word in risky_words):
            return True, headline

    return False, None
