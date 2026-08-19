"""Optional baseline: extract a few recurring financial metrics from cleaned text."""
import json
import re

from src.config import DATA_DIR

CLEAN_DIR = DATA_DIR / "clean"
OUTPUT_FILE = DATA_DIR / "financial_facts.json"


def normalize_number(value: str) -> str:
    return re.sub(r"[^\d.\-]", "", value)


def extract_value(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return normalize_number(match.group(1))
    return None


def extract_year_facts(input_file):
    year = input_file.stem.split("_")[0]
    text = input_file.read_text(encoding="utf-8", errors="ignore")
    return {
        "year": year,
        "total_assets": extract_value([r"TOTAL\s+ASSETS\s+([\d\s.\-,]+)"], text),
        "total_liabilities": extract_value([r"TOTAL\s+LIABILITIES\s+([\d\s.\-,]+)"], text),
        "net_profit": extract_value([r"Net Profit(?:\s*\(Loss\))?\s+([\d\s.\-,()]+)"], text),
        "total_income": extract_value([r"Total Income\s+([\d\s.\-,]+)"], text),
    }


def main():
    inputs = sorted(CLEAN_DIR.glob("*_clean.txt"))
    if not inputs:
        raise FileNotFoundError(f"No cleaned text found in {CLEAN_DIR}")
    facts = {item["year"]: item for item in map(extract_year_facts, inputs)}
    OUTPUT_FILE.write_text(json.dumps(facts, indent=2), encoding="utf-8")
    print(f"Saved baseline facts -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
