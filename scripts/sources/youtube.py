"""YouTube検索ページの軽量スクレイピングでGR Corolla動画の人気/新着を取得する。

公式YouTube Data APIキーを利用しないため、検索結果ページに埋め込まれた
`ytInitialData` JSONを正規表現で抽出するベストエフォート実装。
YouTube側のページ構造変更で失敗する可能性があり、その場合は空リストを返す。
"""

from __future__ import annotations

import json
import re

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT, parse_relative_seconds_ago, parse_view_count

SEARCH_URL = "https://www.youtube.com/results?search_query={query}&hl=en"


def _fetch_raw_results(query: str) -> list[dict]:
    url = SEARCH_URL.format(query=requests.utils.quote(query))
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    match = re.search(r"var ytInitialData = ({.*?});</script>", resp.text)
    if not match:
        return []
    data = json.loads(match.group(1))

    videos: list[dict] = []
    try:
        sections = (
            data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]
            ["sectionListRenderer"]["contents"]
        )
        for section in sections:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                v = item.get("videoRenderer")
                if not v:
                    continue
                title = "".join(run.get("text", "") for run in v.get("title", {}).get("runs", []))
                video_id = v.get("videoId", "")
                view_count_text = v.get("viewCountText", {}).get("simpleText", "")
                published_text = v.get("publishedTimeText", {}).get("simpleText", "")
                channel = ""
                owner = v.get("ownerText", {}).get("runs", [])
                if owner:
                    channel = owner[0].get("text", "")
                if not title or not video_id:
                    continue
                videos.append(
                    {
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "source": channel or "YouTube",
                        "published": published_text,
                        "view_count_text": view_count_text,
                        "view_count": parse_view_count(view_count_text),
                        "recency_seconds": parse_relative_seconds_ago(published_text),
                        "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                    }
                )
    except (KeyError, TypeError):
        return []
    return videos


def fetch(query: str = "GR Corolla", top_n: int = 8) -> dict:
    """人気動画(再生数順)と新着動画(公開日時順)をまとめて返す。"""
    try:
        raw = _fetch_raw_results(query)
    except Exception as exc:  # noqa: BLE001
        return {
            "popular": [{"title": f"[取得エラー] {exc}", "url": "", "source": "error", "published": ""}],
            "new": [],
        }

    if not raw:
        fallback = {
            "title": "YouTube検索結果を取得できませんでした(ページ構造の変更の可能性)",
            "url": f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}",
            "source": "YouTube",
            "published": "",
        }
        return {"popular": [fallback], "new": [fallback]}

    popular = sorted(raw, key=lambda v: v["view_count"], reverse=True)[:top_n]
    new = sorted(raw, key=lambda v: v["recency_seconds"])[:top_n]
    return {"popular": popular, "new": new}
