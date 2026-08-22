"""GR Corollaが参戦するモータースポーツの年間レース日程を取得する。

TC America・スーパー耐久・ARAともに公式サイトの静的HTMLから日程を取得する。
ARAはWix製ページビルダーで描画されHTML構造がイベントごとに微妙に揺れるが、
各イベントが `<h6 class="font_6...">` ブロック単位(1〜複数ブロックに分割される
ケースあり)で構成されており、日付パターンを軸にブロックを分類・結合すれば
概ね安定して抽出できることを確認済み(1件のみ元HTML自体が破損しており抽出不可)。

なお、ARAのシリーズランキング(順位表)は公式サイト自体には一切埋め込まれておらず
("1st"/"points"等の数値データがページ内に存在しない)、非公式の第三者サイト
(sneakattackrally.com)がJavaScriptで描画する非公開フォーマットのデータに
依存しているため、ランキングはスクレイピング対象外とし検索リンクのみ提供する
(standings.py参照)。
"""

from __future__ import annotations

import html as html_module
import re
from datetime import date

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT

TC_AMERICA_CALENDAR_URL = "https://tcamerica.us/calendar"
SUPER_TAIKYU_INDEX_URL = "https://supertaikyu.com/race/index.html"
ARA_SCHEDULE_URL = "https://www.americanrallyassociation.org/2026-ara-schedule"

_ARA_DATE_RE = re.compile(r"^[A-Z][a-z]+ \d{1,2}(?:\s*[-–]\s*\d{1,2})?,?\s*\d{4}$")
_ARA_REGION_RE = re.compile(r"^\(.*\)$")

_MONTH_NUM = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _month_num(text: str) -> int:
    return _MONTH_NUM.get(text.strip()[:3].upper(), 0)


def _status(sort_key: int) -> str:
    today_key = date.today().year * 10000 + date.today().month * 100 + date.today().day
    return "upcoming" if sort_key >= today_key else "completed"


def fetch_tc_america_schedule() -> list[dict]:
    """TC America公式カレンダー(開催予定+開催済み)を取得する。"""
    session = _session()
    events: list[dict] = []
    try:
        resp = session.get(TC_AMERICA_CALENDAR_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        html_text = resp.text

        date_block_re = re.compile(
            r'"calendar__date-number">(\d+)</span>\s*'
            r'<span class="calendar__date-month">([A-Z]+)</span>\s*'
            r'<span class="calendar__date-year">(\d+)</span>',
            re.S,
        )

        for chunk in html_text.split('calendar__list-item">')[1:]:
            chunk = chunk[:3000]
            dates = date_block_re.findall(chunk)
            track_m = re.search(r'calendar__race-header">([^<]*)</h3', chunk)
            round_m = re.search(r'calendar__race-text">([^<]*)</span', chunk)
            if not dates or not track_m:
                continue
            s_day, s_month, s_year = dates[0]
            sort_key = int(s_year) * 10000 + _month_num(s_month) * 100 + int(s_day)
            if len(dates) >= 2:
                e_day, e_month, e_year = dates[1]
                date_range = (
                    f"{s_month} {s_day}–{e_day}, {e_year}"
                    if s_month == e_month
                    else f"{s_month} {s_day}–{e_month} {e_day}, {e_year}"
                )
            else:
                date_range = f"{s_month} {s_day}, {s_year}"
            events.append(
                {
                    "round": html_module.unescape(round_m.group(1).strip() if round_m else ""),
                    "track": html_module.unescape(track_m.group(1).strip()),
                    "date_range": date_range,
                    "status": "upcoming",
                    "sort_key": sort_key,
                }
            )

        full_month_re = re.compile(r"(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})")
        single_day_re = re.compile(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})")

        for chunk in html_text.split('past-events__list-item">')[1:]:
            chunk = chunk[:2000]
            spans = re.findall(r'piped-list-span">(.*?)</span>', chunk, re.S)
            spans = [re.sub(r"<[^>]+>", " ", s).strip() for s in spans]
            if len(spans) < 3:
                continue
            date_text, track_country, round_text = spans[0], spans[1], spans[2]
            m = full_month_re.search(date_text)
            if m:
                s_day, _e_day, month_name, year = m.groups()
            else:
                m = single_day_re.search(date_text)
                if not m:
                    continue
                s_day, month_name, year = m.groups()
            sort_key = int(year) * 10000 + _month_num(month_name) * 100 + int(s_day)
            events.append(
                {
                    "round": html_module.unescape(round_text),
                    "track": html_module.unescape(re.sub(r"\s+", " ", track_country).strip()),
                    "date_range": date_text,
                    "status": "completed",
                    "sort_key": sort_key,
                }
            )
    except Exception:  # noqa: BLE001
        return []

    events.sort(key=lambda e: e["sort_key"])
    return events


