import tool


def test_posts_request_uses_documented_posts_dataset(monkeypatch):
    captured = {}
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'[{"url":"https://www.reddit.com/r/saas/comments/a1/launch/","num_comments":7}]'
    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = req.data
        return Response()
    monkeypatch.setattr(tool.urllib.request, "urlopen", fake_urlopen)
    rows = tool.collect_posts(["https://www.reddit.com/r/saas/comments/a1/launch/"], "secret")
    assert "dataset_id=gd_lvz8ah06191smkebj4" in captured["url"]
    assert b'[{"url":' in captured["body"]
    assert rows[0]["num_comments"] == 7


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
