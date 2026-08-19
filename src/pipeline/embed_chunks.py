"""Build FAISS artifacts from the merged chunk file."""
import json

import faiss
import numpy as np
from openai import OpenAI
from tqdm import tqdm

from src.config import ALL_CHUNKS_FILE, EMBEDDING_MODEL, FAISS_INDEX_FILE, FAISS_METADATA_FILE


def main():
    if not ALL_CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Chunk file not found: {ALL_CHUNKS_FILE}")

    chunks = json.loads(ALL_CHUNKS_FILE.read_text(encoding="utf-8"))
    client = OpenAI()

    embeddings = []
    metadata = []
    for chunk in tqdm(chunks, desc="Embedding chunks"):
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=chunk["text"])
        embeddings.append(np.array(response.data[0].embedding, dtype="float32"))
        metadata.append({
            "year": chunk.get("year"),
            "section_title": chunk.get("section_title"),
            "note_number": chunk.get("note_number"),
            "text": chunk["text"],
        })

    matrix = np.vstack(embeddings)
    index = faiss.IndexFlatL2(matrix.shape[1])
    index.add(matrix)
    FAISS_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_FILE))
    FAISS_METADATA_FILE.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built {index.ntotal} vectors in {FAISS_INDEX_FILE}")


if __name__ == "__main__":
    main()
