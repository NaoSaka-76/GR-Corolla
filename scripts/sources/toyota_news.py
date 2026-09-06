"""トヨタ自動車・世界各地の販売会社からのGR Corolla関連リリース情報。

**公式ドメインのみに限定**(2026-09-05修正): 従来は`Toyota press release OR
announcement`や`トヨタ 発表 OR 発売 OR 新型`のような無制限キーワード検索を
含んでおり、"press release"や"発表"という語を使う第三者メディア記事(実際の
発表元ではなく発表について報じた記事)も拾ってしまっていた。全クエリを
Toyota公式ドメインへの`site:`フィルタ(OR結合)で絞り込む方式に統一。

対象ドメイン(FR Sports Car Watchで検証済みのものを流用):
  - 米/グローバル: pressroom.toyota.com, global.toyota
  - 欧州: newsroom.toyota.eu
  - 豪州: pressroom.toyota.com.au
  - 日本: toyota.jp
"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency

_OFFICIAL_SITES_EN = [
    "pressroom.toyota.com",
    "global.toyota",
    "newsroom.toyota.eu",
    "pressroom.toyota.com.au",
]


def _site_filter(domains: list[str]) -> str:
    return "(" + " OR ".join(f"site:{d}" for d in domains) + ")"


QUERIES = [
    # グローバル/北米/欧州/豪州の公式ニュースルーム(GR Corolla)
    (f'"GR Corolla" {_site_filter(_OFFICIAL_SITES_EN)}', "en-US", "US", "US:en"),
    # 上位グレードのGRMN Corollaは"GR Corolla"の完全一致に含まれないため別クエリで補足
    (f'"GRMN Corolla" {_site_filter(_OFFICIAL_SITES_EN)}', "en-US", "US", "US:en"),
    # 日本(トヨタ自動車公式サイト)
    ("GRカローラ site:toyota.jp", "ja", "JP", "JP:ja"),
    ("GRMNカローラ site:toyota.jp", "ja", "JP", "JP:ja"),
]


def fetch(limit_per_query: int = 8) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return sort_by_recency(dedupe_by_url(items))
