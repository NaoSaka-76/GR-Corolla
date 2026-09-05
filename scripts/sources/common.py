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
from email.utils import parsedate_to_datetime

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


def sort_by_recency(items: list[dict]) -> list[dict]:
    """"published"(RFC822形式)を新しい順に並べ替える。解析できないものは末尾に回す。"""

    def _key(item: dict) -> datetime:
        raw = item.get("published", "")
        if not raw:
            return datetime.min.replace(tzinfo=timezone.utc)
        try:
            dt = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            return datetime.min.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    return sorted(items, key=_key, reverse=True)


_JAPANESE_CHAR_RE = re.compile(r"[぀-ヿ一-鿿]")


def needs_japanese_translation(text: str) -> bool:
    """日本語の文字を1つも含まない場合にTrueを返す(=英語など翻訳が必要な見出しとみなす)。"""
    return bool(text) and not _JAPANESE_CHAR_RE.search(text)


def translate_to_japanese(text: str) -> str | None:
    """Google翻訳の非公式エンドポイントで英語→日本語に翻訳する。

    公式APIキーを使わない無料のベストエフォート実装で、エンドポイントの仕様変更や
    レート制限により失敗する可能性がある。失敗時はNoneを返し、呼び出し側は原文のみを
    表示する(見出し文の翻訳なので、多少の意訳・機械翻訳的な表現になる点はご容赦を)。
    """
    if not text:
        return None
    try:
        resp = _session().get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "en", "tl": "ja", "dt": "t", "q": text},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        translated = "".join(chunk[0] for chunk in data[0] if chunk and chunk[0])
        translated = translated.strip()
        return translated or None
    except Exception as exc:  # noqa: BLE001
        global _last_translation_error
        _last_translation_error = f"{type(exc).__name__}: {exc}"
        return None


_last_translation_error: str | None = None


def attach_japanese_translations(items: list[dict], limit: int = 400) -> None:
    """各itemの"title"が日本語を含まない場合、"title_ja"として翻訳を付与する。

    30分毎の実行時間や翻訳エンドポイントへの負荷を抑えるため、1回の実行あたりの
    翻訳件数に上限を設けている(通常の運用では上限に達しない想定)。
    """
    count = 0
    success = 0
    for item in items:
        if count >= limit:
            break
        title = item.get("title")
        if not title or not needs_japanese_translation(title):
            continue
        count += 1
        translated = translate_to_japanese(title)
        if translated and translated != title:
            item["title_ja"] = translated
            success += 1
    print(f"[translate] attempted={count} success={success} last_error={_last_translation_error}")


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


_RELATIVE_UNITS_JP = [
    ("秒", 1),
    ("分", 60),
    ("時間", 3600),
    ("週間", 604800),
    ("ヶ月", 2629800),
    ("か月", 2629800),
    ("カ月", 2629800),
    ("日", 86400),
    ("月", 2629800),
    ("年", 31557600),
]


def parse_relative_seconds_ago(text: str) -> int:
    """'3 hours ago' や '4時間前' のような相対時刻テキストを秒数に変換する(新しいほど小さい値)。"""
    if not text:
        return 10**12

    match = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)", text.lower())
    if match:
        value, unit = int(match.group(1)), match.group(2)
        return value * _RELATIVE_UNITS.get(unit, 10**9)

    # 日本語表記(例: "4時間前", "13日前", "11か月前")。単位は長いものから順に照合する。
    for unit, seconds in _RELATIVE_UNITS_JP:
        jp_match = re.search(rf"(\d+)\s*{unit}", text)
        if jp_match:
            return int(jp_match.group(1)) * seconds

    return 10**12
