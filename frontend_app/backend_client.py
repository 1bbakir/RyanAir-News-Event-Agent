"""The ONE place where the Slack frontend talks to the backend.

Integration with the real backend = change only this file.
"""
import os
from typing import Any

from frontend_app.schemas import Alert, DraftResult

USE_MOCK = os.getenv("USE_MOCK_BACKEND", "true").lower() == "true"
OWN_COMPANY = "ryanair"


def alert_from_news_event(row: dict[str, Any]) -> Alert:
    """Convert a Supabase ``news_events`` row into the Slack alert contract."""

    company = row.get("company") or "Ryanair"
    is_competitor = row.get("is_competitor")
    if is_competitor is None:
        is_competitor = company.strip().lower() != OWN_COMPANY

    return Alert(
        article_id=str(row["id"]),
        title=row["title"],
        url=row["article_url"],
        source=row.get("source_name") or "Unknown source",
        published_at=row.get("published_at") or row.get("created_at"),
        company=company,
        is_competitor=is_competitor,
        sentiment=row.get("sentiment") or "neutral",
        threat_level=row["threat_level"],
        threat_reason=row.get("threat_reason"),
        summary=row.get("summary") or "",
    )


def draft_pr_response(article_id: str) -> DraftResult:
    """Run the RAG workflow for an article and return a draft (or a refusal)."""
    if USE_MOCK:
        from frontend_app.mock_backend import draft_pr_response as mock_draft

        return mock_draft(article_id)

    # TODO(integration): replace with the backend's real function, e.g.
    # from backend.rag.drafting import draft_pr_response as real_draft
    # return real_draft(article_id)
    raise NotImplementedError("Real backend not connected yet - set USE_MOCK_BACKEND=true")


def approve_draft(article_id: str, user_id: str) -> None:
    """Record or publish an approved draft when the real workflow is connected."""
    if USE_MOCK:
        return
    raise NotImplementedError("Real approval workflow not connected yet - set USE_MOCK_BACKEND=true")
