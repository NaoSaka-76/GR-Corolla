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

**Added 2026-09-06 — Canada distributor + Japan dealer expansion** (additive
only; every domain below was verified live via a direct Google News RSS
`site:` query returning genuine GR Corolla official content, never third-party
media, before being added):

*Canada* (media.toyota.ca / "Toyota Canada") — a real gap in the previous list:
GR Corolla is confirmed sold in Canada (one of this vehicle's three core
markets alongside Japan and the US) but no Canadian domain was queried at all.
A direct probe (`"GR Corolla" site:media.toyota.ca`) returned multiple genuine
Toyota Canada press articles (model-year updates, the H2 Fuji 24 Hour item),
so it's added to the same English-locale OR group as the other English-
language newsrooms.

*Europe / Australia / NZ — deliberately NOT expanded further*: GR Corolla
production is confirmed starting at Toyota Motor Manufacturing UK from 2026
(reported on newsroom.toyota.eu / media.toyota.co.uk / toyota-media.de, all of
which are either already covered via newsroom.toyota.eu or were considered and
rejected below), but as of this writing Toyota has stated the specific retail
markets, volumes, and launch timing are "to be confirmed at a later date" —
i.e. production-country ≠ confirmed retail market yet. Given that genuine
uncertainty, country-specific European distributor domains (UK/DE/IT/ES — all
verified working for the sibling FR-Sports-Car-Watch/GR Supra dashboard) were
NOT added here; newsroom.toyota.eu (already in the list) will pick up the
announcement once EU retail is confirmed. Australia (pressroom.toyota.com.au,
already in the list) is a genuine current market — confirmed for sale via
toyota.com.au/gr-corolla — so no change was needed there. NZ has no separate
GR Corolla-specific finding either way; left as a known gap.

*Japan dealer-corporation domains* (representative sample, GR Garage-network
priority; same set verified for the sibling FR-Sports-Car-Watch/GR Supra
dashboard, each confirmed here too via a Google News RSS `site:` probe
combined with a GR Corolla / GRMN Corolla term):
  トヨタモビリティ東京 (toyota-mobi-tokyo.co.jp), 愛知トヨタ (aichi-toyota.jp),
  Weins Toyota神奈川 (weins-toyota-kanagawa.co.jp), トヨタモビリティ中京
  (tm-chukyo.co.jp), 広島トヨタ (hiroshima-toyota.co.jp), 大阪トヨペット
  (osaka-toyopet.jp), 群馬トヨタ (gtoyota.com — richest content of the set:
  dated per-model blog posts), ネッツトヨタ兵庫 (netzhyogo.jp), ネッツトヨタ
  東埼玉 (mynetz.jp), トヨタカローラ福岡 GR Garage 福岡空港 (dedicated site
  with its own NEWS section: grgarage-fukuoka.net), AGHトヨタ札幌 GR Garage
  札幌西 (dedicated site with its own NEWS section: gr-garage-sad.com).
  This remains a representative sample, not the full ~60+ dealer-corporation
  network — genuinely dealer-specific stories outside this set are a known,
  accepted gap (same as documented in the FR-Sports-Car-Watch dashboard).
"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency

_OFFICIAL_SITES_EN = [
    "pressroom.toyota.com",
    "global.toyota",
    "newsroom.toyota.eu",
    "pressroom.toyota.com.au",
    "media.toyota.ca",
]

# 日本の販売会社(GR Garage網を中心とした代表サンプル、2026-09-06追加)。
# 単一の統一プレスルームが存在しないため、共有の販売会社サイト群を1つのOR
# グループとして持ち、車名クエリと組み合わせて使う。
_JP_DEALER_SITES = [
    "toyota-mobi-tokyo.co.jp",
    "aichi-toyota.jp",
    "weins-toyota-kanagawa.co.jp",
    "tm-chukyo.co.jp",
    "hiroshima-toyota.co.jp",
    "osaka-toyopet.jp",
    "gtoyota.com",
    "netzhyogo.jp",
    "mynetz.jp",
    "grgarage-fukuoka.net",
    "gr-garage-sad.com",
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
    # 日本の販売会社(GR Garage網中心の代表サンプル)
    (f"GRカローラ {_site_filter(_JP_DEALER_SITES)}", "ja", "JP", "JP:ja"),
    (f"GRMNカローラ {_site_filter(_JP_DEALER_SITES)}", "ja", "JP", "JP:ja"),
]


def fetch(limit_per_query: int = 8) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return sort_by_recency(dedupe_by_url(items))
