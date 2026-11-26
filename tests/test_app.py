import app


class FakeRepository:
    def __init__(self) -> None:
        self.created_event: dict[str, object] | None = None
        self.attached_message: tuple[str, str, str | None] | None = None
        self.saved_draft: tuple[str, str, str] | None = None

    def create_news_event(self, event: dict[str, object]) -> dict[str, object]:
        self.created_event = event
        return {"id": "event-123"}

    def attach_slack_message(
        self, event_id: str, channel_id: str, message_ts: str | None
    ) -> None:
        self.attached_message = (event_id, channel_id, message_ts)

    def get_news_event(self, event_id: str) -> dict[str, object]:
        assert event_id == "event-123"
        return {"article_url": "https://example.com/story"}

    def save_pr_draft(self, event_id: str, draft: str, citation: str) -> None:
        self.saved_draft = (event_id, draft, citation)


def test_news_alert_contains_expected_story_and_actions() -> None:
    blocks = app.build_news_alert_blocks("event-123")
    serialized = str(blocks)

    assert "Ryanair cancels flights after an airport strike" in serialized
    assert "Medium" in serialized
    assert "draft_pr_response" in serialized
    assert "open_news_article" in serialized


def test_news_alert_has_draft_button() -> None:
    actions = next(
        block
        for block in app.build_news_alert_blocks("event-123")
        if block["type"] == "actions"
    )

    assert any(
        element["action_id"] == "draft_pr_response"
        for element in actions["elements"]
    )
    draft_button = next(
        element
        for element in actions["elements"]
        if element["action_id"] == "draft_pr_response"
    )
    assert draft_button["value"] == "event-123"


def test_mention_persists_event_and_slack_message(monkeypatch) -> None:
    repository = FakeRepository()
    monkeypatch.setattr(app, "get_repository", lambda: repository)
    sent: dict[str, object] = {}

    def say(**kwargs):
        sent.update(kwargs)
        return {"ts": "123.456"}

    app.handle_app_mention(
        {"ts": "123.000", "channel": "C123"},
        say,
    )

    assert repository.created_event is not None
    assert repository.attached_message == ("event-123", "C123", "123.456")
    assert sent["thread_ts"] == "123.000"
    blocks = sent["blocks"]
    actions = next(block for block in blocks if block["type"] == "actions")
    assert actions["elements"][0]["value"] == "event-123"


def test_draft_button_loads_and_saves_event(monkeypatch) -> None:
    repository = FakeRepository()
    monkeypatch.setattr(app, "get_repository", lambda: repository)
    acknowledged = []
    sent: dict[str, object] = {}

    app.handle_draft_pr_response(
        lambda: acknowledged.append(True),
        {
            "actions": [{"value": "event-123"}],
            "container": {"thread_ts": "123.000"},
            "message": {"ts": "123.456"},
        },
        lambda **kwargs: sent.update(kwargs),
    )

    assert acknowledged == [True]
    assert repository.saved_draft is not None
    assert repository.saved_draft[0] == "event-123"
    assert sent["thread_ts"] == "123.000"


def test_citation_is_escaped_for_slack(monkeypatch) -> None:
    repository = FakeRepository()
    monkeypatch.setattr(app, "get_repository", lambda: repository)
    sent: dict[str, object] = {}

    def get_event(event_id: str) -> dict[str, object]:
        return {"article_url": "https://example.com/?a=1&b=<unsafe>"}

    repository.get_news_event = get_event  # type: ignore[method-assign]
    app.handle_draft_pr_response(
        lambda: None,
        {"actions": [{"value": "event-123"}], "message": {"ts": "123.456"}},
        lambda **kwargs: sent.update(kwargs),
    )

    assert "&amp;" in sent["text"]
    assert "&lt;unsafe&gt;" in sent["text"]


def test_mention_requires_slack_message_timestamp(monkeypatch) -> None:
    repository = FakeRepository()
    monkeypatch.setattr(app, "get_repository", lambda: repository)

    def say(**kwargs):
        return {}

    try:
        app.handle_app_mention({"ts": "123.000", "channel": "C123"}, say)
    except RuntimeError as error:
        assert "timestamp" in str(error)
    else:
        raise AssertionError("missing Slack timestamp should fail")


def test_malformed_draft_action_is_reported(monkeypatch) -> None:
    monkeypatch.setattr(app, "get_repository", lambda: FakeRepository())
    sent: dict[str, object] = {}

    app.handle_draft_pr_response(
        lambda: None,
        {"actions": [], "message": {"ts": "123.456"}},
        lambda **kwargs: sent.update(kwargs),
    )

    assert "valid news event ID" in sent["text"]
