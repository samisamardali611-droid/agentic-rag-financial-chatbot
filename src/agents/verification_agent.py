"""Agent wrapper around deterministic numeric verification."""
from typing import Any, Dict

from agents import Agent
from agents.decorators import tool

from src.rag_engine.verification import verify_numeric_from_context


def verify_numeric_from_context_py(metric_text: str, context_text: str) -> Dict[str, Any]:
    return verify_numeric_from_context(metric_text, context_text)


@tool(name_override="verify_numeric_from_context")
def verify_numeric_from_context_tool(metric_text: str, context_text: str) -> Dict[str, Any]:
    """Verify a numeric value deterministically from retrieved context."""
    return verify_numeric_from_context(metric_text, context_text)


verification_agent = Agent(
    name="VerificationAgent",
    instructions="Verify numeric values from supplied context and never guess.",
    tools=[verify_numeric_from_context_tool],
)
