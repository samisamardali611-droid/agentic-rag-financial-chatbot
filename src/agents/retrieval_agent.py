"""Retrieval agent and hybrid retrieval tool."""
import json

import faiss
import numpy as np
from agents import Agent, ModelSettings
from agents.decorators import tool
from openai import OpenAI

from src.config import EMBEDDING_MODEL, FAISS_INDEX_FILE, FAISS_METADATA_FILE, LLM_MODEL
from src.rag_engine.reranker import rerank_chunks

TOP_K_WIDE = 80
TOP_K_FINAL = 12
MAX_CHARS_PER_CHUNK = 1200


def get_openai_client() -> OpenAI:
    return OpenAI()


def embed_text(text: str) -> np.ndarray:
    client = get_openai_client()
    emb = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return np.array(emb.data[0].embedding, dtype="float32").reshape(1, -1)


def load_index():
    index = faiss.read_index(str(FAISS_INDEX_FILE))
    metadata = json.loads(FAISS_METADATA_FILE.read_text(encoding="utf-8"))
    return index, metadata


@tool(name_override="retrieve_relevant_chunks")
def retrieve_relevant_chunks(question: str) -> str:
    """Retrieve and rerank evidence for a financial-statement question."""
    index, metadata = load_index()
    q_emb = embed_text(question)
    search_k = min(TOP_K_WIDE, index.ntotal)
    distances, indices = index.search(q_emb, search_k)

    chunks = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        item = dict(metadata[idx])
        item["score"] = 1 / (1 + float(dist))
        chunks.append(item)

    chunks = rerank_chunks(chunks, question, top_n=TOP_K_FINAL)
    return "\n\n".join(
        f"[{c.get('year')} | {c.get('section_title')}]\n"
        f"{(c.get('text') or '')[:MAX_CHARS_PER_CHUNK]}"
        for c in chunks
    )


retrieval_agent = Agent(
    name="RetrievalAgent",
    model=LLM_MODEL,
    instructions="Retrieve evidence for the user's question using the available retrieval tool.",
    tools=[retrieve_relevant_chunks],
    model_settings=ModelSettings(tool_choice="retrieve_relevant_chunks"),
    tool_use_behavior="stop_on_first_tool",
)
