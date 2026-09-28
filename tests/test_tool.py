import tool


def test_groups_observed_engagement_by_venue_and_format():
    result = tool.retrospect(tool.SAMPLE)
    assert result["post_count"] == 3
    assert result["venues"]["r/indiehackers"]["observed_comments"] == 14
    assert result["recommendation"]


def test_empty_input_rejected():
    try:
        tool.retrospect([])
    except ValueError:
        return
    assert False, "empty cohort should be rejected"
