"""モータースポーツのシリーズランキング(実データ)を取得する。

TC America公式サイト(tcamerica.us)はシーズン/クラスをHTMLの<select>から動的に解決でき、
順位表も静的HTMLテーブルとして提供されているため、実データでのグラフ化が可能。

ARA(米国ラリー選手権)公式サイトには「ポイント付きのフル順位表」はないが、
championship-standingsページにNational Driver/Co-Driverそれぞれの上位3名(表彰台)を
写真付きで紹介するセクションが実在し、写真のalt属性にドライバー名が、メーカーロゴ画像に
所属ブランドが埋め込まれている。これは静的HTMLかつ位置(First/Second/Third)と画像の
対応が崩れないため、上位3名に限り安全に抽出できる。フルの順位表(全ポイント)は
非公式の第三者サイト(sneakattackrally.com)がJavaScriptで描画するSPAに依存しており、
裏側のJSONも非公開・非文書化のフォーマットのため、そちらは引き続き対象外とする。

スーパー耐久 ST-Qクラス(水素エンジンGRカローラが参戦)も対象外: 開発車両専用クラスのため、
そもそもポイントによるシリーズランキングの対象になっていない(公式サイトの
年間ランキングボードにST-Qは掲載されていない)。
"""

from __future__ import annotations

import html as html_module
import re
from datetime import datetime, timezone, timedelta

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT

BASE_URL = "https://tcamerica.us"
STANDINGS_URL = f"{BASE_URL}/standings"
RESULTS_URL = f"{BASE_URL}/results"
TARGET_CLASS_LABEL = "TC America TC Drivers"
JST = timezone(timedelta(hours=9))
MAX_TRACKS_FOR_CAR_MAP = 10


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _extract_select_options(html_text: str, select_name: str) -> list[tuple[str, str]]:
    block = re.search(rf'<select[^>]*name="{select_name}"[^>]*>(.*?)</select>', html_text, re.S)
    if not block:
        return []
    options = re.findall(r'<option\s+value="([^"]*)"[^>]*>([^<]*)</option>', block.group(1))
    return [(value, html_module.unescape(label.strip())) for value, label in options]


def _current_season_id(html_text: str, year: int) -> str | None:
    for value, label in _extract_select_options(html_text, "filter_season_id"):
        if str(year) in label:
            return value
    return None


def _target_standing_type_id(html_text: str) -> str | None:
    for value, label in _extract_select_options(html_text, "filter_standing_type"):
        if label.strip() == TARGET_CLASS_LABEL:
            return value
    return None


def _parse_standings_table(html_text: str) -> list[dict]:
    table = re.search(r'<table class="table standing".*?</table>', html_text, re.S)
    if not table:
        return []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(0), re.S)
    results: list[dict] = []
    for row in rows[1:]:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
        if len(cells) < 4 or not cells[0].isdigit():
            continue
        points_raw = re.sub(r"[^\d]", "", cells[3]) or "0"
        results.append({"position": int(cells[0]), "name": cells[1], "points": int(points_raw)})
    return results


