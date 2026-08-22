"""GR Corollaダッシュボード用データを収集し、site/data/latest.jsonへ出力する。

30分おきにGitHub Actionsから実行される想定。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sources import complaints, events, media_reviews, motorsports, sentiment, social_buzz, toyota_news, youtube

JST = timezone(timedelta(hours=9))
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "site" / "data" / "latest.json"


def _with_sentiment(items: list[dict]) -> list[dict]:
    return sentiment.attach_sentiment(items)


def _motorsports_section() -> dict:
    series = motorsports.fetch()
    for s in series.values():
        s["topics"] = _with_sentiment(s["topics"])
        s["results"] = _with_sentiment(s["results"])
        s["standings"] = _with_sentiment(s["standings"])
    return {
        "label": "モータースポーツ(TC America・ARA・スーパー耐久)",
        "series": series,
        "note": (
            "トピックス/レース結果はニュース記事ベースで集約しています。TC Americaのみ"
            "公式サイトの実データからドライバーズランキングをグラフ表示しています"
            "(ARA・スーパー耐久ST-Qを図示しない理由は各カード内に記載)。"
        ),
    }


def build_dashboard() -> dict:
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)

    youtube_data = youtube.fetch(queries=["GR Corolla", "GRMN Corolla"], hl="en", gl="US")
    youtube_data_jp = youtube.fetch(queries=["GRカローラ", "GRMNカローラ"], hl="ja", gl="JP")
    buzz_data = social_buzz.fetch()
    complaint_data = complaints.fetch()

    return {
        "generated_at_utc": now_utc.isoformat(),
        "generated_at_jst": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        "sections": {
            "toyota_news": {
                "label": "トヨタ/販売会社 最新リリース",
                "items": toyota_news.fetch(),
            },
            "youtube_popular": {
                "label": "YouTube 人気動画(グローバル)",
                "items": _with_sentiment(youtube_data["popular"]),
            },
            "youtube_new": {
                "label": "YouTube 新着動画(グローバル)",
                "items": _with_sentiment(youtube_data["new"]),
            },
            "youtube_popular_jp": {
                "label": "YouTube 人気動画(日本語)",
                "items": _with_sentiment(youtube_data_jp["popular"]),
            },
            "youtube_new_jp": {
                "label": "YouTube 新着動画(日本語)",
                "items": _with_sentiment(youtube_data_jp["new"]),
            },
            "social_buzz": {
                "label": "SNSでの話題(X/Facebook 代替指標)",
                "items": _with_sentiment(buzz_data["items"]),
                "note": buzz_data["note"],
            },
            "media_reviews": {
                "label": "自動車メディア評価記事",
                "items": _with_sentiment(media_reviews.fetch()),
            },
            "complaints": {
                "label": "お客様の声・クレーム関連情報",
                "items": _with_sentiment(complaint_data["items_latest"]),
                "items_buzz": _with_sentiment(complaint_data["items_buzz"]),
                "note": complaint_data["note"],
            },
            "motorsports": _motorsports_section(),
            "events": {
                "label": "世界各地のイベント情報",
                "items": _with_sentiment(events.fetch()),
                "note": (
                    "オーナーズミーティング/ミートアップと、GR Corolla自体が主役となる試乗会・"
                    "展示会・著名モーターショーへの出展・GR Garageイベントに絞ってニュース記事から"
                    "集約した簡易カレンダーです。公式のイベント日程一覧ではありません。"
                ),
            },
        },
    }


def main() -> None:
    dashboard = build_dashboard()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote dashboard data to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
