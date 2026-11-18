"""HTTP integration tests for the AI dashboard endpoint."""

import pytest

from contextlib import contextmanager
from http.client import HTTPConnection
from threading import Event, Thread
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlencode

from homeops.dashboard import DashboardHandler, AI_CSRF_TOKEN


@pytest.fixture(autouse=True)
def reset_ai_state():
    """Isolate AI report and cooldown state between tests."""
    from homeops import dashboard

    with dashboard.AI_REPORT_LOCK:
        dashboard.AI_LAST_SUCCESS = None
        dashboard.AI_LATEST_REPORT = None

    yield

    with dashboard.AI_REPORT_LOCK:
        dashboard.AI_LAST_SUCCESS = None
        dashboard.AI_LATEST_REPORT = None


@contextmanager
def running_server():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        DashboardHandler,
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def post_analysis(port, token=AI_CSRF_TOKEN,
                  origin="http://127.0.0.1:8080"):
    body = urlencode({"csrf_token": token})
    connection = HTTPConnection("127.0.0.1", port, timeout=5)

    try:
        connection.request(
            "POST",
            "/ai/analyze",
            body=body,
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": origin,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def sample_report():
    return {
        "overall_health": "HEALTHY",
        "severity": "LOW",
        "executive_summary": "Network operating normally.",
        "findings": ["All monitored devices are online."],
        "recommendations": ["Continue monitoring."],
        "limitations": ["Limited observation window."],
    }


def test_authorized_request_returns_report():
    with patch(
        "homeops.dashboard.collect_network_health_summary",
        return_value={"synthetic": True},
    ), patch(
        "homeops.dashboard.analyze_network_health",
        return_value=sample_report(),
    ) as analyze:
        with running_server() as port:
            status, body = post_analysis(port)

    assert status == 303
    assert body == ""
    analyze.assert_called_once_with({"synthetic": True})


def test_invalid_csrf_rejected_before_api_call():
    with patch(
        "homeops.dashboard.analyze_network_health"
    ) as analyze:
        with running_server() as port:
            status, _ = post_analysis(port, token="invalid")

    assert status == 403
    analyze.assert_not_called()


def test_external_origin_rejected_before_api_call():
    with patch(
        "homeops.dashboard.analyze_network_health"
    ) as analyze:
        with running_server() as port:
            status, _ = post_analysis(
                port, origin="https://example.com"
            )

    assert status == 403
    analyze.assert_not_called()


def test_overlapping_analysis_rejected():
    started = Event()
    release = Event()
    first_result = {}

    def slow_analysis(summary):
        started.set()
        if not release.wait(timeout=5):
            raise RuntimeError("Timed out waiting for test")
        return sample_report()

    with patch(
        "homeops.dashboard.collect_network_health_summary",
        return_value={"synthetic": True},
    ), patch(
        "homeops.dashboard.analyze_network_health",
        side_effect=slow_analysis,
    ) as analyze:
        with running_server() as port:
            def first_request():
                first_result["response"] = post_analysis(port)

            thread = Thread(target=first_request, daemon=True)
            thread.start()

            try:
                assert started.wait(timeout=3)
                status, _ = post_analysis(port)
                assert status == 409
            finally:
                release.set()
                thread.join(timeout=5)

    assert first_result["response"][0] == 303
    assert analyze.call_count == 1


def test_successful_analysis_is_saved():
    from homeops.dashboard import get_latest_ai_report

    report = sample_report()

    with patch(
        "homeops.dashboard.collect_network_health_summary",
        return_value={"synthetic": True},
    ), patch(
        "homeops.dashboard.analyze_network_health",
        return_value=report,
    ):
        with running_server() as port:
            status, _ = post_analysis(port)

    assert status == 303
    assert get_latest_ai_report() == report


def test_dashboard_refresh_does_not_call_openai():
    from homeops.dashboard import build_dashboard

    with patch(
        "homeops.dashboard.get_all_devices",
        return_value=[],
    ), patch(
        "homeops.dashboard.get_recent_scan_history",
        return_value=[],
    ), patch(
        "homeops.dashboard.get_recent_alerts",
        return_value=[],
    ), patch(
        "homeops.dashboard.get_unread_alert_count",
        return_value=0,
    ), patch(
        "homeops.dashboard.get_device_availability",
        return_value=[],
    ), patch(
        "homeops.dashboard.analyze_network_health",
    ) as analyze:
        html = build_dashboard()

    assert "Generate AI Analysis" in html
    assert 'action="/ai/analyze"' in html
    analyze.assert_not_called()


def test_cooldown_blocks_repeat_analysis():
    from homeops import dashboard

    with patch.object(
        dashboard, "AI_LAST_SUCCESS", None
    ), patch(
        "homeops.dashboard.collect_network_health_summary",
        return_value={"synthetic": True},
    ), patch(
        "homeops.dashboard.analyze_network_health",
        return_value=sample_report(),
    ) as analyze:
        with running_server() as port:
            first_status, _ = post_analysis(port)
            second_status, _ = post_analysis(port)

    assert first_status == 303
    assert second_status == 429
    assert analyze.call_count == 1


def test_expired_cooldown_allows_analysis():
    from homeops import dashboard

    with patch.object(
        dashboard, "AI_LAST_SUCCESS", -1000000
    ), patch(
        "homeops.dashboard.collect_network_health_summary",
        return_value={"synthetic": True},
    ), patch(
        "homeops.dashboard.analyze_network_health",
        return_value=sample_report(),
    ) as analyze:
        with running_server() as port:
            status, _ = post_analysis(port)

    assert status == 303
    analyze.assert_called_once()


def test_invalid_token_does_not_collect_network_data():
    with patch(
        "homeops.dashboard.collect_network_health_summary"
    ) as collect, patch(
        "homeops.dashboard.analyze_network_health"
    ) as analyze:
        with running_server() as port:
            status, _ = post_analysis(
                port, token="unauthorized-token"
            )

    assert status == 403
    collect.assert_not_called()
    analyze.assert_not_called()


def test_api_failure_does_not_expose_sensitive_details():
    secret = "sk-example-sensitive-test-key"
    private_ip = "192.168.1.123"

    with patch(
        "homeops.dashboard.collect_network_health_summary",
        return_value={"synthetic": True},
    ), patch(
        "homeops.dashboard.analyze_network_health",
        side_effect=RuntimeError(
            f"Failure involving {secret} and {private_ip}"
        ),
    ):
        with running_server() as port:
            status, body = post_analysis(port)

    assert status == 503
    assert secret not in body
    assert private_ip not in body


def test_successful_response_redirects_to_dashboard():
    with patch(
        "homeops.dashboard.collect_network_health_summary",
        return_value={"synthetic": True},
    ), patch(
        "homeops.dashboard.analyze_network_health",
        return_value=sample_report(),
    ):
        with running_server() as port:
            status, body = post_analysis(port)

    assert status == 303
    assert body == ""


def test_dashboard_refresh_does_not_collect_ai_summary():
    from homeops.dashboard import build_dashboard

    with patch(
        "homeops.dashboard.get_all_devices",
        return_value=[],
    ), patch(
        "homeops.dashboard.get_recent_scan_history",
        return_value=[],
    ), patch(
        "homeops.dashboard.get_recent_alerts",
        return_value=[],
    ), patch(
        "homeops.dashboard.get_unread_alert_count",
        return_value=0,
    ), patch(
        "homeops.dashboard.get_device_availability",
        return_value=[],
    ), patch(
        "homeops.dashboard.collect_network_health_summary"
    ) as collect:
        html = build_dashboard()

    assert "Generate AI Analysis" in html
    collect.assert_not_called()