def fetch_super_taikyu_schedule() -> list[dict]:
    """スーパー耐久公式レース一覧(テストデー含む全ラウンド)を取得する。"""
    session = _session()
    events: list[dict] = []
    try:
        resp = session.get(SUPER_TAIKYU_INDEX_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        # サーバーがcharsetを明示しないため、requestsの既定(ISO-8859-1)ではなく
        # 実際の文字コード推定を使う(このサイトは実質UTF-8)。
        resp.encoding = resp.apparent_encoding or "utf-8"
        html_text = resp.text

        blocks = re.findall(
            r'<div class="Race_BX_Wrapp">.*?(?=<div class="Race_BX_Wrapp">|\Z)', html_text, re.S
        )
        for block in blocks:
            rd_m = re.search(r'Race_BX_Rd">([^<]*)<', block)
            date_m = re.search(r'Race_BX_Date">\s*([^<]*)<', block)
            circuit_m = re.search(r'Race_BX_Circuit">([^<]*)<', block)
            name_m = re.search(r'Race_BX_Name">(.*?)</div>', block, re.S)
            if not (rd_m and date_m):
                continue
            date_text = date_m.group(1).strip()
            dm = re.match(r"(\d{4})/(\d{1,2})/(\d{1,2})(?:-(\d{1,2}))?", date_text)
            if not dm:
                continue
            year, month, day, _end_day = dm.groups()
            sort_key = int(year) * 10000 + int(month) * 100 + int(day)
            name_txt = re.sub(r"<!--.*?-->", "", name_m.group(1)) if name_m else ""
            name_txt = re.sub(r"<[^>]+>", "", name_txt).strip()
            events.append(
                {
                    "round": rd_m.group(1).strip(),
                    "track": (circuit_m.group(1).strip() if circuit_m else ""),
                    "name": name_txt,
                    "date_range": date_text.replace("/", "."),
                    "status": _status(sort_key),
                    "sort_key": sort_key,
                }
            )
    except Exception:  # noqa: BLE001
        return []

    events.sort(key=lambda e: e["sort_key"])
    return events


def fetch_ara_schedule() -> list[dict]:
    """ARA公式サイトのイベント一覧(Wix製リッチテキストブロック)を取得する。

    各イベントは "<h6 class=\"font_6...\">" ブロックとして描画されるが、
    編集履歴の都合でブロック分割が一定しない(1ブロックに全情報が収まる
    イベントもあれば、name/region → 空ブロック(区切り) → date → location と
    複数ブロックに分かれるイベントもある)。日付パターンの有無でブロックを
    分類し、直前の未確定イベント(pending)に結合するか新規イベントとして
    扱うかを判定する。日付が最後まで見つからなかったイベントは(元HTML自体が
    壊れているケースがあるため)無理に補完せず捨てる。
    """
    session = _session()
    events: list[dict] = []
    try:
        resp = session.get(ARA_SCHEDULE_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        html_text = resp.text

        blocks: list[tuple[list[str], str | None]] = []
        for m in re.finditer(r'<h6 class="font_6[^"]*"[^>]*>(.*?)</h6>', html_text, re.S):
            content = m.group(1)
            href_m = re.search(
                r'href="(https://www\.americanrallyassociation\.org/[a-z0-9-]+)"', content
            )
            text = re.sub(r"<br[^>]*>", "\n", content)
            text = re.sub(r"<[^>]+>", "", text)
            text = html_module.unescape(text).replace("\xa0", " ")
            lines = [l.strip() for l in text.split("\n") if l.strip() and l.strip() != "​"]
            blocks.append((lines, href_m.group(1) if href_m else None))

        pending: dict | None = None

        def flush() -> None:
            nonlocal pending
            if pending and pending.get("name") and pending.get("date"):
                events.append(pending)
            pending = None

        for lines, href in blocks:
            if not lines:
                continue
            if lines == ["Media"]:
                # スケジュール本体の終端(以降はフッターのナビゲーションメニュー)
                flush()
                break

            date_idx = next((i for i, l in enumerate(lines) if _ARA_DATE_RE.match(l)), None)

            if date_idx is not None:
                pre = lines[:date_idx]
                name_parts = [l for l in pre if not _ARA_REGION_RE.match(l)]
                region_parts = [l.strip("()") for l in pre if _ARA_REGION_RE.match(l)]
                post = lines[date_idx + 1 :]
                if pending and "date" not in pending and not pre:
                    # 直前のname/regionブロックに続く「日付のみ」ブロック
                    pending["date"] = lines[date_idx]
                    if post:
                        pending["location"] = post
                        flush()
                else:
                    flush()
                    pending = {
                        "name": " ".join(name_parts),
                        "region": "/".join(region_parts),
                        "date": lines[date_idx],
                        "href": href,
                    }
                    if post:
                        pending["location"] = post
                        flush()
            else:
                has_region = any(_ARA_REGION_RE.match(l) for l in lines)
                if pending and "date" in pending and "location" not in pending:
                    pending["location"] = lines
                    flush()
                elif pending and "date" not in pending:
                    if has_region:
                        pending["region"] = "/".join(
                            l.strip("()") for l in lines if _ARA_REGION_RE.match(l)
                        )
                    else:
                        pending["name"] = (pending.get("name", "") + " " + " ".join(lines)).strip()
                else:
                    flush()
                    pending = {
                        "name": " ".join(l for l in lines if not _ARA_REGION_RE.match(l)),
                        "region": "/".join(l.strip("()") for l in lines if _ARA_REGION_RE.match(l)),
                        "href": href,
                    }
        flush()

        for ev in events:
            m = re.match(r"([A-Za-z]+) (\d{1,2})(?:\s*[-–]\s*\d{1,2})?,?\s*(\d{4})", ev["date"])
            if not m:
                continue
            month_name, day, year = m.groups()
            ev["sort_key"] = int(year) * 10000 + _month_num(month_name) * 100 + int(day)
        events = [ev for ev in events if "sort_key" in ev]

        for ev in events:
            ev["round"] = ev.pop("region", "")
            ev["track"] = ", ".join(ev.pop("location", []))
            ev["date_range"] = ev.pop("date")
            ev.pop("href", None)
    except Exception:  # noqa: BLE001
        return []

    events.sort(key=lambda e: e["sort_key"])
    return events


def _finalize(events: list[dict]) -> list[dict]:
    for e in events:
        e["status"] = _status(e["sort_key"])
        del e["sort_key"]
    return events


def fetch_all() -> dict:
    return {
        "tc_america": _finalize(fetch_tc_america_schedule()),
        "super_taikyu": _finalize(fetch_super_taikyu_schedule()),
        "ara": _finalize(fetch_ara_schedule()),
    }
