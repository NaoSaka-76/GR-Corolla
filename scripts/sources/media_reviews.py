"""自動車メディアによるGR Corolla評価記事の収集。"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency

QUERIES = [
    ("\"GR Corolla\" review", "en-US", "US", "US:en"),
    ("\"GRMN Corolla\" review", "en-US", "US", "US:en"),
    (
        "(\"GR Corolla\" OR \"GRMN Corolla\") (site:caranddriver.com OR site:motortrend.com "
        "OR site:topgear.com OR site:autocar.co.uk OR site:roadandtrack.com "
        "OR site:carsguide.com.au OR site:autoblog.com OR site:thedrive.com "
        "OR site:carbuzz.com)",
        "en-US",
        "US",
        "US:en",
    ),
    ("GRカローラ OR GRMNカローラ 試乗 OR インプレッション OR レビュー", "ja", "JP", "JP:ja"),
]


def fetch(limit_per_query: int = 8) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return sort_by_recency(dedupe_by_url(items))
