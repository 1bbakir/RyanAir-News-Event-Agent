"""Slack Block Kit builders - the 'Generative UI'.

Every function returns a dict with `text` (notification fallback) and either
`attachments` (colored card) or `blocks`. Pass it straight to chat_postMessage / chat_update:
    client.chat_postMessage(channel=ch, **alert_message(alert))

Design tip: prototype changes in https://app.slack.com/block-kit-builder first.
"""
from app.schemas import Alert, DraftResult

# Colour of the vertical bar on the left of the card
COLOR_HIGH = "#D93025"  # red
COLOR_MEDIUM = "#F29900"  # orange
COLOR_POSITIVE = "#1E8E3E"  # green
COLOR_COMPETITOR = "#7B1FA2"  # purple
COLOR_NEUTRAL = "#9AA0A6"  # grey

THREAT_LABEL = {
    "critical": ":rotating_light: Critical",
    "high": ":red_circle: High",
    "medium": ":large_orange_circle: Medium",
    "low": ":large_yellow_circle: Low",
    "none": ":white_circle: None",
}
SENTIMENT_LABEL = {
    "positive": ":chart_with_upwards_trend: Positive",
    "neutral": ":heavy_minus_sign: Neutral",
    "negative": ":chart_with_downwards_trend: Negative",
}

DRAFT_ACTION_ID = "draft_pr_response"
MAX_TEXT = 2900  # Slack section text limit is 3000 chars


def _esc(text: str) -> str:
    """Escape characters that Slack mrkdwn treats as control characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cut(text: str, limit: int = MAX_TEXT) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def alert_color(alert: Alert) -> str:
    if alert.threat_level in ("high", "critical"):
        return COLOR_HIGH
    if alert.is_competitor:
        return COLOR_COMPETITOR
    if alert.threat_level == "medium":
        return COLOR_MEDIUM
    if alert.sentiment == "positive":
        return COLOR_POSITIVE
    return COLOR_NEUTRAL


def alert_message(alert: Alert) -> dict:
    """Colour-coded news alert card with the [Draft PR Response] button."""
    tag = ":crossed_swords: Competitor" if alert.is_competitor else ":airplane: Ryanair"
    if alert.published_at:
        ts = int(alert.published_at.timestamp())
        published = f"<!date^{ts}^{{date_short_pretty}} {{time}}|{alert.published_at:%Y-%m-%d %H:%M} UTC>"
    else:
        published = "date unknown"

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*<{alert.url}|{_esc(_cut(alert.title, 250))}>*"},
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"{tag} · *{_esc(alert.company)}* · {_esc(alert.source)} · {published}"}
            ],
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Sentiment*\n{SENTIMENT_LABEL[alert.sentiment]}"},
                {"type": "mrkdwn", "text": f"*Threat level*\n{THREAT_LABEL[alert.threat_level]}"},
            ],
        },
        *(
            [{"type": "context", "elements": [{"type": "mrkdwn", "text": f"_Why:_ {_esc(_cut(alert.threat_reason, 500))}"}]}]
            if alert.threat_reason
            else []
        ),
        # Slack rejects empty text, so fall back to a placeholder
        {"type": "section", "text": {"type": "mrkdwn", "text": _esc(_cut(alert.summary)) or "_No summary yet._"}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": DRAFT_ACTION_ID,
                    "text": {"type": "plain_text", "text": ":memo: Draft PR Response", "emoji": True},
                    "style": "primary",
                    "value": alert.article_id,
                },
                {
                    "type": "button",
                    "action_id": "open_article",
                    "text": {"type": "plain_text", "text": "Open article", "emoji": True},
                    "url": alert.url,
                },
            ],
        },
    ]
    return {
        "text": f"[{alert.threat_level.upper()}] {alert.company}: {alert.title}",
        "attachments": [{"color": alert_color(alert), "blocks": blocks}],
    }


def loading_message() -> dict:
    """Shown instantly in the thread while the slow LLM call runs in the background."""
    return {
        "text": "Generating draft…",
        "blocks": [
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": ":hourglass_flowing_sand: Searching brand guidelines and drafting a response…"}
                ],
            }
        ],
    }


def draft_message(result: DraftResult, user_id: str) -> dict:
    """Final result: a draft with cited sources, a refusal, or an error."""
    if result.status == "ok" and result.draft:
        sources = ", ".join(f"`{s}`" for s in result.sources) or "_none reported_"
        return {
            "text": "PR response draft",
            "attachments": [
                {
                    "color": COLOR_POSITIVE,
                    "blocks": [
                        {"type": "section", "text": {"type": "mrkdwn", "text": ":memo: *Draft PR response*"}},
                        {"type": "section", "text": {"type": "mrkdwn", "text": _esc(_cut(result.draft))}},
                        {
                            "type": "context",
                            "elements": [
                                {"type": "mrkdwn", "text": f":books: Sources: {sources}"},
                                {"type": "mrkdwn", "text": f"Requested by <@{user_id}> · Draft only, review before publishing"},
                            ],
                        },
                    ],
                }
            ],
        }

    if result.status == "refused":
        reason = result.reason or "No relevant brand guidelines were found."
        return {
            "text": "Draft not generated",
            "attachments": [
                {
                    "color": COLOR_MEDIUM,
                    "blocks": [
                        {"type": "section", "text": {"type": "mrkdwn", "text": ":warning: *Draft not generated*"}},
                        {"type": "section", "text": {"type": "mrkdwn", "text": _esc(reason)}},
                        {
                            "type": "context",
                            "elements": [
                                {"type": "mrkdwn", "text": "The agent refuses rather than inventing company policy. Escalate to the PR team."}
                            ],
                        },
                    ],
                }
            ],
        }

    return {
        "text": "Draft failed",
        "attachments": [
            {
                "color": COLOR_HIGH,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f":x: *Something went wrong while drafting.*\n{_esc(result.reason or 'Unknown error')}",
                        },
                    }
                ],
            }
        ],
    }


def help_message() -> dict:
    return {
        "text": "How to use the Ryanair News Agent",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Ryanair News Agent* :airplane:\n"
                        "I post colour-coded alerts when Ryanair or competitors are in the news.\n\n"
                        "• `@Ryanair News Agent demo` - post sample alerts\n"
                        "• Click *Draft PR Response* on an alert to get a draft based on brand guidelines"
                    ),
                },
            }
        ],
    }
