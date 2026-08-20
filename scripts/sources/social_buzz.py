"""X(旧Twitter)/Facebookのバズ記事の代替情報を収集する。

X API・Facebook Graph APIの公式キーを利用しないため、SNS投稿そのものは取得できない。
代替として、ニュース/ブログでの言及(Google News RSS)を「話題度」の指標として使う。
(Reddit公開検索APIは2025年時点でボット判定によりブロックされるため不採用)
"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss

NEWS_QUERIES = [
    ("\"GR Corolla\" viral OR trending OR buzz OR social media", "en-US", "US", "US:en"),
    ("GRカローラ 話題 OR バズ OR SNS", "ja", "JP", "JP:ja"),
]


def fetch(limit_per_query: int = 8) -> dict:
    items: list[dict] = []
    for query, hl, gl, ceid in NEWS_QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))

    return {
        "items": dedupe_by_url(items),
        "note": (
            "X/Facebookの公式APIキーが未設定のため、投稿本体は取得できません。"
            "ニュース・ブログでの言及数を話題性の代替指標として表示しています。"
        ),
    }
