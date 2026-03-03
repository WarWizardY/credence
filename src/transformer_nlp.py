from __future__ import annotations

from typing import List, Dict, Any

try:
    from transformers import pipeline  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pipeline = None  # type: ignore


_sentiment_pipe = None


def _get_sentiment_pipeline():
    global _sentiment_pipe
    if _sentiment_pipe is not None:
        return _sentiment_pipe
    if pipeline is None:
        return None
    try:
        # FinBERT sentiment as a reasonable default; falls back silently if unavailable
        _sentiment_pipe = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    except Exception:
        _sentiment_pipe = None
    return _sentiment_pipe


def analyze_texts_with_transformer(texts: List[str]) -> Dict[str, Any]:
    """
    Use a transformer (FinBERT or fallback) to compute an aggregate sentiment
    score as a proxy for risk tone. This is optional and degrades gracefully
    if transformers are not available.
    """
    pipe = _get_sentiment_pipeline()
    if pipe is None or not texts:
        return {}

    results = pipe(texts[:20])  # cap for speed
    pos = neg = neu = 0
    for r in results:
        label = r.get("label", "").upper()
        if "NEG" in label:
            neg += 1
        elif "POS" in label:
            pos += 1
        else:
            neu += 1

    total = max(1, pos + neg + neu)
    return {
        "transformer_pos_share": pos / total,
        "transformer_neg_share": neg / total,
        "transformer_neu_share": neu / total,
    }

