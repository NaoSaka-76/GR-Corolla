"""GR Corollaダッシュボード用データを収集し、site/data/latest.jsonへ出力する。

1日3回(7時/12時/17時 JST)、GitHub Actionsから実行される想定。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sources import complaints, media_reviews, motorsports, sentiment, social_buzz, toyota_news, youtube

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
            "各シリーズ公式サイトのリザルト/ランキング表は構造が異なり自動取得が不安定なため、"
            "ニュース記事ベースでトピックス・レース結果・ランキング話題を集約しています。"
            "正式な最新順位表は各シリーズの検索リンクからご確認ください。"
        ),
    }


def build_dashboard() -> dict:
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)

    youtube_data = youtube.fetch()
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
                "label": "YouTube 人気動画",
                "items": _with_sentiment(youtube_data["popular"]),
            },
            "youtube_new": {
                "label": "YouTube 新着動画",
                "items": _with_sentiment(youtube_data["new"]),
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
                "items": _with_sentiment(complaint_data["items"]),
                "note": complaint_data["note"],
            },
            "motorsports": _motorsports_section(),
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
