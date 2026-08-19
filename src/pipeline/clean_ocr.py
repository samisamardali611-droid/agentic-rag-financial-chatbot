"""Clean OCR text files from data/ocr into data/clean."""
import re
from pathlib import Path

from src.config import DATA_DIR

OCR_DIR = DATA_DIR / "ocr"
CLEAN_DIR = DATA_DIR / "clean"

PAGE_NUMBER_RE = re.compile(r"^\s*-\s*\d+\s*-\s*$")
FOOTER_RE = re.compile(
    r"The accompanying notes .* integral part .* read with them",
    re.IGNORECASE,
)


def clean_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if PAGE_NUMBER_RE.match(stripped):
            continue
        if FOOTER_RE.search(stripped):
            continue
        if "deloitte" in stripped.lower() and len(stripped) < 80:
            continue
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"_{2,}", " ", cleaned)
    return cleaned.strip() + "\n"


def main():
    if not OCR_DIR.exists():
        raise FileNotFoundError(f"OCR directory not found: {OCR_DIR}")
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    inputs = sorted(OCR_DIR.glob("*_ocr.txt"))
    if not inputs:
        raise FileNotFoundError(f"No *_ocr.txt files found in {OCR_DIR}")

    for input_file in inputs:
        output_file = CLEAN_DIR / input_file.name.replace("_ocr", "_clean")
        output_file.write_text(
            clean_text(input_file.read_text(encoding="utf-8", errors="ignore")),
            encoding="utf-8",
        )
        print(f"Cleaned {input_file.name} -> {output_file.name}")


if __name__ == "__main__":
    main()
