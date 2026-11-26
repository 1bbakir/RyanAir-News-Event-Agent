"""Click flow with a fake Slack client: ack first, status updates, approve."""
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")


@pytest.fixture(scope="module")
def server():
    with patch("slack_sdk.WebClient.auth_test", return_value={"ok": True, "user_id": "UB", "bot_id": "B", "team_id": "T"}):
        from app.slack import server as srv
    return srv


def _alert_body(article_id="mock-001"):
    from app.mock_backend import MOCK_ALERTS
    from app.slack import blocks

    msg = blocks.alert_message(next(a for a in MOCK_ALERTS if a.article_id == article_id))
    return {
        "actions": [{"value": article_id}],
        "channel": {"id": "C1"},
        "user": {"id": "U1"},
        "message": {"ts": "100.1", **msg},
    }


def _run_now(server):
    """Run background jobs immediately, so the test can check the result."""
    return patch.object(server.executor, "submit", side_effect=lambda fn, *a: fn(*a))


def test_draft_click_acks_first_then_updates_alert_and_thread(server):
    with patch("app.backend_client.draft_pr_response") as draft, _run_now(server):
        from app.schemas import DraftResult

        draft.return_value = DraftResult(status="ok", draft="Sorry", sources=["crisis_communication.md"])
        client, ack = MagicMock(), MagicMock()
        client.chat_postMessage.return_value = {"ts": "200.2"}
        server.on_draft_clicked(ack, _alert_body(), client)

    ack.assert_called_once()
    updates = [c.kwargs for c in client.chat_update.call_args_list]
    alert_updates = [u for u in updates if u["ts"] == "100.1"]
    assert "Drafting" in str(alert_updates[0]["attachments"])
    assert "Draft ready" in str(alert_updates[-1]["attachments"])
    draft_update = next(u for u in updates if u["ts"] == "200.2")
    assert "approve_draft" in str(draft_update["attachments"])


def test_refusal_puts_try_again_on_alert(server):
    with _run_now(server), patch("app.mock_backend.time.sleep"):
        client = MagicMock()
        client.chat_postMessage.return_value = {"ts": "200.2"}
        server.on_draft_clicked(MagicMock(), _alert_body("mock-004"), client)  # mock-004 -> refused
    last_alert = [c.kwargs for c in client.chat_update.call_args_list if c.kwargs["ts"] == "100.1"][-1]
    assert "Try again" in str(last_alert["attachments"])


def test_approve_updates_draft(server):
    from app.schemas import DraftResult
    from app.slack import blocks

    draft = blocks.draft_message(DraftResult(status="ok", draft="Hi", sources=["a.md"]), "U1", "mock-001")
    body = {"actions": [{"value": "mock-001"}], "channel": {"id": "C1"}, "user": {"id": "U2"},
            "message": {"ts": "300.3", "thread_ts": "100.1", **draft}}
    with _run_now(server):
        client, ack = MagicMock(), MagicMock()
        server.on_approve(ack, body, client)
    ack.assert_called_once()
    assert "Approved by <@U2>" in str(client.chat_update.call_args.kwargs["attachments"])
