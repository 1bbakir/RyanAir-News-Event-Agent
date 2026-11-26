# Ryanair News Event Agent

This repository contains a Supabase-backed Slack backend and a separately
named Slack frontend prototype. The backend is the production entry point;
the frontend prototype provides the richer mock-card workflow, including
drafting status and Approve/Regenerate actions.

## Structure

- [`app.py`](./app.py): Supabase-backed Slack Socket Mode application.
- [`database.py`](./database.py): Supabase persistence layer.
- [`supabase_schema.sql`](./supabase_schema.sql): database table and timestamp trigger.
- [`frontend_app/`](./frontend_app/): Slack card builders, mock workflow, and Supabase-row mapping.
- [`Dockerfile`](./Dockerfile): container entry point for the backend.

Do not run both Slack entry points in the same workspace: both register the
`draft_pr_response` action.

## Setup

Create a `.env` file locally or set environment variables. Never commit real
tokens or secret keys.

```powershell
$env:SLACK_BOT_TOKEN = "xoxb-your-bot-token"
$env:SLACK_APP_TOKEN = "xapp-your-app-level-token"
$env:SUPABASE_URL = "https://your-project.supabase.co"
$env:SUPABASE_SECRET_KEY = "your-server-only-secret-key"
```

Run [`supabase_schema.sql`](./supabase_schema.sql) once in the Supabase SQL
Editor, then start the backend:

```powershell
python app.py
```

Slack must have Socket Mode enabled, an app-level token with
`connections:write`, the `app_mentions:read` and `chat:write` bot scopes,
the `app_mention` event subscription, and interactivity enabled.

## Frontend prototype

The prototype uses the shared contract in `frontend_app/schemas.py` and maps
rows from `public.news_events` through `frontend_app/backend_client.py`.
It can be run separately with:

```powershell
python -m frontend_app.slack.server
```

Set `USE_MOCK_BACKEND=true` for its mock drafting workflow. The real drafting
and approval implementations remain separate integration points; the
Supabase row mapping is covered by tests.

## Docker

Build and run the Supabase-backed backend after setting the required runtime
environment variables:

```powershell
docker build -t ryanair-news-agent .
docker run --env-file .env ryanair-news-agent
```

## Tests

```powershell
python -m pytest -q
```
