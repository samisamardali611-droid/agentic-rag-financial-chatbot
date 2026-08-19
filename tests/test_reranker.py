from src.rag_engine.reranker import rerank_chunks


def test_keyword_reranking_prefers_metric_match():
    chunks = [
        {"text": "general governance disclosure", "score": 0.8},
        {"text": "total assets 123,456", "score": 0.5},
    ]
    ranked = rerank_chunks(chunks, "What are total assets?", top_n=2)
    assert ranked[0]["text"].startswith("total assets")
