from src.rag_engine.router import QuestionRouter


def test_numeric_route():
    plan = QuestionRouter().route("What were total assets in 2024?")
    assert plan.query_type == "numeric"
    assert plan.metric == "total_assets"
    assert plan.years == [2024]


def test_comparison_route():
    plan = QuestionRouter().route("Compare net profit in 2023 and 2024")
    assert plan.query_type == "comparison"
    assert plan.metric == "net_profit"
    assert plan.years == [2023, 2024]
