"""Shared configuration for the portfolio RAG application."""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = PROJECT_ROOT / "src" / "artifacts"
DATA_DIR = PROJECT_ROOT / "data"

FAISS_INDEX_FILE = ARTIFACTS_DIR / "faiss.index"
FAISS_METADATA_FILE = ARTIFACTS_DIR / "faiss_metadata.json"
ALL_CHUNKS_FILE = DATA_DIR / "chunks" / "all_chunks.json"

EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4.1-mini"
