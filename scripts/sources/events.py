"""世界各地で開催・企画されているGR Corolla関連イベント情報の収集。

モーターショー・展示会、試乗会、GR Garageのイベント、オーナーミートアップなど、
モータースポーツ(motorsports.py)以外のイベント告知・レポート記事をGoogle News RSSで
横断的に集約する。公式のイベントカレンダーではなく、ニュース記事ベースの簡易集約。
"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency

QUERIES = [
    # 北米
    (
        "(\"GR Corolla\" OR \"GRMN Corolla\") event OR exhibition OR \"auto show\" "
        "OR \"test drive event\" OR \"car meet\" OR meetup OR unveiling",
        "en-US",
        "US",
        "US:en",
    ),
    ("(\"GR Corolla\" OR \"GRMN Corolla\") \"GR Garage\" OR \"GAZOO Racing\" event", "en-US", "US", "US:en"),
    (
        "(\"GR Corolla\" OR \"GRMN Corolla\") \"Tokyo Auto Salon\" OR \"SEMA Show\" "
        "OR \"Goodwood Festival of Speed\"",
        "en-US",
        "US",
        "US:en",
    ),
    # 欧州
    ("(\"GR Corolla\" OR \"GRMN Corolla\") event OR exhibition OR \"auto show\"", "en-GB", "GB", "GB:en"),
    # オセアニア
    ("(\"GR Corolla\" OR \"GRMN Corolla\") event OR exhibition OR \"auto show\"", "en-AU", "AU", "AU:en"),
    # 日本語
    ("GRカローラ OR GRMNカローラ イベント OR 試乗会 OR 展示会 OR お披露目", "ja", "JP", "JP:ja"),
    ("GRカローラ OR GRMNカローラ \"GRガレージ\" OR モーターショー OR モータショー OR オートサロン", "ja", "JP", "JP:ja"),
]


def fetch(limit_per_query: int = 6) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return sort_by_recency(dedupe_by_url(items))