def _parse_race_classification(html_text: str) -> list[dict]:
    """個別レースの完全クラシフィケーション表から driver/team/car を抽出する。"""
    table = re.search(r"<table.*?</table>", html_text, re.S)
    if not table:
        return []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(0), re.S)
    if not rows:
        return []
    header = [re.sub(r"<[^>]+>", "", c).strip().lower() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", rows[0], re.S)]
    try:
        driver_idx = header.index("drivers")
        team_idx = header.index("team")
        car_idx = header.index("car")
    except ValueError:
        return []

    entries: list[dict] = []
    for row in rows[1:]:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
        if len(cells) <= max(driver_idx, team_idx, car_idx):
            continue
        driver, team, car = cells[driver_idx], cells[team_idx], cells[car_idx]
        if driver and car:
            entries.append({"driver": driver, "team": team, "car": car})
    return entries


def fetch_tc_america_car_map() -> dict[str, dict]:
    """TC Americaの各レース完全結果から driver名 -> {team, car} のマップを組み立てる。

    ドライバーズランキング表そのものにはチーム/車種の列が存在しないため、
    シーズン中の各レースウィークエンドの完全クラシフィケーション(結果ページ)を
    巡回して補完する。複数レースに出た場合は、より新しいレースの情報で上書きする。
    """
    session = _session()
    car_map: dict[str, dict] = {}
    try:
        index_resp = session.get(RESULTS_URL, timeout=REQUEST_TIMEOUT)
        index_resp.raise_for_status()
        track_paths = list(dict.fromkeys(re.findall(r'href="(/results/\d{4}/[a-z0-9-]+)"', index_resp.text)))

        for track_path in track_paths[:MAX_TRACKS_FOR_CAR_MAP]:
            try:
                track_resp = session.get(f"{BASE_URL}{track_path}", timeout=REQUEST_TIMEOUT)
                if not track_resp.ok:
                    continue
                race_paths = re.findall(rf'href="({re.escape(track_path)}/race-\d+-tcam)"', track_resp.text)
                if not race_paths:
                    continue
                race_resp = session.get(f"{BASE_URL}{race_paths[0]}", timeout=REQUEST_TIMEOUT)
                if not race_resp.ok:
                    continue
                for entry in _parse_race_classification(race_resp.text):
                    car_map[entry["driver"]] = {"team": entry["team"], "car": entry["car"]}
            except requests.RequestException:
                continue
    except Exception:  # noqa: BLE001
        return car_map
    return car_map


def fetch_tc_america_driver_standings(limit: int = 10) -> dict:
    """TC America「TC」クラス ドライバーズランキング(公式サイト実データ)。

    ランキング表自体にはチーム/車種の列がないため、各レースの完全結果ページから
    補完した driver -> {team, car} マップで各行に "team" / "car" /
    "is_gr_corolla" を付与する。
    """
    session = _session()
    try:
        base_resp = session.get(STANDINGS_URL, timeout=REQUEST_TIMEOUT)
        base_resp.raise_for_status()
        base_html = base_resp.text

        season_id = _current_season_id(base_html, datetime.now(JST).year)
        standing_type_id = _target_standing_type_id(base_html)
        if not season_id or not standing_type_id:
            return {"standings": [], "error": "対象シーズン/クラスを公式サイト上で特定できませんでした"}

        resp = session.get(
            STANDINGS_URL,
            params={"filter_standing_type": standing_type_id, "filter_season_id": season_id},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        rows = _parse_standings_table(resp.text)[:limit]

        if rows:
            car_map = fetch_tc_america_car_map()
            for row in rows:
                info = car_map.get(row["name"], {})
                car = info.get("car", "")
                row["team"] = info.get("team", "")
                row["car"] = car
                row["is_gr_corolla"] = "corolla" in car.lower()

        return {
            "standings": rows,
            "error": None if rows else "現在、順位データが空です(シーズン開幕前などの可能性があります)",
        }
    except Exception as exc:  # noqa: BLE001
        return {"standings": [], "error": f"取得エラー: {exc}"}


ARA_STANDINGS_URL = "https://www.americanrallyassociation.org/2026-championship-standings"


def _clean_brand(alt_text: str) -> str:
    text = re.sub(r"[_\s]*logo[_\s]*", "", alt_text, flags=re.IGNORECASE)
    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace("_", " ").strip()
    return text.title() if text else ""


def fetch_ara_podium() -> dict:
    """ARA公式サイトのNational Driver/Co-Driver上位3名(表彰台)を取得する。

    "First"/"Second"/"Third"という見出しの直後に、ドライバー写真(alt=氏名)と
    メーカーロゴ画像が並ぶ構成が崩れないことを確認済み。ドライバー名はh4要素の
    位置ではなく写真のalt属性から取る(セクションによりh4の並び方が異なり、
    位置ベースだと名前を取り違えるリスクがあるため)。
    """
    session = _session()
    try:
        resp = session.get(ARA_STANDINGS_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        html_text = resp.text

        label_positions: list[tuple[int, str]] = []
        for m in re.finditer(r'<h6 class="font_6[^"]*"[^>]*>(.*?)</h6>', html_text, re.S):
            text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if text in ("First", "Second", "Third"):
                label_positions.append((m.start(), text))

        entries: list[dict] = []
        for i, (pos, label) in enumerate(label_positions):
            end = label_positions[i + 1][0] if i + 1 < len(label_positions) else pos + 2000
            window = html_text[pos:end]
            alts = re.findall(r'alt="([^"]+?)(?:\.png|\.jpg|\.jpeg)?"', window)
            name = None
            brand = None
            for alt in alts:
                if "logo" in alt.lower():
                    if brand is None:
                        brand = _clean_brand(alt)
                elif name is None:
                    name = html_module.unescape(alt.strip())
            if name:
                entries.append({"position": label, "name": name, "brand": brand or ""})

        # 最初の3件=National Driver Standings、次の3件=National Co-Driver Standings
        drivers = entries[:3]
        codrivers = entries[3:6]
        for row in drivers:
            row["is_gr_corolla"] = "toyota" in row["brand"].lower()

        return {
            "drivers": drivers,
            "codrivers": codrivers,
            "error": None if drivers else "上位3名の情報を取得できませんでした",
        }
    except Exception as exc:  # noqa: BLE001
        return {"drivers": [], "codrivers": [], "error": f"取得エラー: {exc}"}
