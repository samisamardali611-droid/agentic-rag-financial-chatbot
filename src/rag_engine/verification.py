"""Deterministic numeric verification helpers."""
import re
from typing import Any, Dict


def verify_numeric_from_context(metric_text: str, context_text: str) -> Dict[str, Any]:
    if not metric_text or not context_text:
        return {"status": "not_found", "value": None, "evidence": None}

    metric = " ".join(metric_text.lower().replace("_", " ").split())
    num_pat = r"(\(?\d{1,3}(?:[, ]\d{3})*(?:\.\d+)?\)?)"

    if "net profit" in metric or metric == "profit":
        patterns = [
            rf"(net\s+profit).*?{num_pat}",
            rf"(profit\s+for\s+the\s+year).*?{num_pat}",
            rf"(attributable\s+to\s+shareholders).*?{num_pat}",
        ]
    elif "total assets" in metric or metric == "assets":
        patterns = [rf"(total\s+assets).*?{num_pat}", rf"(assets\s+total).*?{num_pat}"]
    elif "total income" in metric or "income" in metric or "revenue" in metric:
        patterns = [rf"(total\s+income).*?{num_pat}", rf"(income).*?{num_pat}", rf"(revenue).*?{num_pat}"]
    elif "earnings per share" in metric or metric == "eps" or "per share" in metric:
        patterns = [
            rf"(earnings\s+per\s+share).*?{num_pat}",
            rf"(eps).*?{num_pat}",
            rf"(basic\s+and\s+diluted).*?{num_pat}",
        ]
    else:
        patterns = [rf"({re.escape(metric)}).*?{num_pat}"]

    for pattern in patterns:
        match = re.search(pattern, context_text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue

        raw = match.group(2) if match.lastindex and match.lastindex >= 2 else None
        if not raw:
            continue

        negative = raw.startswith("(") and raw.endswith(")")
        digits = re.sub(r"[^\d.]", "", raw)
        if not digits:
            continue

        if "per share" not in metric and "eps" not in metric:
            if len(re.sub(r"\D", "", digits)) < 6:
                continue

        value = f"-{digits}" if negative else digits
        start = max(match.start() - 120, 0)
        end = min(match.end() + 120, len(context_text))
        evidence = context_text[start:end].replace("\n", " ").strip()
        return {"status": "verified", "value": value, "evidence": evidence}

    return {"status": "not_found", "value": None, "evidence": None}
