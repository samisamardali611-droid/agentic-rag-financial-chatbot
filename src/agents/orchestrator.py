"""End-to-end orchestration for the agentic RAG workflow."""
from agents import Runner

from src.agents.retrieval_agent import retrieval_agent
from src.agents.table_extraction_agent import extract_numeric_from_tables_py
from src.agents.triage_agent import TriagePlan, triage_agent
from src.agents.verification_agent import verify_numeric_from_context_py
from src.rag_engine import rag_engine
from src.rag_engine.router import QuestionRouter


def normalize_metric_text(metric: str) -> str:
    if not metric:
        return ""
    return " ".join(metric.lower().replace("_", " ").split())


async def run_orchestrator(question: str) -> str:
    triage_result = await Runner.run(triage_agent, question)
    plan = triage_result.final_output

    if isinstance(plan, TriagePlan):
        query_type = plan.query_type
        metric_text = normalize_metric_text(plan.metric_text or "")
        years = plan.years or []
    else:
        fallback = QuestionRouter().route(question)
        query_type = fallback.query_type
        metric_text = normalize_metric_text(fallback.metric or "")
        years = fallback.years or []

    retrieval_result = await Runner.run(retrieval_agent, question)
    context_text = str(retrieval_result.final_output or "")

    if query_type == "numeric" and metric_text:
        verified = verify_numeric_from_context_py(metric_text, context_text)
        if verified.get("status") == "verified":
            answer = f"The {metric_text} is {verified.get('value')}."
            if verified.get("evidence"):
                answer += f"\n\nEvidence: {verified.get('evidence')}"
            return rag_engine.format_answer(question, answer, [], "High")

        if years:
            table_result = extract_numeric_from_tables_py(metric_text, int(years[0]), context_text)
            if table_result.get("status") == "verified_from_table":
                answer = f"The {metric_text} in {years[0]} is {table_result.get('value')}."
                if table_result.get("evidence"):
                    answer += f"\n\nEvidence: {table_result.get('evidence')}"
                return rag_engine.format_answer(question, answer, [], "Medium")

    # The deterministic engine handles comparisons and provides a grounded fallback.
    return rag_engine.answer_question(question)
