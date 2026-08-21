"""YouTube検索ページの軽量スクレイピングでGR Corolla動画の人気/新着を取得する。

公式YouTube Data APIキーを利用しないため、検索結果ページに埋め込まれた
`ytInitialData` JSONを正規表現で抽出するベストエフォート実装。
YouTube側のページ構造変更で失敗する可能性があり、その場合は空リストを返す。
"""

from __future__ import annotations

import json
import re
import time

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT, parse_relative_seconds_ago, parse_view_count

SEARCH_URL = "https://www.youtube.com/results?search_query={query}&hl={hl}&gl={gl}"
WATCH_URL = "https://www.youtube.com/watch?v={video_id}"
_DESCRIPTION_MAX_CHARS = 280
_MAX_DESCRIPTIONS_PER_SIDE = 10  # 人気/新着それぞれ上位何件まで概要欄を取得するか
_DESCRIPTION_REQUEST_DELAY = 0.6  # 秒。連続アクセスによるボット判定を避けるための間隔
_DESCRIPTION_RETRY_DELAY = 2.5  # 429(レート制限)発生時の再試行までの待機秒数

_REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    # GitHub Actions等のデータセンター発IPからのアクセスでCookie同意ページに
    # リダイレクトされるのを避けるため、同意済みとするCookieを送る。
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


def _fetch_description_once(video_id: str) -> tuple[str, int | None]:
    """概要欄取得を1回試みる。戻り値は (description, http_status)。"""
    resp = requests.get(WATCH_URL.format(video_id=video_id), headers=_REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 429:
        return "", 429
    resp.raise_for_status()
    match = re.search(r"var ytInitialPlayerResponse = ({.*?});", resp.text)
    if not match:
        return "", resp.status_code
    data = json.loads(match.group(1))
    desc = (data.get("videoDetails", {}) or {}).get("shortDescription", "") or ""
    desc = re.sub(r"\s+", " ", desc).strip()
    if len(desc) > _DESCRIPTION_MAX_CHARS:
        desc = desc[:_DESCRIPTION_MAX_CHARS].rsplit(" ", 1)[0] + "…"
    return desc, resp.status_code


def _fetch_description(video_id: str) -> str:
    """動画の概要欄(shortDescription)を取得する。

    YouTube側のレート制限(429)が発生した場合は一度だけ間隔を空けて再試行し、
    それでも失敗する場合は諦めて空文字を返す(ツールチップが表示されないだけで、
    ダッシュボード全体の動作には影響しない)。
    """
    try:
        desc, status = _fetch_description_once(video_id)
        if status == 429:
            time.sleep(_DESCRIPTION_RETRY_DELAY)
            desc, _status = _fetch_description_once(video_id)
        return desc
    except Exception:  # noqa: BLE001
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

    # 概要欄はYouTube側のボット対策(連続アクセスでの429)にかかりやすいため、
    # 表示件数の全件ではなく上位のみに絞り、リクエスト間隔も空ける。
    to_describe = {
        v["video_id"]: v
        for v in (popular[:_MAX_DESCRIPTIONS_PER_SIDE] + new[:_MAX_DESCRIPTIONS_PER_SIDE])
    }
    described_count = 0
    for i, (video_id, v) in enumerate(to_describe.items()):
        if i > 0:
            time.sleep(_DESCRIPTION_REQUEST_DELAY)
        v["description"] = _fetch_description(video_id)
        if v["description"]:
            described_count += 1
    print(f"[youtube] description fetched for {described_count}/{len(to_describe)} videos ({queries[0]!r})")

    return {"popular": popular, "new": new}
