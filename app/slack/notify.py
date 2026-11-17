"""Entry point for the BACKEND to push an alert into Slack.

Backend usage (after analysing an article):
    from app.slack.notify import send_alert
    send_alert(alert)          # alert is an app.schemas.Alert
"""
import os

from dotenv import load_dotenv
from slack_sdk import WebClient

from app.schemas import Alert
from app.slack.blocks import alert_message

load_dotenv()

_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))


def send_alert(alert: Alert, channel: str | None = None) -> str:
    """Post a colour-coded alert card. Returns the Slack message timestamp (id)."""
    channel = channel or os.environ["SLACK_ALERT_CHANNEL"]
    response = _client.chat_postMessage(channel=channel, **alert_message(alert))
    return response["ts"]


if __name__ == "__main__":
    # Quick manual test: python -m app.slack.notify
    from app.mock_backend import MOCK_ALERTS

    for a in MOCK_ALERTS:
        print("posted", send_alert(a))
