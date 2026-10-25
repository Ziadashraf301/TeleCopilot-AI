from telecopilot.core.observability import ObservabilityTracer


def test_token_estimation_and_cost_calculation():
    """Verify ObservabilityTracer accurately calculates tokens and USD costs."""
    sample_text = "This is a customer service query about router troubleshooting."
    tokens = ObservabilityTracer.estimate_tokens(sample_text)
    assert tokens > 0

    # Calculate cost for 1,000 prompt tokens and 500 completion tokens on gemini-1.5-flash
    cost = ObservabilityTracer.calculate_cost("gemini-1.5-flash", prompt_tokens=1000, completion_tokens=500)
    expected_cost = round((1000 / 1e6 * 0.075) + (500 / 1e6 * 0.30), 6)
    assert cost == expected_cost
    assert cost > 0.0


def test_observability_log_generation():
    """Verify log_generation returns token and cost dictionary."""
    metrics = ObservabilityTracer.log_generation(
        trace=None,
        name="test_llm_call",
        input_data={"prompt": "test query"},
        output_data={"reply": "test reply"},
        model="gemini-1.5-flash",
        latency=0.45,
        prompt_tokens=120,
        completion_tokens=80,
    )

    assert metrics["prompt_tokens"] == 120
    assert metrics["completion_tokens"] == 80
    assert metrics["total_tokens"] == 200
    assert metrics["estimated_cost_usd"] > 0.0
