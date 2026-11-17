"""Supabase persistence for news events and generated PR drafts."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from supabase import Client, create_client


def create_supabase_client() -> Client:
    """Create a server-side Supabase client from environment variables."""

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SECRET_KEY are required for database access"
        )

    return create_client(url, key)


class NewsEventRepository:
    """Small data-access layer for the public.news_events table."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def create_news_event(self, event: dict[str, Any]) -> dict[str, Any]:
        response = (
            self.client.table("news_events")
            .upsert(event, on_conflict="article_url")
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase did not return the inserted news event")
        return response.data[0]

    def attach_slack_message(
        self,
        event_id: str,
        channel_id: str,
        message_ts: str | None,
    ) -> None:
        self.client.table("news_events").update(
            {
                "slack_channel_id": channel_id,
                "slack_message_ts": message_ts,
            }
        ).eq("id", event_id).execute()

    def get_news_event(self, event_id: str) -> dict[str, Any]:
        response = (
            self.client.table("news_events")
            .select("*")
            .eq("id", event_id)
            .single()
            .execute()
        )
        if not response.data:
            raise LookupError(f"News event {event_id} was not found")
        return response.data

    def save_pr_draft(self, event_id: str, draft: str, citation: str) -> None:
        self.client.table("news_events").update(
            {
                "pr_draft": draft,
                "pr_citation": citation,
                "pr_draft_generated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", event_id).execute()
