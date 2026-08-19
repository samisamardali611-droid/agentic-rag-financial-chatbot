"""Structured triage agent for financial-statement questions."""
from typing import Literal, Optional

from agents import Agent
from pydantic import BaseModel

from src.config import LLM_MODEL


class TriagePlan(BaseModel):
    query_type: Literal["numeric", "descriptive", "comparison"]
    metric_text: Optional[str] = None
    years: Optional[list[int]] = None
    needs_verification: bool = False


triage_agent = Agent(
    name="QueryTriageAgent",
    model=LLM_MODEL,
    output_type=TriagePlan,
    instructions=(
        "Classify the user's financial-statement question as numeric, descriptive, or comparison. "
        "Extract any four-digit years. For numeric/comparison questions, set metric_text to a short "
        "financial measure such as 'total assets', 'net profit', or 'earnings per share' and set "
        "needs_verification=true. For descriptive questions, metric_text should be null and "
        "needs_verification=false. Do not answer the question itself."
    ),
)
