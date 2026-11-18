"""Security tests for the AI dashboard endpoint."""

from homeops.dashboard import (
    AI_CSRF_TOKEN,
    valid_ai_request,
)


def test_valid_local_request():
    assert valid_ai_request(
        AI_CSRF_TOKEN,
        "http://127.0.0.1:8080",
    )


def test_invalid_csrf_token():
    assert not valid_ai_request(
        "invalid-token",
        "http://127.0.0.1:8080",
    )


def test_external_origin_rejected():
    assert not valid_ai_request(
        AI_CSRF_TOKEN,
        "https://example.com",
    )


def test_missing_origin_rejected():
    assert not valid_ai_request(
        AI_CSRF_TOKEN,
        None,
    )


def test_missing_token_rejected():
    assert not valid_ai_request(
        None,
        "http://127.0.0.1:8080",
    )
