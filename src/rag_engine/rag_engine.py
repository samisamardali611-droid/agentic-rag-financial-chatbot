"""Core retrieval, routing, verification, and answer-generation utilities."""
import json
import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from openai import OpenAI

from src.config import EMBEDDING_MODEL, FAISS_INDEX_FILE, FAISS_METADATA_FILE, LLM_MODEL


from src.rag_engine.router import QueryPlan, QuestionRouter


def get_openai_client() -> OpenAI:
    """Create the client lazily so imports/tests do not require an API key."""
    return OpenAI()


def normalize_number(raw: str) -> Optional[str]:
    if not raw:
        return None
    value = raw.strip()
    negative = value.startswith("(") and value.endswith(")")
    value = re.sub(r"[^\d.]", "", value)
    if not value:
        return None
    return f"-{value}" if negative else value


def is_sane_number(value: str, min_digits: int = 6, max_digits: int = 15) -> bool:
    digits = re.sub(r"\D", "", value)
    return min_digits <= len(digits) <= max_digits


@lru_cache(maxsize=1)
def load_index():
    if not FAISS_INDEX_FILE.exists() or not FAISS_METADATA_FILE.exists():
        raise FileNotFoundError(
            "FAISS artifacts are missing. Expected files under src/artifacts/."
        )
    index = faiss.read_index(str(FAISS_INDEX_FILE))
    metadata = json.loads(FAISS_METADATA_FILE.read_text(encoding="utf-8"))
    return index, metadata


def embed_text(text: str) -> np.ndarray:
    client = get_openai_client()
    emb = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return np.array(emb.data[0].embedding, dtype="float32").reshape(1, -1)


def adaptive_top_k(plan: QueryPlan) -> int:
    if plan.query_type == "numeric":
        return 8
    if plan.query_type == "comparison":
        return 12
    return 10


def retrieve_chunks(question: str, year: Optional[int] = None, top_k: int = 8):
    index, metadata = load_index()
    q_emb = embed_text(question)

    # Retrieve more than requested when a year filter is active, then filter.
    search_k = min(max(top_k * 4, top_k), index.ntotal)
    distances, indices = index.search(q_emb, search_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        item = dict(metadata[idx])
        if year is not None and int(item.get("year")) != int(year):
            continue
        item["score"] = 1 / (1 + float(dist))
        results.append(item)
        if len(results) >= top_k:
            break
    return results


def filter_context(chunks: List[Dict], question: str):
    q_words = {w for w in re.findall(r"\w+", question.lower()) if len(w) > 2}
    filtered = [
        c for c in chunks
        if c.get("score", 0) > 0.05
        and any(word in c.get("text", "").lower() for word in q_words)
    ]
    return filtered or chunks[:3]


PATTERNS = {
    "total_assets": r"(total\s+assets)\s*[:\-]?\s*([\d,\s]+)",
    "total_liabilities": r"(total\s+liabilities)\s*[:\-]?\s*([\d,\s]+)",
    "net_profit": r"(net\s+profit).*?([\d,\s\(\)]+)",
    "total_income": r"(total\s+income).*?([\d,\s]+)",
    "earnings_per_share": r"(earnings\s+per\s+share|eps).*?([\d,.\s\(\)]+)",
}


def extract_verified_number(metric: str, chunks: List[Dict]) -> Tuple[Optional[str], Optional[List[Dict]]]:
    pattern = PATTERNS.get(metric)
    if not pattern:
        return None, None

    matches = []
    for chunk in chunks:
        match = re.search(pattern, chunk.get("text", ""), re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        value = normalize_number(match.group(2))
        if not value:
            continue
        if metric == "earnings_per_share" or is_sane_number(value):
            matches.append((value, chunk))

    if not matches:
        return None, None

    frequencies: Dict[str, int] = {}
    for value, _ in matches:
        frequencies[value] = frequencies.get(value, 0) + 1

    best = max(frequencies, key=frequencies.get)
    sources = [chunk for value, chunk in matches if value == best][:3]
    return best, sources


def llm_answer(question: str, context: List[Dict]) -> str:
    context_text = "\n\n".join(
        f"[{c.get('year')} | {c.get('section_title')}]\n{c.get('text')}"
        for c in context
    )
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial analyst assistant. Answer strictly from the supplied "
                    "evidence. If the evidence is insufficient, say so. Never invent values."
                ),
            },
            {"role": "user", "content": f"Question:\n{question}\n\nEvidence:\n{context_text}"},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


def format_answer(question: str, answer: str, sources, confidence: str) -> str:
    lines = [f"**Answer**\n\n{answer}", "", "**Sources**"]
    for source in sources or []:
        note = source.get("note_number")
        suffix = f" | Note {note}" if note else ""
        lines.append(f"- {source.get('year')} | {source.get('section_title')}{suffix}")
    if not sources:
        lines.append("- No structured source metadata available")
    lines.extend(["", f"**Confidence:** {confidence}"])
    return "\n".join(lines)


class NumericExecutor:
    def run(self, question: str, plan: QueryPlan) -> str:
        top_k = adaptive_top_k(plan)
        year = plan.years[0] if plan.years else None
        chunks = filter_context(retrieve_chunks(question, year, top_k), question)
        value, sources = extract_verified_number(plan.metric, chunks)
        if value:
            label = plan.metric.replace("_", " ")
            return format_answer(question, f"The {label} is {value}.", sources, "High")
        answer = llm_answer(question, chunks[:6]) if chunks else "No relevant evidence was found."
        return format_answer(question, answer, chunks[:3], "Medium")


class DescriptiveExecutor:
    def run(self, question: str, plan: QueryPlan) -> str:
        top_k = adaptive_top_k(plan)
        year = plan.years[0] if plan.years else None
        chunks = filter_context(retrieve_chunks(question, year, top_k), question)
        answer = llm_answer(question, chunks[:6]) if chunks else "No relevant evidence was found."
        return format_answer(question, answer, chunks[:3], "Medium")


class ComparisonExecutor:
    def run(self, question: str, plan: QueryPlan) -> str:
        results, sources = [], []
        for year in plan.years or []:
            chunks = filter_context(
                retrieve_chunks(question, year, adaptive_top_k(plan)), question
            )
            value, matched_sources = extract_verified_number(plan.metric, chunks)
            if value:
                results.append(f"{year}: {value}")
                sources.extend(matched_sources or [])

        if results:
            return format_answer(question, "; ".join(results), sources[:5], "High")

        # Fall back to grounded LLM synthesis across year-specific evidence.
        combined = []
        for year in plan.years or []:
            combined.extend(retrieve_chunks(question, year, 4))
        answer = llm_answer(question, combined[:8]) if combined else "No relevant evidence was found."
        return format_answer(question, answer, combined[:5], "Medium")


def answer_question(question: str) -> str:
    plan = QuestionRouter().route(question)
    if plan.query_type == "numeric":
        return NumericExecutor().run(question, plan)
    if plan.query_type == "comparison":
        return ComparisonExecutor().run(question, plan)
    return DescriptiveExecutor().run(question, plan)
