"""GR Corollaが参戦するモータースポーツ情報(TC America / ARA / スーパー耐久)。

各シリーズ公式サイトの結果・ランキング表は構造がそれぞれ異なり安定したスクレイピングが
難しいため、ニュース記事(Google News RSS)ベースでトピックス・レース結果・ランキング関連の
話題を集約する。正式な最新順位表は、あわせて表示する検索リンクから確認する運用とする。
"""

from __future__ import annotations

import urllib.parse

from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency
from .schedule import fetch_all as fetch_all_schedules
from .standings import fetch_ara_podium, fetch_tc_america_driver_standings


def _search_link(query: str) -> str:
    return "https://www.google.com/search?q=" + urllib.parse.quote(query)


SERIES = {
    "tc_america": {
        "label": "TC America(米国 ツーリングカー選手権)",
        "queries": {
            "topics": [
                ("\"GR Corolla\" \"TC America\"", "en-US", "US", "US:en"),
                ("\"GRMN Corolla\" \"TC America\"", "en-US", "US", "US:en"),
            ],
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
                ("\"GRMN Corolla\" \"American Rally Association\" OR \"ARA\" rally", "en-US", "US", "US:en"),
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
                ("水素 GRカローラ OR GRMNカローラ スーパー耐久", "ja", "JP", "JP:ja"),
                ("\"GR Corolla\" OR \"GRMN Corolla\" hydrogen \"Super Taikyu\" OR \"S耐\"", "en-US", "US", "US:en"),
            ],
            "results": [
                ("スーパー耐久 GRカローラ OR GRMNカローラ 水素 決勝 OR レース結果 OR 完走", "ja", "JP", "JP:ja"),
            ],
            "standings": [
                ("スーパー耐久 シリーズランキング OR ポイントランキング GRカローラ OR GRMNカローラ 水素", "ja", "JP", "JP:ja"),
            ],
        },
        "standings_search": "スーパー耐久シリーズ ST-Q クラス ランキング 水素カローラ 2026",
    },
}


# TC America・ARAの車両規定/参戦車両概要は頻繁に変わらないため、ニュース収集とは別に
# 手動調査した内容を静的に保持する(スーパー耐久ST-Qは開発車両専用クラスのため対象外)。
_GR_COROLLA_PHOTO = {
    "src": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Toyota_GR_Corolla_2026.jpg",
    "credit": "Gogerr",
    "license": "CC BY-SA 4.0",
    "source_url": "https://commons.wikimedia.org/wiki/File:Toyota_GR_Corolla_2026.jpg",
}

