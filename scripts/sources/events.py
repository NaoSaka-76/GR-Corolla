"""世界各地で開催・企画されている、GR Corollaに関する「人が集まる」イベント情報の収集。

オーナーズミーティング/ミートアップ、GR Corolla自体の試乗会・体験会、著名モーターショーへの
展示・出展のみに絞って集約する。「event」「unveil」「showcase」のような一般的すぎる語だけの
検索は、発売告知・スペック発表などのプレスリリース記事まで拾ってしまうため使わない。

Google News RSSは見出し文のみで、記事本文・実際の日程/開催地はリンク先を開かないと
分からない(Googleの記事リンクはJavaScriptによるリダイレクトが必要でRSS側からは
本文取得ができない)。そのため、見出しに具体的な日付らしき表記(◯月◯日、開催中 等)が
含まれる記事を優先的に上位表示し、日程の確認を促す形にしている。
公式のイベントカレンダーではなく、ニュース記事ベースの簡易集約。
"""

from __future__ import annotations

import re

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

_JP_DATE_RE = re.compile(r"\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月|開催中|開催決定|募集中|\d{1,2}/\d{1,2}")
_EN_MONTH = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
_EN_DATE_RE = re.compile(_EN_MONTH + r"\s*\d{1,2}|\d{1,2}\s*" + _EN_MONTH, re.IGNORECASE)


def _has_date_hint(title: str) -> bool:
    """見出し文に具体的な日付らしき表記が含まれるかを判定する(簡易ヒューリスティック)。"""
    return bool(_JP_DATE_RE.search(title) or _EN_DATE_RE.search(title))


def fetch(limit_per_query: int = 6) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))

    deduped = sort_by_recency(dedupe_by_url(items))
    # 日付らしき表記が見出しにある記事を優先(グループ内は新着順を維持)
    with_date = [it for it in deduped if _has_date_hint(it["title"])]
    without_date = [it for it in deduped if not _has_date_hint(it["title"])]
    return with_date + without_date
