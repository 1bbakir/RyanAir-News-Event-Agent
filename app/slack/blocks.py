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

DRAFT_ACTION_ID = "draft_pr_response"  # on the alert card
APPROVE_ACTION_ID = "approve_draft"  # on the draft message
REGENERATE_ACTION_ID = "regenerate_draft"  # on the draft message
OPEN_ARTICLE_ACTION_ID = "open_article"

# block_ids let us find and swap these blocks when the message is updated
ALERT_ACTIONS_BLOCK_ID = "alert_actions"
ALERT_STATUS_BLOCK_ID = "alert_status"
DRAFT_ACTIONS_BLOCK_ID = "draft_actions"
MAX_TEXT = 2900  # Slack section text limit is 3000 chars


def _esc(text: str) -> str:
    """Escape characters that Slack mrkdwn treats as control characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cut(text: str, limit: int = MAX_TEXT) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _button(action_id: str, label: str, value: str = "", style: str | None = None, url: str | None = None) -> dict:
    button = {"type": "button", "action_id": action_id, "text": {"type": "plain_text", "text": label, "emoji": True}}
    if value:
        button["value"] = value
    if style:
        button["style"] = style
    if url:
        button["url"] = url
    return button


def _context(text: str, block_id: str | None = None) -> dict:
    block = {"type": "context", "elements": [{"type": "mrkdwn", "text": text}]}
    if block_id:
        block["block_id"] = block_id
    return block


def _header(text: str) -> list[dict]:
    """Small line shown ABOVE the coloured card.

    When a message has top-level `blocks`, Slack uses `text` only for
    notifications and no longer prints it above the card (no duplicated title).
    """
    return [_context(text)]


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
            "block_id": ALERT_ACTIONS_BLOCK_ID,
            "elements": [
                _button(DRAFT_ACTION_ID, ":memo: Draft PR Response", value=alert.article_id, style="primary"),
                _button(OPEN_ARTICLE_ACTION_ID, "Open article", url=alert.url),
            ],
        },
    ]
    level = THREAT_LABEL[alert.threat_level]
    return {
        # notification text (phone / desktop banner), not shown in the channel
        "text": f"[{alert.threat_level.upper()}] {alert.company}: {alert.title}",
        "blocks": _header(f"*New alert* · {level} · {_esc(alert.company)}"),
        "attachments": [{"color": alert_color(alert), "blocks": blocks}],
    }


def alert_with_status(attachments: list[dict], status: str, user_id: str, article_id: str) -> list[dict]:
    """Rebuild the alert card's bottom part to show the drafting status.

    `attachments` are taken from the clicked message in the Slack payload.
    status: "drafting" | "ready" | "refused" | "approved"
    """
    card = attachments[0]
    kept = [b for b in card["blocks"] if b.get("block_id") not in (ALERT_ACTIONS_BLOCK_ID, ALERT_STATUS_BLOCK_ID)]

    # keep the Open-article link button from the original card
    url = None
    for b in card["blocks"]:
        if b.get("block_id") == ALERT_ACTIONS_BLOCK_ID:
            url = next((e.get("url") for e in b.get("elements", []) if e.get("url")), None)
    link = [_button(OPEN_ARTICLE_ACTION_ID, "Open article", url=url)] if url else []

    if status == "drafting":
        text = f":hourglass_flowing_sand: Drafting a response… requested by <@{user_id}>"
        buttons = link  # no Draft button while generating -> no double clicks
    elif status == "ready":
        text = f":memo: Draft ready in the thread below · requested by <@{user_id}>"
        buttons = link
    elif status == "approved":
        text = f":white_check_mark: Response approved by <@{user_id}>"
        buttons = link
    else:  # refused / error
        text = ":warning: No draft was generated - see the thread"
        buttons = [_button(DRAFT_ACTION_ID, ":repeat: Try again", value=article_id)] + link

    new_blocks = kept + [_context(text, ALERT_STATUS_BLOCK_ID)]
    if buttons:
        new_blocks.append({"type": "actions", "block_id": ALERT_ACTIONS_BLOCK_ID, "elements": buttons})
    return [{"color": card.get("color"), "blocks": new_blocks}]


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


def draft_message(result: DraftResult, user_id: str, article_id: str | None = None) -> dict:
    """Final result: a draft with cited sources, a refusal, or an error.

    With `article_id`, the draft gets [Approve] [Regenerate] buttons.
    """
    if result.status == "ok" and result.draft:
        sources = ", ".join(f"`{s}`" for s in result.sources) or "_none reported_"
        card_blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": _esc(_cut(result.draft))}},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f":books: Sources: {sources}"},
                    {"type": "mrkdwn", "text": f"Requested by <@{user_id}> · Draft only, review before publishing"},
                ],
            },
        ]
        if article_id:
            card_blocks.append(
                {
                    "type": "actions",
                    "block_id": DRAFT_ACTIONS_BLOCK_ID,
                    "elements": [
                        _button(APPROVE_ACTION_ID, ":white_check_mark: Approve", value=article_id, style="primary"),
                        _button(REGENERATE_ACTION_ID, ":repeat: Regenerate", value=article_id),
                    ],
                }
            )
        return {
            "text": "PR response draft",
            "blocks": _header(":memo: *Draft PR response*"),
            "attachments": [{"color": COLOR_POSITIVE, "blocks": card_blocks}],
        }

    if result.status == "refused":
        reason = result.reason or "No relevant brand guidelines were found."
        return {
            "text": "Draft not generated",
            "blocks": _header(":warning: *Draft not generated*"),
            "attachments": [
                {
                    "color": COLOR_MEDIUM,
                    "blocks": [
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
        "blocks": _header(":x: *Draft failed*"),
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


def draft_with_footer(attachments: list[dict], text: str) -> list[dict]:
    """Replace the draft's [Approve] [Regenerate] buttons with a status line."""
    card = attachments[0]
    kept = [b for b in card["blocks"] if b.get("block_id") != DRAFT_ACTIONS_BLOCK_ID]
    return [{"color": card.get("color"), "blocks": kept + [_context(text, DRAFT_ACTIONS_BLOCK_ID)]}]


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
                        "• Click *Draft PR Response* on an alert to get a draft based on brand guidelines\n"
                        "• On the draft: *Approve* it or *Regenerate* a new version"
                    ),
                },
            }
        ],
    }