VEHICLE_INFO = {
    "tc_america": {
        "regulation": {
            "class_name": "TC(ツーリングカー)クラス",
            "description": (
                "2025年からTCXクラスとTCクラスが統合されて誕生した単一クラスで、旧TCAクラスは"
                "廃止された。BMW M2 CS、Mazda3 TC、Hyundai Elantra N1 TC、Honda Civic Type R、"
                "MINI Cooper JCW等、市販コンパクト/ハッチバックをベースとする複数ブランドの"
                "車両が参戦しており、GR Corolla TCはこのクラス初の四輪駆動車として2025年シーズンに"
                "デビューした。具体的な性能調整(Balance of Performance等)の詳細はTC America公式の"
                "技術規則書に基づくが、一般には公開されていない。"
            ),
        },
        "vehicle": {
            "manufacturer": "TOYOTA",
            "model": "GR Corolla TC",
            "description": (
                "市販グレードのGR CorollaをベースにTOYOTA GAZOO Racing North America(TGRNA)が"
                "TC America用に開発したレース車両。市販車と同じ1.6L直列3気筒ターボエンジン"
                "(300PS/295lb-ft)とGR-FOUR全輪駆動システム、8速オートメイテッドトランスミッションを"
                "維持しつつ、ブレーキ・サスペンション・空力・電子制御・安全装備をレース用に強化している。"
                "2025年シーズンより、JMF MotorsportsがGR Corolla TCを運用してレースに参戦している"
                "(Virginia International Racewayでの優勝実績あり)。"
            ),
            "team": "開発: TOYOTA GAZOO Racing North America(TGRNA) / 運用: JMF Motorsports",
            "debut": "2025年シーズン",
            "specs": [
                {"key": "engine", "value": "1.6L 直列3気筒ターボ(市販車と同型)"},
                {"key": "power", "value": "300PS(295lb-ft)"},
                {"key": "drivetrain", "value": "GR-FOUR 電子制御全輪駆動"},
                {"key": "transmission", "value": "8速GAZOO Racing Direct Automatic Transmission(DAT)"},
                {"key": "brakes", "value": "Alcon製(前6ポット/後2ポット)"},
                {"key": "suspension", "value": "TGRNA設計カスタムMacPhersonストラット + JRi製減衰力調整式ダンパー"},
                {
                    "key": "safety",
                    "value": "FIA公認ロールケージ、OMP製ファイバーグラスシート(6点式ハーネス)、OMP製電動消火装置",
                },
            ],
            "photo": _GR_COROLLA_PHOTO,
            "source_url": "https://www.tcamerica.us/news/715/toyota-gazoo-racing-north-america-unveils-new-gr-corolla-touring-car",
        },
    },
    "ara": {
        "regulation": {
            "class_name": "RC2クラス",
            "description": (
                "ARAが採用するRC1〜RC5のクラス体系のうち、RC2は国際ラリー界の「Rally2」(旧R5)規定に"
                "ほぼ相当する水準の車両を対象とするクラス。一般的なRally2規定では1.6Lターボエンジン"
                "(リストリクター径32mm、出力目安280〜290馬力)・4WD・5〜6速シーケンシャルトランスミッション・"
                "最低重量1,230kg等が定められ、量産2,500台以上の市販車をベースとすることが条件となる。"
                "GR Corolla Rally RC2はFIA Rally2の公式ホモロゲーションは取得していないが、これと"
                "ほぼ同等の性能を目標に開発された車両である。"
            ),
        },
        "vehicle": {
            "manufacturer": "TOYOTA",
            "model": "GR Corolla Rally RC2",
            "description": (
                "市販グレードのGR CorollaをベースにTOYOTA GAZOO Racing World Rally Team(TGR-WRT)と"
                "米国Rallysport Servicesが共同開発したラリー車両。WRC2で2年連続タイトルを獲得した"
                "GR Yaris Rally2の開発ノウハウを流用し、同じ1.6L直列3気筒ターボエンジンとSadev製5速"
                "シーケンシャルギアボックス、リアデファレンシャル、Alconブレーキ、Reiger製ダンパーを"
                "採用しつつ、GR Corollaの長いホイールベースに合わせて各部を再設計している。"
                "2026年3月開幕戦の100 Acre WoodラリーからARAのRC2クラスに参戦し、シーズン7戦"
                "(予定)を戦う。"
            ),
            "team": (
                "開発: TOYOTA GAZOO Racing World Rally Team(TGR-WRT)+ Rallysport Services / "
                "ドライバー: セス・クインテロ、コ・ドライバー: Topi Luhtinen(車番103)"
            ),
            "debut": "2026年3月 100 Acre Woodラリー(開幕戦)",
            "specs": [
                {"key": "engine", "value": "1.6L 直列3気筒ターボ(GR Yaris Rally2と同型)"},
                {"key": "drivetrain", "value": "4WD"},
                {"key": "transmission", "value": "Sadev製5速シーケンシャル"},
                {"key": "brakes", "value": "Alcon製(GR Yaris Rally2と共通)"},
                {"key": "suspension", "value": "Reiger製ダンパー"},
            ],
            "photo": _GR_COROLLA_PHOTO,
            "source_url": "https://tgr-wrt.com/gr-corolla-rally-car-to-compete-on-american-soil-in-2026/",
        },
    },
}


def _fetch_group(query_list: list[tuple], limit: int = 5) -> list[dict]:
    items: list[dict] = []
    for query, hl, gl, ceid in query_list:
        items.extend(fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit))
    return sort_by_recency(dedupe_by_url(items))


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
            "podium": None,
            "schedule": [],
            "schedule_link": None,
            "vehicle_info": VEHICLE_INFO.get(key),
        }

    # TC America「TC」クラスは20台に満たないため、上限なく全ドライバーを取得し
    # GR Corolla勢(ドライバー/チーム)が順位に関わらず必ず表示されるようにする。
    tc_chart = fetch_tc_america_driver_standings(limit=30)
    result["tc_america"]["standings_chart"] = tc_chart["standings"]
    result["tc_america"]["standings_chart_note"] = (
        tc_chart["error"]
        or "TC America「TC」クラス ドライバーズランキング(公式サイト実データ)。"
        "各レースの完全結果ページから補完したチーム/使用車種を表示しており、"
        "Toyota GR Corollaで参戦するドライバー/チームには目印を付けています。"
    )
    ara_podium = fetch_ara_podium()
    result["ara"]["podium"] = ara_podium
    result["ara"]["standings_chart_note"] = (
        ara_podium["error"]
        or "ARA公式サイトにはポイント付きのフル順位表はなく、実データは非公式サイトの"
        "JavaScript描画に依存しているため、フル順位表のグラフ化は行っていません。"
        "公式サイトに掲載されているNational Driver/Co-Driver上位3名(表彰台)のみ"
        "表示しています。フル順位表は「公式ランキングを検索」からご確認ください。"
    )
    result["super_taikyu"]["standings_chart_note"] = (
        "水素エンジンGRカローラが参戦するST-Qクラスは開発車両専用クラスのため、"
        "シリーズポイントランキングの対象外です(公式サイトの年間ランキングボードに"
        "ST-Qは掲載されません)。"
    )

    schedules = fetch_all_schedules()
    result["tc_america"]["schedule"] = schedules["tc_america"]
    result["super_taikyu"]["schedule"] = schedules["super_taikyu"]
    result["ara"]["schedule"] = schedules["ara"]

    return result
