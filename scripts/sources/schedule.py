"""GR Corollaが参戦するモータースポーツの年間レース日程を取得する。

TC America(公式カレンダーページ)とスーパー耐久(公式レース一覧ページ)は
静的HTMLに開催日・サーキット名・大会名が明記されており、比較的安定して取得できる。
ARAは日程情報が非公式のページビルダー(Wix)で描画され、構造がイベントごとに
微妙に揺れて誤抽出のリスクが高いため、スクレイピングはせず公式スケジュールページへの
直接リンクのみを提供する。
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


def _finalize(events: list[dict]) -> list[dict]:
    for e in events:
        e["status"] = _status(e["sort_key"])
        del e["sort_key"]
    return events


def fetch_all() -> dict:
    return {
        "tc_america": _finalize(fetch_tc_america_schedule()),
        "super_taikyu": _finalize(fetch_super_taikyu_schedule()),
        "ara": {"link": ARA_SCHEDULE_URL},
    }
