"""世界各地で開催・企画されている、GR Corollaに関する「人が集まる」イベント情報の収集。

オーナーズミーティング/ミートアップ、GR Corolla自体の試乗会・体験会、著名モーターショーへの
展示・出展のみに絞って集約する。「event」「unveil」「showcase」のような一般的すぎる語だけの
検索は、発売告知・スペック発表などのプレスリリース記事まで拾ってしまうため使わない。

Google News RSSは見出し文のみで、記事本文・実際の日程/開催地はリンク先を開かないと
分からない(Googleの記事リンクはJavaScriptによるリダイレクトが必要でRSS側からは
本文取得ができない)。参加を検討する場合は必ず元記事で日程・開催地を確認すること。
公式のイベントカレンダーではなく、ニュース記事ベースの簡易集約。新着順で表示する。
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
    # GR Corollaの試乗会・体験会・お披露目会(来場者が参加する実施イベント)
    (
        "(\"GR Corolla\" OR \"GRMN Corolla\") (\"test drive event\" OR \"ride and drive\" "
        "OR \"meet and greet\")",
        "en-US",
        "US",
        "US:en",
    ),
    ("GRカローラ OR GRMNカローラ (試乗会 OR 体験会 OR お披露目会 OR 試乗イベント)", "ja", "JP", "JP:ja"),
    # 著名モーターショーでの展示・出展(発表記事ではなく会場での展示に限定)
    (
        "(\"GR Corolla\" OR \"GRMN Corolla\") (\"Tokyo Auto Salon\" OR \"SEMA Show\" "
        "OR \"Goodwood Festival of Speed\") (display OR exhibit OR exhibiting)",
        "en-US",
        "US",
        "US:en",
    ),
    ("GRカローラ OR GRMNカローラ (オートサロン OR モーターショー OR モータショー) (出展 OR 展示)", "ja", "JP", "JP:ja"),
]

def fetch(limit_per_query: int = 6) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return sort_by_recency(dedupe_by_url(items))
