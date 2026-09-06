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

**Added 2026-09-06 (second pass) — TMNA/TME corporate-domain check + South America /
China / Thailand / South Africa research** (same standard as above and as the
sibling FR-Sports-Car-Watch dashboard: every domain below was verified reachable
and confirmed via a live Google News RSS `site:` probe returning genuine, on-topic,
dated GR Corolla content before being added):

*TMNA / TME corporate domains — checked, confirmed already covered, nothing added*:
Toyota Motor North America (TMNA) publishes its own corporate press releases
(executive changes, annual sales results, manufacturing announcements) directly on
pressroom.toyota.com under its "Corporate" topic — no distinct `tmna.com`-style
domain exists; pressroom.toyota.com already IS TMNA's official newsroom. Toyota
Motor Europe (TME) is the same: its corporate news publishes directly on
newsroom.toyota.eu's "Corporate" category (newsroom.toyota.eu/corporate-news/) — no
separate TME-only domain found. Both are already fully covered here — nothing added.

*Brazil (toyotacomunica.com.br, "Toyota Comunica") — ADDED*: GR Corolla is
confirmed officially sold in Brazil (a limited run brought in by TOYOTA GAZOO Racing
do Brasil, with subsequent batches/editions and its own dedicated warranty program).
A direct Google News RSS `site:` probe (pt-BR/BR/BR:pt-419 locale) against
toyotacomunica.com.br returned many genuine, dated, on-topic articles credited to
"Toyota Comunica" — e.g. "TOYOTA GAZOO Racing anuncia chegada do GR Corolla ao
Brasil", "GR Corolla inova com inédita garantia de até 10 anos no segmento de
esportivos", "Últimas 30 unidades do GR Corolla Launch Edition chegam ao Brasil".
An earlier-surfaced candidate domain, toyotaimprensa.com.br, does not resolve
(DNS failure) and was not used. GRMN Corolla and GR Supra are not confirmed sold in
Brazil, so this domain was added to the GR Corolla queries only.

*South Africa (toyota.co.za) — ADDED*: GR Corolla is confirmed officially sold in
South Africa (Toyota South Africa Motors / TSAM) — this is the same domain
researched and rejected for the sibling FR-Sports-Car-Watch dashboard's original
pass and now added there too, for the same reason: the earlier rejection used a
generic locale and found only commercial pages, while re-probing with the
country-correct locale (hl=en-ZA, gl=ZA, ceid=ZA:en) surfaced genuine, dated,
on-topic content credited to "Toyota South Africa" — e.g. "TOYOTA GR COROLLA GETS
8-SPEED AUTOMATIC", "Driven: The new GR Corolla", "GR Corolla Takes Centre Stage at
2026 SA Festival of Motoring". No dedicated media/press subdomain (e.g.
`media.toyota.co.za`) was found to exist — toyota.co.za is TSAM's only site.
GRMN Corolla was checked too (`"GRMN Corolla" site:toyota.co.za`) and correctly
returns zero, confirming no false-positive risk from reusing this domain for both
name variants.

*Argentina — researched and rejected*: no evidence GR Corolla is officially sold in
Argentina was found (only GR Supra has a confirmed limited-run Argentina launch, and
that itself returned no indexed press content when checked for the sibling Supra
dashboard). Not added.

*China (toyota.com.cn) — researched and rejected*: no official China-market launch
of GR Corolla was found in either English or Chinese-language search (only
Malaysia/Taiwan neighboring-market coverage turned up, which are separate,
non-mainland-China distributors). A direct `site:toyota.com.cn` probe for
`"GR Corolla"` (zh-CN/CN/CN:zh-Hans locale) returned no on-topic result either.
Not added — the vehicle does not appear to be officially sold there at all.

*Thailand (toyota.co.th) — researched and rejected*: Toyota Motor Thailand does
officially sell GR Corolla (confirmed: toyota.co.th/model/grcorolla, currently
priced, a rare non-JP/US/EU market where it's still listed) and publishes
ข่าวประชาสัมพันธ์ ("press release") content on its own main site (toyota.co.th/news
— no separate press subdomain exists). But `site:toyota.co.th` probes for
`"GR Corolla"` in both Thai and English locale variants returned only generic
catalogue/model/promotion pages (Corolla Cross, Camry, Hilux, etc.) — no on-topic
GR Corolla press content indexed. Not added.
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


# 欧州以外の地域の公式販売代理店ニュースルーム(2026-09-06追加、第2弾)。
# ブラジル(Toyota Comunica)・南アフリカ(TSAM)はいずれも専用メディアサブドメインが
# 見つからず(ブラジルはtoyotacomunica.com.br自体が報道向けサイト、南アフリカは
# toyota.co.za本体がそれを兼ねる)。国ごとのロケールを合わせないと0件になる点はEU各国
# 及びFR-Sports-Car-Watchダッシュボードでの検証と同じ。
_DISTRIBUTOR_SITES: dict[str, tuple[str, str, str, str]] = {
    # country_code: (domain, hl, gl, ceid)
    "BR": ("toyotacomunica.com.br", "pt-BR", "BR", "BR:pt-419"),
    "ZA": ("toyota.co.za", "en-ZA", "ZA", "ZA:en"),
}


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
    # ブラジル(Toyota Comunica)・南アフリカ(TSAM) — GR Corolla/GRMN Corolla両方確認
    *[
        (f'"GR Corolla" site:{domain}', hl, gl, ceid)
        for domain, hl, gl, ceid in _DISTRIBUTOR_SITES.values()
    ],
    *[
        (f'"GRMN Corolla" site:{domain}', hl, gl, ceid)
        for domain, hl, gl, ceid in _DISTRIBUTOR_SITES.values()
    ],
]


# 発信元ドメイン -> 地域タブのキー(フロントエンドのi18n.regionsと対応)。
# 日本の販売会社ドメインは全てtoyota.jpと同じ"japan"バケットにまとめる。
# global.toyota(トヨタ自動車グローバル本体)は特定の国に紐づかないため、どのタブにも
# 割り当てず「グローバル(すべて)」タブでのみ表示する(region未設定のまま)。
_DOMAIN_TO_REGION: dict[str, str] = {
    "pressroom.toyota.com": "us",
    "media.toyota.ca": "canada",
    "newsroom.toyota.eu": "europe",
    "pressroom.toyota.com.au": "australia",
    "toyota.jp": "japan",
    "toyotacomunica.com.br": "brazil",
    "toyota.co.za": "south_africa",
    **{domain: "japan" for domain in _JP_DEALER_SITES},
}


def _tag_region(items: list[dict]) -> list[dict]:
    for item in items:
        domain = item.get("source_domain", "")
        # Google NewsのRSSは同じサイトでも"www."有り無しの両方を返すことがあるため、
        # 先頭のwww.を落としてから完全一致で照合する。
        domain = domain[4:] if domain.startswith("www.") else domain
        item["region"] = _DOMAIN_TO_REGION.get(domain)
    return items


def fetch(limit_per_query: int = 8) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query))
    return _tag_region(sort_by_recency(dedupe_by_url(items)))
