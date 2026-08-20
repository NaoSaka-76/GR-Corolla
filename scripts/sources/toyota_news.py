"""トヨタ自動車・世界各地の販売会社からのGR Corolla関連リリース情報。"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss

QUERIES = [
    # グローバル/北米
    ("\"GR Corolla\" Toyota press release OR announcement", "en-US", "US", "US:en"),
    ("\"GR Corolla\" site:pressroom.toyota.com OR site:global.toyota OR site:newsroom.toyota.eu", "en-US", "US", "US:en"),
    # 日本語(GRカローラ)
    ("GRカローラ トヨタ 発表 OR 発売 OR 新型", "ja", "JP", "JP:ja"),
    # 欧州
    ("\"GR Corolla\" Toyota Europe", "en-GB", "GB", "GB:en"),
    # オセアニア
    ("\"GR Corolla\" Toyota Australia", "en-AU", "AU", "AU:en"),
]


def fetch(limit_per_query: int = 6) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return dedupe_by_url(items)
