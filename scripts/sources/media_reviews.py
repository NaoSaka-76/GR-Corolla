"""自動車メディアによるGR Corolla評価記事の収集。"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss

QUERIES = [
    ("\"GR Corolla\" review", "en-US", "US", "US:en"),
    (
        "\"GR Corolla\" (site:caranddriver.com OR site:motortrend.com OR site:topgear.com "
        "OR site:autocar.co.uk OR site:roadandtrack.com OR site:carsguide.com.au)",
        "en-US",
        "US",
        "US:en",
    ),
    ("GRカローラ 試乗 OR インプレッション OR レビュー", "ja", "JP", "JP:ja"),
]


def fetch(limit_per_query: int = 6) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return dedupe_by_url(items)
