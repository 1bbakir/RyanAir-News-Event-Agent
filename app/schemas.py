"""Shared data contract between backend and frontend (Slack).

Both sides import from here. If you change a field, tell your teammate:
this file is the single source of truth for what flows between the two halves.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative"]
ThreatLevel = Literal["none", "low", "medium", "high", "critical"]


class Alert(BaseModel):
    """One analysed news article, produced by the backend, rendered by Slack."""

    article_id: str = Field(..., description="Stable unique id (e.g. hash of the URL)")
    title: str
    url: str
    source: str = Field(..., description="Publisher, e.g. 'Reuters'")
    published_at: Optional[datetime] = None
    company: str = Field(..., description="Company the article is about, e.g. 'Ryanair' or 'easyJet'")
    is_competitor: bool = False
    sentiment: Sentiment = Field("neutral", description="Not stored in the Supabase table yet")
    threat_level: ThreatLevel
    summary: str = Field("", description="Short business summary from the LLM")
    threat_reason: Optional[str] = Field(None, description="Why the LLM chose this threat level")


class DraftResult(BaseModel):
    """Result of the RAG 'Draft PR Response' workflow."""

    status: Literal["ok", "refused", "error"]
    draft: Optional[str] = None
    sources: list[str] = Field(default_factory=list, description="Brand guideline files used")
    reason: Optional[str] = Field(None, description="Why the draft was refused / failed")
