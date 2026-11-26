"""Slack Bolt app for testing Ryanair news alerts.

Run this app in Socket Mode so Slack can deliver events without a public URL.
"""

from __future__ import annotations

import os
from typing import Any

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


NEWS_URL = "https://example.com/ryanair-airport-strike"


def build_news_alert_blocks() -> list[dict[str, Any]]:
    """Return the hardcoded news alert card used by the Slack test app."""

    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Ryanair News Alert"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Ryanair cancels flights after an airport strike*\n\n"
                    "A fictional airport strike has disrupted Ryanair services, "
                    "with cancellations expected to affect today’s schedule."
                ),
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "*Threat level*\nMedium"},
                {"type": "mrkdwn", "text": "*Source*\nFictional test story"},
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "draft_pr_response",
                    "text": {"type": "plain_text", "text": "Draft PR Response"},
                    "style": "primary",
                    "value": "ryanair-airport-strike",
                },
                {
                    "type": "button",
                    "action_id": "open_news_article",
                    "text": {"type": "plain_text", "text": "Read article"},
                    "url": NEWS_URL,
                    "value": NEWS_URL,
                },
            ],
        },
    ]


# Bolt validates the token during App construction. A placeholder with
# verification disabled keeps pure block-builder tests importable; the
# executable still requires real credentials below before starting Socket Mode.
bot_token = os.environ.get("SLACK_BOT_TOKEN")
app = App(
    token=bot_token or "xoxb-test-token",
    token_verification_enabled=bool(bot_token),
)


@app.event("app_mention")
def handle_app_mention(event: dict[str, Any], say: Any) -> None:
    """Reply to a mention with the sample alert card."""

    say(
        text="Here is the latest Ryanair news alert.",
        blocks=build_news_alert_blocks(),
        thread_ts=event.get("ts"),
    )


@app.action("draft_pr_response")
def handle_draft_pr_response(ack: Any, body: dict[str, Any], say: Any) -> None:
    """Acknowledge the button and post a placeholder draft in the thread."""

    ack()
    message = body.get("message", {})
    container = body.get("container", {})
    thread_ts = container.get("thread_ts") or message.get("ts")

    say(
        text=(
            "*Draft PR response (placeholder)*\n\n"
            "We are aware of reports that an airport strike has affected some "
            "Ryanair flights. Our teams are working to support impacted customers "
            "and will share further updates as more information becomes available.\n\n"
            "_Citation: fictional test story — https://example.com/ryanair-airport-strike_"
        ),
        thread_ts=thread_ts,
    )


if __name__ == "__main__":
    if not os.environ.get("SLACK_BOT_TOKEN"):
        raise RuntimeError("SLACK_BOT_TOKEN is required to run in Socket Mode")

    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not app_token:
        raise RuntimeError("SLACK_APP_TOKEN is required to run in Socket Mode")

    SocketModeHandler(app, app_token).start()
