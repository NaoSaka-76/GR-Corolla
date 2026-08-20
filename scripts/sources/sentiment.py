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


def _score_japanese(text: str) -> float:
    pos = sum(text.count(w) for w in _POSITIVE_JP)
    neg = sum(text.count(w) for w in _NEGATIVE_JP)
    if pos == 0 and neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def analyze(text: str) -> dict:
    """{'label': 'positive'|'negative'|'neutral', 'score': -1.0〜1.0} を返す。"""
    if not text:
        return {"label": "neutral", "score": 0.0}

    if _JAPANESE_RE.search(text):
        score = _score_japanese(text)
    else:
        score = _analyzer.polarity_scores(text)["compound"]

    if score >= 0.15:
        label = "positive"
    elif score <= -0.15:
        label = "negative"
    else:
        label = "neutral"
    return {"label": label, "score": round(score, 3)}


def attach_sentiment(items: list[dict]) -> list[dict]:
    for item in items:
        item["sentiment"] = analyze(item.get("title", ""))
    return items
