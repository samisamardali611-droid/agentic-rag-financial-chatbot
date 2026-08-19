from src.rag_engine.verification import verify_numeric_from_context


def test_numeric_verification():
    context = "Total assets 12,345,678 as reported for the period."
    result = verify_numeric_from_context("total assets", context)
    assert result["status"] == "verified"
    assert result["value"] == "12345678"
