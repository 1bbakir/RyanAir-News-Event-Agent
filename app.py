"""Slack Bolt app for testing Ryanair news alerts with Supabase persistence."""

from __future__ import annotations

import os
from typing import Any

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from database import NewsEventRepository, create_supabase_client


NEWS_URL = "https://example.com/ryanair-airport-strike"
PLACEHOLDER_DRAFT = (
    "We are aware of reports that an airport strike has affected some Ryanair "
    "flights. Our teams are working to support impacted customers and will share "
    "further updates as more information becomes available."
)

SAMPLE_NEWS_EVENT: dict[str, Any] = {
    "title": "Ryanair cancels flights after an airport strike",
    "summary": (
        "A fictional airport strike has disrupted Ryanair services, with "
        "cancellations expected to affect today's schedule."
    ),
    "article_url": NEWS_URL,
    "source_name": "Fictional test story",
    "company": "Ryanair",
    "threat_level": "medium",
    "threat_reason": "Flight cancellations may affect customers and reputation.",
}


def get_repository() -> NewsEventRepository:
    """Create the repository used by a live Slack event."""

    return NewsEventRepository(create_supabase_client())


def build_news_alert_blocks(event_id: str) -> list[dict[str, Any]]:
    """Build the Slack alert card, carrying the Supabase event ID."""

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
                    "with cancellations expected to affect today's schedule."
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
                    "value": event_id,
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
# verification disabled keeps unit tests importable without Slack credentials.
bot_token = os.environ.get("SLACK_BOT_TOKEN")
app = App(
    token=bot_token or "xoxb-test-token",
    token_verification_enabled=bool(bot_token),
)


@app.event("app_mention")
def handle_app_mention(event: dict[str, Any], say: Any) -> None:
    """Persist and post the sample news event when the bot is mentioned."""

    repository = get_repository()
    news_event = repository.create_news_event(SAMPLE_NEWS_EVENT)
    event_id = str(news_event["id"])

    response = say(
        text="Here is the latest Ryanair news alert.",
        blocks=build_news_alert_blocks(event_id),
        thread_ts=event.get("ts"),
    )
    message_ts = response.get("ts") if response else None
    repository.attach_slack_message(
        event_id,
        channel_id=str(event["channel"]),
        message_ts=message_ts,
    )


@app.action("draft_pr_response")
def handle_draft_pr_response(ack: Any, body: dict[str, Any], say: Any) -> None:
    """Load the event, save a placeholder draft, and reply in its thread."""

    ack()
    repository = get_repository()
    action = body.get("actions", [{}])[0]
    event_id = str(action.get("value", ""))
    if not event_id:
        raise ValueError("Draft button payload did not include a news event ID")

    news_event = repository.get_news_event(event_id)
    citation = str(news_event["article_url"])
    draft = news_event.get("pr_draft") or PLACEHOLDER_DRAFT
    repository.save_pr_draft(event_id, draft, citation)

    message = body.get("message", {})
    container = body.get("container", {})
    thread_ts = container.get("thread_ts") or message.get("ts")
    say(
        text=(
            f"*Draft PR response (placeholder)*\n\n{draft}\n\n"
            f"_Citation: {citation}_"
        ),
        thread_ts=thread_ts,
    )


if __name__ == "__main__":
    if not os.environ.get("SLACK_BOT_TOKEN"):
        raise RuntimeError("SLACK_BOT_TOKEN is required to run in Socket Mode")
    if not os.environ.get("SLACK_APP_TOKEN"):
        raise RuntimeError("SLACK_APP_TOKEN is required to run in Socket Mode")
    if not os.environ.get("SUPABASE_URL"):
        raise RuntimeError("SUPABASE_URL is required to run the backend")
    if not os.environ.get("SUPABASE_SECRET_KEY"):
        raise RuntimeError("SUPABASE_SECRET_KEY is required to run the backend")

    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
