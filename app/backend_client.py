"""The ONE place where the Slack frontend talks to the backend.

Integration with the real backend = change only this file.
"""
import os

from app.schemas import DraftResult

USE_MOCK = os.getenv("USE_MOCK_BACKEND", "true").lower() == "true"


def draft_pr_response(article_id: str) -> DraftResult:
    """Run the RAG workflow for an article and return a draft (or a refusal)."""
    if USE_MOCK:
        from app.mock_backend import draft_pr_response as mock_draft

        return mock_draft(article_id)

    # TODO(integration): replace with the backend's real function, e.g.
    # from app.rag.drafting import draft_pr_response as real_draft
    # return real_draft(article_id)
    raise NotImplementedError("Real backend not connected yet - set USE_MOCK_BACKEND=true")
