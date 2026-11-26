# Ryanair News Event Agent

Slack Bolt test app for a Ryanair news-monitoring bot. When the bot is mentioned,
it posts a hardcoded news alert card. The **Draft PR Response** button replies in
the same Slack thread with a placeholder response and citation.

## Slack app setup

1. Create a Slack app at <https://api.slack.com/apps>.
2. Enable **Socket Mode** and create an app-level token with the `connections:write` scope.
3. Add bot token scopes `app_mentions:read`, `chat:write`, and `channels:history` under **OAuth & Permissions**.
4. Subscribe to the `app_mention` event under **Event Subscriptions**.
5. Under **Interactivity & Shortcuts**, enable interactivity. Socket Mode handles the request delivery.
6. Install the app to a test workspace and invite it to a channel.

## Run locally

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SLACK_BOT_TOKEN = "xoxb-your-bot-token"
$env:SLACK_APP_TOKEN = "xapp-your-app-level-token"
python app.py
```

Mention the bot in a channel, for example `@Ryanair News Bot`, and it will post
the sample card. Click **Draft PR Response** to add the placeholder draft to the
alert thread.

## Test

```powershell
pip install pytest
pytest
```

Never commit real Slack tokens. Use `.env` or environment variables locally.

## Supabase setup

1. Create a Supabase project.
2. Open the SQL Editor and run [`supabase_schema.sql`](./supabase_schema.sql).
3. Copy the project URL and a server-only secret key into your environment:

```powershell
$env:SUPABASE_URL = "https://your-project.supabase.co"
$env:SUPABASE_SECRET_KEY = "your-server-only-secret-key"
```

The backend uses [`database.py`](./database.py) to store news events, attach the
Slack message ID, load the event when the button is clicked, and save the draft
and citation. The secret key must never be exposed to the Slack client, browser,
or committed to GitHub.

The table has Row Level Security enabled. The server-side key is used only by
this trusted backend; add explicit policies before exposing `news_events` to a
frontend or other client.

This repository currently contains the Supabase-backed implementation on the
`backend` branch. The GitHub `main` branch contains a separate frontend Slack
prototype with a different data contract. Do not run both Slack entry points at
the same time; they both register the `draft_pr_response` action. Before
deploying, choose one implementation and merge/update the other branch to use
the same event fields and handler.
