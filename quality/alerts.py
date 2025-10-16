"""Slack alerting for data quality failures."""

import json
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog

from config import get_settings

logger = structlog.get_logger(__name__)


def send_quality_alert(validation_result: dict[str, Any]) -> bool:
    """Send Slack alert when data quality checks fail.

    Args:
        validation_result: Output from WeatherQualityCheckpoint.validate_batch()

    Returns:
        True if alert sent successfully
    """
    settings = get_settings()
    webhook_url = settings.slack.webhook_url

    if not webhook_url:
        logger.warning("slack_webhook_not_configured")
        return False

    stats = validation_result.get("statistics", {})
    failed = validation_result.get("failed_expectations", [])

    # Build failure details
    failure_lines = []
    for f in failed[:5]:  # Limit to 5 failures in alert
        failure_lines.append(
            f"• `{f['expectation_type']}` on `{f.get('kwargs', {}).get('column', 'table')}` "
            f"— observed: `{f.get('observed_value', 'N/A')}`"
        )

    failure_text = "\n".join(failure_lines)
    if len(failed) > 5:
        failure_text += f"\n_... and {len(failed) - 5} more failures_"

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔴 Weather Pipeline — Data Quality FAILED",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total Checks:*\n{stats.get('evaluated_expectations', 0)}"},
                    {"type": "mrkdwn", "text": f"*Failed:*\n{stats.get('unsuccessful_expectations', 0)}"},
                    {"type": "mrkdwn", "text": f"*Success Rate:*\n{stats.get('success_percent', 0):.1f}%"},
                    {"type": "mrkdwn", "text": f"*Timestamp:*\n{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Failed Expectations:*\n{failure_text}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠️ *Pipeline has been halted.* dbt transformations were NOT run. Investigate and re-trigger manually.",
                },
            },
        ],
    }

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("slack_alert_sent")
        return True
    except Exception as e:
        logger.error("slack_alert_failed", error=str(e))
        return False


def send_success_notification() -> bool:
    """Send brief success notification."""
    settings = get_settings()
    webhook_url = settings.slack.webhook_url

    if not webhook_url:
        return False

    payload = {
        "text": f"🟢 Weather Pipeline — All quality checks passed | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    }

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception:
        return False
