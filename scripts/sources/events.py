"""世界各地で開催・企画されているGR Corolla関連イベント情報の収集。

オーナーズミーティング/ミートアップと、GR Corolla自体が主役となる試乗会・展示会・
著名モーターショーへの出展・GR Garageイベントに絞って集約する。「event」のような
一般的すぎる語だけでの検索は、レース結果や無関係な発表記事まで拾ってしまうため使わない。
公式のイベントカレンダーではなく、ニュース記事ベースの簡易集約。
"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency

QUERIES = [
    # オーナーズミーティング/ミートアップ
    (
        "(\"GR Corolla\" OR \"GRMN Corolla\") (\"owners meet\" OR \"owners club\" "
        "OR \"car meet\" OR meetup OR \"owners gathering\")",
        "en-US",
        "US",
        "US:en",
    ),
    ("GRカローラ OR GRMNカローラ (オーナーズミーティング OR オーナーミーティング OR オーナー会 OR ミートアップ)", "ja", "JP", "JP:ja"),
    # GR Corollaの試乗会・展示会・お披露目会
    (
        "(\"GR Corolla\" OR \"GRMN Corolla\") (\"test drive event\" OR \"on display\" "
        "OR showcase OR \"ride and drive\")",
        "en-US",
        "US",
        "US:en",
    ),
    ("GRカローラ OR GRMNカローラ (試乗会 OR 展示会 OR お披露目会 OR 体験会)", "ja", "JP", "JP:ja"),
    # 著名モーターショーへの出展
    (
        "(\"GR Corolla\" OR \"GRMN Corolla\") (\"Tokyo Auto Salon\" OR \"SEMA Show\" "
        "OR \"Goodwood Festival of Speed\")",
        "en-US",
        "US",
        "US:en",
    ),
    ("GRカローラ OR GRMNカローラ (オートサロン OR モーターショー OR モータショー)", "ja", "JP", "JP:ja"),
    # GR Garageイベント
    ("(\"GR Corolla\" OR \"GRMN Corolla\") \"GR Garage\" event", "en-US", "US", "US:en"),
    ("GRカローラ OR GRMNカローラ \"GRガレージ\" イベント", "ja", "JP", "JP:ja"),
]


def fetch(limit_per_query: int = 6) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return sort_by_recency(dedupe_by_url(items))
