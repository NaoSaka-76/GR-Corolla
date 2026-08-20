"""記事タイトルからポジティブ/ネガティブを推定する軽量センチメント判定。

公式の感情分析APIは使わず、英語はVADER(ルールベース・オフライン)、
日本語は自動車レビュー文脈向けに手作りした極性辞書でスコアリングする。
見出し(短文)のみを対象とした簡易推定であり、精度は限定的。

ニュース記事・動画とも、本文全文や動画の内容そのものを無料で安定的に取得する手段が
ないため(Google News RSSのsummaryは見出しの複製のみ、YouTube検索結果の
descriptionSnippetもほとんどのケースで空)、見出し文が唯一の入力である。
そのため「見出し中のどれか1語だけで判定が決まってしまう」ことを避けるガードとして、
判定根拠となる単語が2つ以上見つかった場合のみポジティブ/ネガティブを確定し、
1語以下しか見つからない場合は中立として扱う。
"""

from __future__ import annotations

import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

# 自動車/モータースポーツ文脈で一般英語辞書とは意味・強さが異なる語を補正する
# (例: "drag race"の"drag"は「退屈」ではなくモータースポーツ用語。
#  "teaser"は新型車の予告カットなど中立〜好意的な文脈で使われることが多い。
#  "recall"はVADER標準辞書に存在しないが、自動車分野では強いネガティブ語)
_LEXICON_OVERRIDES = {
    "drag": 0.0,
    "teaser": 0.0,
    "recall": -2.0,
    "recalls": -2.0,
    "recalled": -2.0,
}
_analyzer.lexicon.update(_LEXICON_OVERRIDES)

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
_MIN_EVIDENCE_WORDS = 2  # これ未満(0〜1語)の場合は中立扱いにする


def _dedupe(words: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for w in words:
        key = w.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(w)
    return out


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
        if not word_score:
            continue
        if word_score > 0:
            pos_hits.append(token)
        elif word_score < 0:
            neg_hits.append(token)
    return compound, _dedupe(pos_hits), _dedupe(neg_hits)


def analyze(text: str) -> dict:
    """{'label', 'score', 'reasons'} を返す。

    英語(VADER)は一般辞書のため、"drag race"の"drag"のように文脈と無関係な語が
    紛れ込みやすい。判定根拠となる単語が2つ未満の場合は、1語だけで結論が
    引っ張られるのを避けるため中立(neutral)として扱う。
    日本語辞書はこのダッシュボード向けに自動車文脈のみを想定して手作りしているため
    多義語が混ざりにくく、1語のみの一致でも判定を確定する。
    """
    if not text:
        return {"label": "neutral", "score": 0.0, "reasons": []}

    is_japanese = bool(_JAPANESE_RE.search(text))
    if is_japanese:
        score, pos_hits, neg_hits = _score_japanese(text)
    else:
        score, pos_hits, neg_hits = _score_english(text)

    evidence_count = len(pos_hits) + len(neg_hits)
    if not is_japanese and evidence_count < _MIN_EVIDENCE_WORDS:
        return {"label": "neutral", "score": round(score, 3), "reasons": []}

    if score >= 0.15:
        label = "positive"
        reasons = pos_hits
    elif score <= -0.15:
        label = "negative"
        reasons = neg_hits
    else:
        label = "neutral"
        reasons = []

    return {"label": label, "score": round(score, 3), "reasons": reasons[:_MAX_REASONS]}


def attach_sentiment(items: list[dict]) -> list[dict]:
    for item in items:
        item["sentiment"] = analyze(item.get("title", ""))
    return items
