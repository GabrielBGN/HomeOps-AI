
"""Tests for HomeOps-AI privacy instructions."""

from homeops.ai_analyst import SYSTEM_PROMPT


def test_ai_prompt_preserves_network_privacy():
    prompt = SYSTEM_PROMPT.lower()

    required_terms = (
        "privacy",
        "ip addresses",
        "mac addresses",
        "hostnames",
        "vendor names",
        "alert messages",
        "anonymized identifiers",
        "local-only investigation",
    )

    for term in required_terms:
        assert term in prompt, (
            f"Missing privacy instruction: {term}"
        )

    assert "never recommend exposing or transmitting" in prompt
    assert "do not recommend weakening" in prompt
