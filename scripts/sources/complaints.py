"""お客様クレーム・不具合報告に関する情報の収集(公開ニュース報道ベース)。

社内CRM等のクレームデータには接続していない。ニュース記事(リコール報道等)から、
公開されている不満・問題報告の言及を集約する。
(Reddit公開検索APIは2025年時点でボット判定によりブロックされるため不採用)
"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss

NEWS_QUERIES = [
    ("\"GR Corolla\" recall OR complaint OR problem OR issue OR defect", "en-US", "US", "US:en"),
    ("GRカローラ 不具合 OR クレーム OR リコール", "ja", "JP", "JP:ja"),
]


def fetch(limit_per_query: int = 10) -> dict:
    items: list[dict] = []
    for query, hl, gl, ceid in NEWS_QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))

    return {
        "items": dedupe_by_url(items),
        "note": (
            "社内クレーム管理システムとは未連携です。ニュース報道(リコール等)で"
            "公開されている情報のみを集約した簡易モニタリングです。"
        ),
    }
