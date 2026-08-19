"""Hybrid reranking utilities for retrieved financial-statement chunks."""
from typing import Dict, List

KEYWORD_BOOSTS = {
    "net profit": ["profit", "profit for the year", "attributable"],
    "total assets": ["total assets", "assets"],
    "total income": ["total income", "income", "revenue"],
    "earnings per share": ["earnings per share", "eps", "per share"],
}


def keyword_score(text: str, query: str) -> float:
    text_lower = text.lower()
    query_lower = query.lower()
    score = 0.0

    for word in query_lower.split():
        if word in text_lower:
            score += 0.3

    for phrase, variants in KEYWORD_BOOSTS.items():
        if phrase in query_lower:
            for variant in variants:
                if variant in text_lower:
                    score += 1.0

    return score


def rerank_chunks(chunks: List[Dict], question: str, top_n: int = 10) -> List[Dict]:
    ranked = []
    for chunk in chunks:
        item = dict(chunk)
        vector_score = float(item.get("score", 0.0))
        lexical_score = keyword_score(item.get("text", ""), question)
        item["_final_score"] = (0.7 * vector_score) + (0.3 * lexical_score)
        ranked.append(item)

    ranked.sort(key=lambda item: item["_final_score"], reverse=True)
    return ranked[:top_n]
