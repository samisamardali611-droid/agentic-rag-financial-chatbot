"""Split cleaned annual-statement text into logical sections."""
import json
import re

from src.config import DATA_DIR

CLEAN_DIR = DATA_DIR / "clean"
SECTIONS_DIR = DATA_DIR / "sections"

NOTE_HEADER_RE = re.compile(r"^(\d{1,2})\.\s+(.+)$")
ALL_CAPS_RE = re.compile(r"^[A-Z][A-Z\s\-&,()]{5,}$")


def split_into_sections(text: str, year: int):
    sections = []
    current = {"year": year, "section_title": "Introduction", "note_number": None, "content": []}

    def flush():
        if current["content"]:
            sections.append({**current, "content": "\n".join(current["content"]).strip()})

    for line in text.splitlines():
        stripped = line.strip()
        note_match = NOTE_HEADER_RE.match(stripped)
        if note_match:
            flush()
            current = {
                "year": year,
                "section_title": note_match.group(2),
                "note_number": note_match.group(1),
                "content": [],
            }
            continue

        if ALL_CAPS_RE.match(stripped):
            flush()
            current = {
                "year": year,
                "section_title": stripped.title(),
                "note_number": None,
                "content": [],
            }
            continue

        current["content"].append(line)

    flush()
    return sections


def main():
    inputs = sorted(CLEAN_DIR.glob("*_clean.txt"))
    if not inputs:
        raise FileNotFoundError(f"No *_clean.txt files found in {CLEAN_DIR}")
    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)

    for input_file in inputs:
        year = int(input_file.stem.split("_")[0])
        sections = split_into_sections(input_file.read_text(encoding="utf-8", errors="ignore"), year)
        output_file = SECTIONS_DIR / f"{year}_sections.json"
        output_file.write_text(json.dumps(sections, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{year}: {len(sections)} sections -> {output_file.name}")


if __name__ == "__main__":
    main()
