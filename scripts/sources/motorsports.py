"""GR Corollaが参戦するモータースポーツ情報(TC America / ARA / スーパー耐久)。

各シリーズ公式サイトの結果・ランキング表は構造がそれぞれ異なり安定したスクレイピングが
難しいため、ニュース記事(Google News RSS)ベースでトピックス・レース結果・ランキング関連の
話題を集約する。正式な最新順位表は、あわせて表示する検索リンクから確認する運用とする。
"""

from __future__ import annotations

import urllib.parse

from .common import dedupe_by_url, fetch_google_news_rss
from .standings import fetch_tc_america_driver_standings


def _search_link(query: str) -> str:
    return "https://www.google.com/search?q=" + urllib.parse.quote(query)


SERIES = {
    "tc_america": {
        "label": "TC America(米国 ツーリングカー選手権)",
        "queries": {
            "topics": [("\"GR Corolla\" \"TC America\"", "en-US", "US", "US:en")],
            "results": [
                ("\"GR Corolla\" \"TC America\" race result OR finish OR podium OR win", "en-US", "US", "US:en"),
            ],
            "standings": [
                ("\"TC America\" championship standings Toyota OR \"GR Corolla\"", "en-US", "US", "US:en"),
            ],
        },
        "standings_search": "TC America championship points standings 2026",
    },
    "ara": {
        "label": "ARA(米国ラリー選手権 / American Rally Association)",
        "queries": {
            "topics": [
                ("\"GR Corolla\" \"American Rally Association\" OR \"ARA\" rally", "en-US", "US", "US:en"),
            ],
            "results": [
                ("\"GR Corolla\" ARA rally result OR podium OR win OR finish", "en-US", "US", "US:en"),
            ],
            "standings": [
                ("\"American Rally Association\" championship standings Toyota OR \"GR Corolla\"", "en-US", "US", "US:en"),
            ],
        },
        "standings_search": "American Rally Association ARA championship points standings 2026",
    },
    "super_taikyu": {
        "label": "スーパー耐久 水素エンジンGRカローラ(日本)",
        "queries": {
            "topics": [
                ("水素 GRカローラ スーパー耐久", "ja", "JP", "JP:ja"),
                ("\"GR Corolla\" hydrogen \"Super Taikyu\" OR \"S耐\"", "en-US", "US", "US:en"),
            ],
            "results": [
                ("スーパー耐久 GRカローラ 水素 決勝 OR レース結果 OR 完走", "ja", "JP", "JP:ja"),
            ],
            "standings": [
                ("スーパー耐久 シリーズランキング OR ポイントランキング GRカローラ 水素", "ja", "JP", "JP:ja"),
            ],
        },
        "standings_search": "スーパー耐久シリーズ ST-Q クラス ランキング 水素カローラ 2026",
    },
}


def _fetch_group(query_list: list[tuple], limit: int = 5) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in query_list:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit))
    return dedupe_by_url(items)


def fetch() -> dict:
    result: dict = {}
    for key, series in SERIES.items():
        result[key] = {
            "label": series["label"],
            "topics": _fetch_group(series["queries"]["topics"]),
            "results": _fetch_group(series["queries"]["results"]),
            "standings": _fetch_group(series["queries"]["standings"]),
            "standings_search_url": _search_link(series["standings_search"]),
            "standings_chart": None,
            "standings_chart_note": None,
        }

    tc_chart = fetch_tc_america_driver_standings()
    result["tc_america"]["standings_chart"] = tc_chart["standings"]
    result["tc_america"]["standings_chart_note"] = (
        tc_chart["error"]
        or "TC America「TC」クラス ドライバーズランキング(公式サイト実データ)。"
        "複数メーカー混走クラスのため車両モデル別の絞り込みはできません。"
    )
    result["ara"]["standings_chart_note"] = (
        "ARA公式サイトに順位表はなく、順位データはJavaScript描画の非公式サイトが提供する"
        "非公開フォーマットのため、誤表示リスクを避けグラフ化は行っていません。"
        "「公式ランキングを検索」からご確認ください。"
    )
    result["super_taikyu"]["standings_chart_note"] = (
        "水素エンジンGRカローラが参戦するST-Qクラスは開発車両専用クラスのため、"
        "シリーズポイントランキングの対象外です(公式サイトの年間ランキングボードに"
        "ST-Qは掲載されません)。"
    )
    return result
