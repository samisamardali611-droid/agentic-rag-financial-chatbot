"""Deterministic query routing for common financial questions."""
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class QueryPlan:
    query_type: str  # numeric | descriptive | comparison
    metric: Optional[str] = None
    years: Optional[List[int]] = None
    needs_verification: bool = False


class QuestionRouter:
    METRICS = {
        "total assets": "total_assets",
        "assets": "total_assets",
        "total liabilities": "total_liabilities",
        "liabilities": "total_liabilities",
        "net profit": "net_profit",
        "profit": "net_profit",
        "loss": "net_profit",
        "total income": "total_income",
        "income": "total_income",
        "revenue": "total_income",
        "earnings per share": "earnings_per_share",
        "eps": "earnings_per_share",
    }

    def route(self, question: str) -> QueryPlan:
        query = question.lower()
        years = sorted({int(year) for year in re.findall(r"(20\d{2})", query)}) or None

        for phrase, metric in self.METRICS.items():
            if phrase in query:
                if years and len(years) > 1:
                    return QueryPlan("comparison", metric, years, True)
                return QueryPlan("numeric", metric, years, True)

        return QueryPlan("descriptive", years=years)
