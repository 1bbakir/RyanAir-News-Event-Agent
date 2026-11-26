"""Slack Bolt server: listens for @mentions and button clicks.

Run locally:   python -m frontend_app.slack.server

Key rule (brief, 'Asynchronous Processing'): Slack must get ack() within 3 seconds,
otherwise it retries. So every handler calls ack() FIRST, and the slow LLM/RAG work
runs in a background thread.
"""
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from slack_bolt import App
from slack_sdk import WebClient

from frontend_app import backend_client
from frontend_app.mock_backend import MOCK_ALERTS
from frontend_app.schemas import DraftResult
from frontend_app.slack import blocks

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("slack-server")

MODE = os.getenv("SLACK_MODE", "socket")  # "socket" (local dev, no ngrok) or "http" (webhooks)

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.getenv("SLACK_SIGNING_SECRET") if MODE == "http" else None,
    token_verification_enabled=True,
)

executor = ThreadPoolExecutor(max_workers=4)

# Prevents two drafts for the same alert if someone double-clicks
_in_flight: set[str] = set()
_in_flight_lock = threading.Lock()


# ---------- @mention -------------------------------------------------------
@app.event("app_mention")
def on_mention(event, say, client):
    text = event.get("text", "").lower()
    if "demo" in text:
        for alert in MOCK_ALERTS:
            client.chat_postMessage(channel=event["channel"], **blocks.alert_message(alert))
    else:
        say(**blocks.help_message())


# ---------- [Draft PR Response] button -------------------------------------
@app.action(blocks.DRAFT_ACTION_ID)
def on_draft_clicked(ack, body, client):
    ack()  # 1) answer Slack immediately (< 3 s)

    article_id = body["actions"][0]["value"]
    channel = body["channel"]["id"]
    alert_ts = body["message"]["ts"]
    user_id = body["user"]["id"]

    with _in_flight_lock:
        if article_id in _in_flight:
            client.chat_postEphemeral(channel=channel, user=user_id, text="A draft for this alert is already being generated.")
            return
        _in_flight.add(article_id)

    # 2) show a placeholder in the alert's thread
    placeholder = client.chat_postMessage(channel=channel, thread_ts=alert_ts, **blocks.loading_message())

    # 3) slow work in the background; this handler returns right away
    executor.submit(_generate_draft, client, channel, placeholder["ts"], article_id, user_id)


def _generate_draft(client: WebClient, channel: str, placeholder_ts: str, article_id: str, user_id: str):
    try:
        result = backend_client.draft_pr_response(article_id)
    except Exception as exc:  # never leave the user staring at the spinner
        log.exception("Draft generation failed for %s", article_id)
        result = DraftResult(status="error", reason=str(exc))
    finally:
        with _in_flight_lock:
            _in_flight.discard(article_id)

    # 4) replace the placeholder with the final card
    client.chat_update(channel=channel, ts=placeholder_ts, **blocks.draft_message(result, user_id))


@app.action("open_article")
def on_open_article(ack):
    ack()  # link buttons still send an event; just acknowledge it


def main():
    if MODE == "http":
        # Webhook mode: Slack calls POST /slack/events (expose locally with ngrok)
        app.start(port=int(os.getenv("PORT", "3000")))
    else:
        from slack_bolt.adapter.socket_mode import SocketModeHandler

        log.info("Starting in Socket Mode - mention the bot in Slack with 'demo'")
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()


if __name__ == "__main__":
    main()
