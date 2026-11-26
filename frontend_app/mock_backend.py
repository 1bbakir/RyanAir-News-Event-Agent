"""Fake backend so the Slack frontend can be built before the real one exists.

All articles below are invented test data (example.com URLs).
Replace with the real backend by setting USE_MOCK_BACKEND=false (see backend_client.py).
"""
import time
from datetime import datetime, timedelta, timezone

from frontend_app.schemas import Alert, DraftResult

_now = datetime.now(timezone.utc)

MOCK_ALERTS: list[Alert] = [
    Alert(
        article_id="mock-001",
        title="Ryanair cancels 400 flights as French air traffic control strike hits Europe",
        url="https://example.com/mock/ryanair-atc-strike",
        source="Mock News",
        published_at=_now - timedelta(minutes=12),
        company="Ryanair",
        sentiment="negative",
        threat_level="high",
        summary="A two-day French ATC strike forces Ryanair to cancel around 400 flights, "
        "affecting ~70,000 passengers. Ryanair blames the EU Commission for failing to protect overflights.",
    ),
    Alert(
        article_id="mock-002",
        title="Passengers criticise Ryanair over new cabin bag sizer rules",
        url="https://example.com/mock/ryanair-bag-rules",
        source="Mock Travel Blog",
        published_at=_now - timedelta(hours=1),
        company="Ryanair",
        sentiment="negative",
        threat_level="medium",
        summary="Social media backlash over stricter enforcement of cabin bag dimensions at boarding gates.",
    ),
    Alert(
        article_id="mock-003",
        title="Ryanair reports record summer traffic of 20 million passengers in August",
        url="https://example.com/mock/ryanair-record-traffic",
        source="Mock Aviation Weekly",
        published_at=_now - timedelta(hours=3),
        company="Ryanair",
        sentiment="positive",
        threat_level="none",
        summary="Record monthly traffic with a 94% load factor; growth driven by new bases in Italy and Poland.",
    ),
    Alert(
        article_id="mock-004",
        title="Wizz Air launches 12 new routes from Rome Fiumicino",
        url="https://example.com/mock/wizz-rome-routes",
        source="Mock Aviation Weekly",
        published_at=_now - timedelta(hours=5),
        company="Wizz Air",
        is_competitor=True,
        sentiment="neutral",
        threat_level="medium",
        summary="Wizz Air expands in Rome with routes overlapping six existing Ryanair routes, signalling a fare war.",
    ),
    Alert(
        article_id="mock-005",
        title="easyJet partners with travel app for in-flight entertainment",
        url="https://example.com/mock/easyjet-entertainment",
        source="Mock Tech News",
        published_at=_now - timedelta(hours=8),
        company="easyJet",
        is_competitor=True,
        sentiment="neutral",
        threat_level="low",
        summary="easyJet adds streaming entertainment via a partner app; limited direct impact on Ryanair.",
    ),
]

_MOCK_DRAFTS: dict[str, DraftResult] = {
    "mock-001": DraftResult(
        status="ok",
        draft=(
            "We sincerely apologise to the 70,000 passengers whose travel plans have been disrupted "
            "by today's French ATC strike. These cancellations are outside Ryanair's control. "
            "All affected passengers have been notified by email/SMS and can choose a free transfer, "
            "a full refund, or reimbursement under EU261 where applicable. We again call on the "
            "European Commission to protect overflights during national ATC strikes."
        ),
        sources=["crisis_communication.md", "compensation_policy.md"],
    ),
    "mock-002": DraftResult(
        status="ok",
        draft=(
            "Our bag rules haven't changed: every passenger can bring one small personal bag for free, "
            "and the sizes are clearly shown at booking. Keeping these rules is how we keep fares the lowest in Europe."
        ),
        sources=["tone_of_voice.md"],
    ),
}


def draft_pr_response(article_id: str) -> DraftResult:
    """Simulates the slow RAG + LLM call (real one will take ~5-15 s)."""
    time.sleep(8)
    return _MOCK_DRAFTS.get(
        article_id,
        DraftResult(
            status="refused",
            reason="No brand guideline matched this article closely enough. "
            "A draft was not generated to avoid inventing company policy.",
        ),
    )
