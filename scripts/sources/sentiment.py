"""記事タイトルからポジティブ/ネガティブを推定する軽量センチメント判定。

公式の感情分析APIは使わず、英語はVADER(ルールベース・オフライン)、
日本語は自動車レビュー文脈向けに手作りした極性辞書でスコアリングする。
見出し(短文)のみを対象とした簡易推定であり、精度は限定的。
"""

from __future__ import annotations

import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

_JAPANESE_RE = re.compile(r"[぀-ヿ一-鿿]")

_POSITIVE_JP = [
    "最高", "絶賛", "好評", "素晴らしい", "快適", "楽しい", "感動", "満足", "おすすめ",
    "期待", "進化", "優勝", "勝利", "表彰台", "速い", "高評価", "人気", "魅力", "上質",
    "刺激的", "面白い", "ワクワク", "称賛", "受賞", "成功", "好調", "圧勝",
]
_NEGATIVE_JP = [
    "不具合", "クレーム", "故障", "リコール", "不満", "残念", "失望", "問題", "欠陥",
    "トラブル", "苦情", "炎上", "批判", "酷評", "低評価", "遅い", "高すぎる", "がっかり",
    "不安", "事故", "損傷", "不良", "リタイア", "敗北", "失敗", "不振",
]


_MAX_REASONS = 4


def _score_japanese(text: str) -> tuple[float, list[str], list[str]]:
    pos_hits = [w for w in _POSITIVE_JP if w in text]
    neg_hits = [w for w in _NEGATIVE_JP if w in text]
    pos = sum(text.count(w) for w in pos_hits)
    neg = sum(text.count(w) for w in neg_hits)
    if pos == 0 and neg == 0:
        return 0.0, [], []
    return (pos - neg) / (pos + neg), pos_hits, neg_hits


_WORD_RE = re.compile(r"[A-Za-z']+")


def _score_english(text: str) -> tuple[float, list[str], list[str]]:
    compound = _analyzer.polarity_scores(text)["compound"]
    pos_hits: list[str] = []
    neg_hits: list[str] = []
    for token in _WORD_RE.findall(text):
        word_score = _analyzer.lexicon.get(token.lower())
        if word_score is None:
            continue
        if word_score > 0:
            pos_hits.append(token)
        elif word_score < 0:
            neg_hits.append(token)
    return compound, pos_hits, neg_hits


def analyze(text: str) -> dict:
    """{'label', 'score', 'reasons'} を返す。reasonsは判定根拠となった単語(最大4件)。"""
    if not text:
        return {"label": "neutral", "score": 0.0, "reasons": []}

    if _JAPANESE_RE.search(text):
        score, pos_hits, neg_hits = _score_japanese(text)
    else:
        score, pos_hits, neg_hits = _score_english(text)

    if score >= 0.15:
        label = "positive"
        reasons = pos_hits
    elif score <= -0.15:
        label = "negative"
        reasons = neg_hits
    else:
        label = "neutral"
        reasons = []

    # 重複を保ったまま順序を維持し、件数を絞る
    seen: set[str] = set()
    deduped: list[str] = []
    for r in reasons:
        key = r.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    return {"label": label, "score": round(score, 3), "reasons": deduped[:_MAX_REASONS]}


def attach_sentiment(items: list[dict]) -> list[dict]:
    for item in items:
        item["sentiment"] = analyze(item.get("title", ""))
    return items
