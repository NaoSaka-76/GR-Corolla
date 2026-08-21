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

SEARCH_URL = "https://www.youtube.com/results?search_query={query}&hl={hl}&gl={gl}"
WATCH_URL = "https://www.youtube.com/watch?v={video_id}"
_DESCRIPTION_MAX_CHARS = 280

# GitHub Actionsのようなデータセンター発IP(EUリージョン扱いされることがある)からアクセスすると、
# 通常のページの代わりにCookie同意インタースティシャルが返り、ytInitialData/
# ytInitialPlayerResponseの埋め込みJSONごと欠落することがある。既定で同意済みとする
# Cookieを送ることでこれを回避する。
_REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "CONSENT=YES+cb.20210328-17-p0.en+FX+000",
}


def _fetch_raw_results(query: str, hl: str = "en", gl: str = "US") -> list[dict]:
    url = SEARCH_URL.format(query=requests.utils.quote(query), hl=hl, gl=gl)
    resp = requests.get(url, headers=_REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
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
                        "video_id": video_id,
                        "title": title,
                        "url": WATCH_URL.format(video_id=video_id),
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


_DEBUG_LOGGED = False


def _fetch_description(video_id: str) -> str:
    """動画の概要欄(shortDescription)を取得し、ツールチップ表示用に短く整形する。"""
    global _DEBUG_LOGGED
    try:
        resp = requests.get(
            WATCH_URL.format(video_id=video_id), headers=_REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        match = re.search(r"var ytInitialPlayerResponse = ({.*?});", resp.text)
        if not match:
            if not _DEBUG_LOGGED:
                _DEBUG_LOGGED = True
                print(f"[youtube] DEBUG watch page for {video_id}: status={resp.status_code} len={len(resp.text)}")
                print(f"[youtube] DEBUG body head: {resp.text[:500]!r}")
            return ""
        data = json.loads(match.group(1))
        desc = (data.get("videoDetails", {}) or {}).get("shortDescription", "") or ""
        desc = re.sub(r"\s+", " ", desc).strip()
        if len(desc) > _DESCRIPTION_MAX_CHARS:
            desc = desc[:_DESCRIPTION_MAX_CHARS].rsplit(" ", 1)[0] + "…"
        return desc
    except Exception as exc:  # noqa: BLE001
        if not _DEBUG_LOGGED:
            _DEBUG_LOGGED = True
            print(f"[youtube] DEBUG exception for {video_id}: {exc!r}")
        return ""


def fetch(queries: list[str], top_n: int = 20, hl: str = "en", gl: str = "US") -> dict:
    """複数クエリ(GR Corolla / GRMN Corollaなど)を合算し、人気動画・新着動画を返す。

    表示対象になる動画についてのみ概要欄を追加取得し、ツールチップ表示用の
    "description" フィールドとして各動画に付与する。
    """
    raw: list[dict] = []
    seen_ids: set[str] = set()
    fetch_failed = False
    for query in queries:
        try:
            results = _fetch_raw_results(query, hl=hl, gl=gl)
        except Exception:  # noqa: BLE001
            fetch_failed = True
            continue
        for v in results:
            if v["video_id"] in seen_ids:
                continue
            seen_ids.add(v["video_id"])
            raw.append(v)

    if not raw:
        message = (
            "YouTube検索結果を取得できませんでした(ページ構造の変更の可能性)"
            if fetch_failed
            else "該当する動画が見つかりませんでした"
        )
        fallback = {
            "title": message,
            "url": f"https://www.youtube.com/results?search_query={requests.utils.quote(queries[0])}",
            "source": "YouTube",
            "published": "",
        }
        return {"popular": [fallback], "new": [fallback]}

    popular = sorted(raw, key=lambda v: v["view_count"], reverse=True)[:top_n]
    new = sorted(raw, key=lambda v: v["recency_seconds"])[:top_n]

    to_describe = {v["video_id"]: v for v in (popular + new)}
    described_count = 0
    for video_id, v in to_describe.items():
        v["description"] = _fetch_description(video_id)
        if v["description"]:
            described_count += 1
    print(f"[youtube] description fetched for {described_count}/{len(to_describe)} videos ({queries[0]!r})")

    return {"popular": popular, "new": new}
