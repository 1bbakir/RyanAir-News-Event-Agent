# Ryanair News Event Agent

Slack bot that monitors news about Ryanair and its competitors. Each analysed
article is posted as a colour-coded alert card. The **Draft PR Response** button
generates a suggested PR reply in the alert's thread.

## Project structure

```
app/
├── schemas.py          # Shared data contract (Alert, DraftResult) - backend <-> frontend
├── backend_client.py   # The only place the Slack frontend calls the backend
├── mock_backend.py     # Fake alerts/drafts used until the real backend is connected
└── slack/              # Frontend
    ├── blocks.py       # Block Kit builders (alert card, loading, draft, help)
    ├── server.py       # Bolt app: @mentions and button clicks
    └── notify.py       # send_alert(alert) - used by the backend to post alerts
tests/                  # pytest tests
week1/                  # Week 1 prototype (day5_slack_bot.py)
slack_manifest.yml      # Slack app manifest
```

## Slack app setup

1. Go to <https://api.slack.com/apps> → **Create New App** → **From a manifest**
   and paste the contents of `slack_manifest.yml`.
2. Under **Basic Information → App-Level Tokens**, create a token with the
   `connections:write` scope (this is the `xapp-...` token).
3. Install the app to your workspace and copy the **Bot User OAuth Token** (`xoxb-...`).
4. Invite the bot to a channel: `/invite @Ryanair News Agent`.

## Run locally (macOS / Linux)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (it is git-ignored - never commit it):

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-level-token
SLACK_ALERT_CHANNEL=C0123456789
```

Start the bot:

```bash
python -m app.slack.server
```

In Slack, mention the bot with `demo` (e.g. `@Ryanair News Agent demo`) to post
the mock alerts. Click **Draft PR Response** on an alert to get a draft in its thread.

To post the mock alerts to `SLACK_ALERT_CHANNEL` without the server running:

```bash
python -m app.slack.notify
```

### Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `SLACK_BOT_TOKEN` | - (required) | Bot token `xoxb-...` |
| `SLACK_APP_TOKEN` | - (required in socket mode) | App-level token `xapp-...` |
| `SLACK_ALERT_CHANNEL` | - | Channel ID used by `notify.send_alert` |
| `SLACK_MODE` | `socket` | `socket` for local dev, `http` for webhooks |
| `SLACK_SIGNING_SECRET` | - | Required only when `SLACK_MODE=http` |
| `PORT` | `3000` | HTTP port when `SLACK_MODE=http` |
| `USE_MOCK_BACKEND` | `true` | `false` to use the real backend (see `backend_client.py`) |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Test

```bash
source venv/bin/activate
python -m pytest -v
```

## Backend integration

- Data format: `app/schemas.py` - any change must be agreed by both sides.
- Pushing alerts to Slack: `from app.slack.notify import send_alert; send_alert(alert)`.
- Drafting: replace the `TODO(integration)` in `app/backend_client.py` and set
  `USE_MOCK_BACKEND=false`.
