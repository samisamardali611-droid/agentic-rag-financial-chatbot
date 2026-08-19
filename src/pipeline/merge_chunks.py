"""Merge per-year chunk files into data/chunks/all_chunks.json."""
import json

from src.config import ALL_CHUNKS_FILE, DATA_DIR

CHUNKS_DIR = DATA_DIR / "chunks"


def main():
    inputs = [p for p in sorted(CHUNKS_DIR.glob("*_chunks.json")) if p.name != "all_chunks.json"]
    if not inputs:
        raise FileNotFoundError(f"No per-year chunk files found in {CHUNKS_DIR}")

    merged = []
    for input_file in inputs:
        items = json.loads(input_file.read_text(encoding="utf-8"))
        merged.extend(items)
        print(f"Loaded {len(items)} chunks from {input_file.name}")

    ALL_CHUNKS_FILE.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(merged)} total chunks -> {ALL_CHUNKS_FILE}")


if __name__ == "__main__":
    main()
