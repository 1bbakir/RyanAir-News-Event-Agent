from types import SimpleNamespace

import pytest

from database import NewsEventRepository


class FakeQuery:
    def __init__(self, data):
        self.data = data
        self.payload = None
        self.filters = None
        self.selected = None

    def update(self, payload):
        self.payload = payload
        return self

    def eq(self, field, value):
        self.filters = (field, value)
        return self

    def select(self, fields):
        self.selected = fields
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


class FakeClient:
    def __init__(self, data):
        self.query = FakeQuery(data)

    def table(self, name):
        assert name == "news_events"
        return self.query


def test_attach_slack_message_updates_timestamp_and_detects_missing_event() -> None:
    client = FakeClient([{"id": "event-123"}])

    NewsEventRepository(client).attach_slack_message(
        "event-123", "C123", "123.456"
    )

    assert client.query.filters == ("id", "event-123")
    assert client.query.selected == "id"
    assert client.query.payload["slack_message_ts"] == "123.456"
    assert client.query.payload["updated_at"]


def test_save_pr_draft_raises_when_no_event_was_updated() -> None:
    client = FakeClient([])

    with pytest.raises(LookupError, match="event-123"):
        NewsEventRepository(client).save_pr_draft(
            "event-123", "Draft response", "https://example.com/story"
        )
