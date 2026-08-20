"""GR Corolla ダッシュボード用の共通ヘルパー。

公式APIキー(YouTube Data API / X API / Facebook Graph API)を使わずに、
Google News RSS・Reddit公開検索・YouTube検索ページの軽量スクレイピングで
代替データを収集する。取得元は無料公開エンドポイントのみで、
構造変化やレート制限により結果が空になる場合がある。
"""

from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, timezone

import feedparser
import requests

USER_AGENT = "Mozilla/5.0 (compatible; GRCorollaDashboardBot/1.0; +https://github.com/NaoSaka-76/GR-Corolla)"

REQUEST_TIMEOUT = 15


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_google_news_rss(query: str, hl: str = "en-US", gl: str = "US", ceid: str = "US:en", limit: int = 10) -> list[dict]:
    """Google News RSS検索。APIキー不要の公開フィード。"""
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    items: list[dict] = []
    try:
        resp = _session().get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:limit]:
            source = ""
            if hasattr(entry, "source") and hasattr(entry.source, "title"):
                source = entry.source.title
            items.append(
                {
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", ""),
                    "source": source or "Google News",
                    "published": entry.get("published", ""),
                }
            )
    except Exception as exc:  # noqa: BLE001
        items.append({"title": f"[取得エラー] {query}", "url": "", "source": "error", "published": str(exc)})
    return items


def fetch_reddit_search(query: str, sort: str = "hot", t: str = "week", limit: int = 10) -> list[dict]:
    """Reddit公開検索API(認証不要, User-Agent必須)。"""
    encoded = urllib.parse.quote(query)
    url = f"https://www.reddit.com/search.json?q={encoded}&sort={sort}&t={t}&limit={limit}"
    items: list[dict] = []
    try:
        resp = _session().get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            created = d.get("created_utc")
            published = (
                datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else ""
            )
            items.append(
                {
                    "title": d.get("title", "").strip(),
                    "url": f"https://www.reddit.com{d.get('permalink', '')}",
                    "source": f"r/{d.get('subreddit', 'reddit')}",
                    "published": published,
                    "score": d.get("score", 0),
                }
            )
    except Exception as exc:  # noqa: BLE001
        items.append({"title": f"[取得エラー] {query}", "url": "", "source": "error", "published": str(exc)})
    return items


def dedupe_by_url(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        key = item.get("url") or item.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


_VIEW_MULTIPLIERS = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def parse_view_count(text: str) -> int:
    """'1.2M回視聴' や '45K views' のようなテキストを数値に変換する。"""
    if not text:
        return 0
    match = re.search(r"([\d,.]+)\s*([kKmMbB]?)", text.replace(",", ""))
    if not match:
        return 0
    number_str, suffix = match.group(1), match.group(2).lower()
    try:
        number = float(number_str)
    except ValueError:
        return 0
    return int(number * _VIEW_MULTIPLIERS.get(suffix, 1))


_RELATIVE_UNITS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 604800,
    "month": 2629800,
    "year": 31557600,
}


def parse_relative_seconds_ago(text: str) -> int:
    """'3 hours ago' のような相対時刻テキストを秒数に変換する(新しいほど小さい値)。"""
    if not text:
        return 10**12
    match = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)", text.lower())
    if not match:
        return 10**12
    value, unit = int(match.group(1)), match.group(2)
    return value * _RELATIVE_UNITS.get(unit, 10**9)
