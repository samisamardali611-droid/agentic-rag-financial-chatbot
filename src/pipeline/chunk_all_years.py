"""Chunk section JSON files into fixed-size word windows."""
import json

from src.config import DATA_DIR

SECTIONS_DIR = DATA_DIR / "sections"
CHUNKS_DIR = DATA_DIR / "chunks"
MIN_CHARS = 300
CHUNK_SIZE = 500


def chunk_text(text: str, chunk_size: int):
    words = text.split()
    for start in range(0, len(words), chunk_size):
        yield " ".join(words[start:start + chunk_size])


def main():
    inputs = sorted(SECTIONS_DIR.glob("*_sections.json"))
    if not inputs:
        raise FileNotFoundError(f"No *_sections.json files found in {SECTIONS_DIR}")
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    for input_file in inputs:
        year = int(input_file.stem.split("_")[0])
        sections = json.loads(input_file.read_text(encoding="utf-8"))
        chunks = []
        for section in sections:
            content = (section.get("content") or "").strip()
            if len(content) < MIN_CHARS:
                continue
            for idx, chunk in enumerate(chunk_text(content, CHUNK_SIZE)):
                chunks.append({
                    "year": year,
                    "section_title": section.get("section_title"),
                    "note_number": section.get("note_number"),
                    "chunk_index": idx,
                    "text": chunk,
                })

        output_file = CHUNKS_DIR / f"{year}_chunks.json"
        output_file.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{year}: {len(chunks)} chunks -> {output_file.name}")


if __name__ == "__main__":
    main()
