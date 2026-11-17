from app.mock_backend import MOCK_ALERTS
from app.schemas import DraftResult
from app.slack import blocks


def test_every_alert_renders_with_button():
    for alert in MOCK_ALERTS:
        msg = blocks.alert_message(alert)
        assert msg["text"]
        card = msg["attachments"][0]
        assert card["color"].startswith("#")
        actions = card["blocks"][-1]["elements"]
        assert actions[0]["action_id"] == blocks.DRAFT_ACTION_ID
        assert actions[0]["value"] == alert.article_id


def test_high_threat_is_red():
    high = next(a for a in MOCK_ALERTS if a.threat_level == "high")
    assert blocks.alert_color(high) == blocks.COLOR_HIGH


def test_draft_cites_sources():
    msg = blocks.draft_message(DraftResult(status="ok", draft="Hi", sources=["tone_of_voice.md"]), "U1")
    assert "tone_of_voice.md" in str(msg)


def test_refusal_has_no_draft_text():
    msg = blocks.draft_message(DraftResult(status="refused", reason="nothing found"), "U1")
    assert msg["text"] == "Draft not generated"
