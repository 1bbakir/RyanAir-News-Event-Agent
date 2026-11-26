"""Alert card states and draft buttons (no Slack connection needed)."""
from frontend_app.mock_backend import MOCK_ALERTS
from frontend_app.schemas import DraftResult
from frontend_app.slack import blocks

HIGH = MOCK_ALERTS[0]


def _card(msg):
    return msg["attachments"][0]


def _actions(card, block_id):
    return next(b for b in card["blocks"] if b.get("block_id") == block_id)


def test_title_is_not_duplicated_above_the_card():
    msg = blocks.alert_message(HIGH)
    # top-level blocks exist -> Slack does not print `text` above the card
    assert msg["blocks"]
    assert HIGH.title not in str(msg["blocks"])


def test_drafting_hides_draft_button_but_keeps_link():
    attachments = blocks.alert_message(HIGH)["attachments"]
    new = blocks.alert_with_status(attachments, "drafting", "U1", HIGH.article_id)[0]
    ids = [e["action_id"] for e in _actions(new, blocks.ALERT_ACTIONS_BLOCK_ID)["elements"]]
    assert blocks.DRAFT_ACTION_ID not in ids
    assert blocks.OPEN_ARTICLE_ACTION_ID in ids
    assert "Drafting" in str(_actions(new, blocks.ALERT_STATUS_BLOCK_ID))


def test_refused_offers_try_again():
    attachments = blocks.alert_message(HIGH)["attachments"]
    new = blocks.alert_with_status(attachments, "refused", "U1", HIGH.article_id)[0]
    first = _actions(new, blocks.ALERT_ACTIONS_BLOCK_ID)["elements"][0]
    assert first["action_id"] == blocks.DRAFT_ACTION_ID
    assert first["value"] == HIGH.article_id


def test_status_updates_do_not_stack():
    attachments = blocks.alert_message(HIGH)["attachments"]
    a = blocks.alert_with_status(attachments, "drafting", "U1", HIGH.article_id)
    b = blocks.alert_with_status(a, "ready", "U1", HIGH.article_id)[0]
    statuses = [x for x in b["blocks"] if x.get("block_id") == blocks.ALERT_STATUS_BLOCK_ID]
    assert len(statuses) == 1 and "ready" in str(statuses[0])
    assert b["color"] == blocks.COLOR_HIGH


def test_draft_has_approve_and_regenerate():
    msg = blocks.draft_message(DraftResult(status="ok", draft="Hi", sources=["a.md"]), "U1", "mock-001")
    ids = [e["action_id"] for e in _actions(_card(msg), blocks.DRAFT_ACTIONS_BLOCK_ID)["elements"]]
    assert ids == [blocks.APPROVE_ACTION_ID, blocks.REGENERATE_ACTION_ID]


def test_footer_replaces_draft_buttons():
    msg = blocks.draft_message(DraftResult(status="ok", draft="Hi", sources=["a.md"]), "U1", "mock-001")
    new = blocks.draft_with_footer(msg["attachments"], "Approved by <@U2>")[0]
    assert "Approved" in str(new) and "approve_draft" not in str(new)
