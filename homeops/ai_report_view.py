"""Safe HTML rendering for AI network health reports."""

from html import escape

from .ai_analyst import validate_ai_report


def render_ai_report(report):
    """Render a validated AI report as escaped HTML."""

    validate_ai_report(report)

    def render_items(items):
        if not items:
            return "<p>None reported.</p>"

        return "<ul>" + "".join(
            f"<li>{escape(item)}</li>"
            for item in items
        ) + "</ul>"

    health = escape(report["overall_health"])
    severity = escape(report["severity"])
    summary = escape(report["executive_summary"])

    return f"""
    <section class="ai-report">
        <h2>AI Network Analysis</h2>

        <p><strong>Network Health:</strong> {health}</p>
        <p><strong>Severity:</strong> {severity}</p>

        <h3>Executive Summary</h3>
        <p>{summary}</p>

        <h3>Findings</h3>
        {render_items(report["findings"])}

        <h3>Recommendations</h3>
        {render_items(report["recommendations"])}

        <h3>Limitations</h3>
        {render_items(report["limitations"])}
    </section>
    """
