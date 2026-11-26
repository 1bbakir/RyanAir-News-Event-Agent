"""Tests for the Supabase-row to Slack-alert mapping."""

from frontend_app.backend_client import alert_from_news_event
from frontend_app.slack import blocks


SUPABASE_ROW = {
    "id": "3f6c1a2e-0000-4000-8000-000000000001",
    "title": "Ryanair cancels flights after an airport strike",
    "summary": "A fictional airport strike has disrupted Ryanair services.",
    "article_url": "https://example.com/ryanair-airport-strike",
    "source_name": "Fictional test story",
    "published_at": None,
    "company": "Ryanair",
    "threat_level": "critical",
    "threat_reason": "Flight cancellations may affect customers and reputation.",
    "pr_draft": None,
    "created_at": "2026-11-17T18:00:00+00:00",
}


def test_supabase_row_maps_to_alert() -> None:
    alert = alert_from_news_event(SUPABASE_ROW)
    assert alert.article_id == SUPABASE_ROW["id"]
    assert alert.url == SUPABASE_ROW["article_url"]
    assert alert.source == "Fictional test story"
    assert alert.sentiment == "neutral"
    assert alert.is_competitor is False
    assert alert.published_at is not None


def test_competitor_is_derived_from_company() -> None:
    alert = alert_from_news_event({**SUPABASE_ROW, "company": "Wizz Air"})
    assert alert.is_competitor is True


def test_critical_alert_renders_with_reason_and_button() -> None:
    card = blocks.alert_message(alert_from_news_event(SUPABASE_ROW))["attachments"][0]
    assert card["color"] == blocks.COLOR_HIGH
    assert "Why:" in str(card["blocks"])
    assert card["blocks"][-1]["elements"][0]["value"] == SUPABASE_ROW["id"]


def test_missing_date_and_summary_do_not_break_slack_card() -> None:
    row = {**SUPABASE_ROW, "published_at": None, "created_at": None, "summary": None}
    card = blocks.alert_message(alert_from_news_event(row))["attachments"][0]
    texts = [
        block["text"]["text"]
        for block in card["blocks"]
        if block["type"] == "section" and "text" in block
    ]
    assert all(texts)
    assert "date unknown" in str(card)
