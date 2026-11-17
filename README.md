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
