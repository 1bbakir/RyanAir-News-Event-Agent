from week1.day5_slack_bot import build_news_alert_blocks


def test_news_alert_contains_expected_story_and_actions() -> None:
    blocks = build_news_alert_blocks()
    serialized = str(blocks)

    assert "Ryanair cancels flights after an airport strike" in serialized
    assert "Medium" in serialized
    assert "draft_pr_response" in serialized
    assert "open_news_article" in serialized


def test_news_alert_has_draft_button() -> None:
    actions = next(block for block in build_news_alert_blocks() if block["type"] == "actions")

    assert any(
        element["action_id"] == "draft_pr_response"
        for element in actions["elements"]
    )
