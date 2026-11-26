"""The ONE place where the Slack frontend talks to the backend.

Integration with the real backend = change only this file.
"""
import os
from typing import Any

from app.schemas import Alert, DraftResult

USE_MOCK = os.getenv("USE_MOCK_BACKEND", "true").lower() == "true"
OWN_COMPANY = "ryanair"


def alert_from_news_event(row: dict[str, Any]) -> Alert:
    """Convert a row of the backend's Supabase `news_events` table into an Alert.

    Column names follow supabase_schema.sql on the backend branch:
    id, title, summary, article_url, source_name, published_at, company,
    threat_level, threat_reason. `sentiment` / `is_competitor` are used if the
    backend adds them later; otherwise sensible defaults are derived here.
    """
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
        from app.mock_backend import draft_pr_response as mock_draft

        return mock_draft(article_id)

    # TODO(integration): replace with the backend's real function, e.g.
    # from app.rag.drafting import draft_pr_response as real_draft
    # return real_draft(article_id)
    raise NotImplementedError("Real backend not connected yet - set USE_MOCK_BACKEND=true")
