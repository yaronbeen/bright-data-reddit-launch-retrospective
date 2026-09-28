import json
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

def test_report_labels_curated_and_collected_provenance():
    report=tool.build_report(["https://www.reddit.com/r/saas/comments/1/x/"],[{"url":"https://www.reddit.com/r/saas/comments/1/x/","curated":{"format":"question-led","reply_themes":["pricing"]},"collected":{"community_name":"saas","num_comments":7,"num_upvotes":9}}])
    post=report["posts"][0]
    assert post["provenance"]["format"] == "curated"
    assert post["provenance"]["reply_themes"] == "curated"
    assert post["provenance"]["num_comments"] == "collected"
    assert post["provenance"]["subreddit"] == "collected"

def test_report_lists_missing_requested_urls_and_partial_collection():
    requested=["https://www.reddit.com/r/saas/comments/1/x/","https://www.reddit.com/r/saas/comments/2/y/"]
    report=tool.build_report(requested,[{"url":requested[0],"num_comments":3}])
    assert report["missing_urls"] == [requested[1]]
    assert report["partial_collection"] is True
    empty=tool.build_report(requested,[])
    assert empty["post_count"]==0 and empty["missing_urls"]==requested and empty["partial_collection"] is True

def test_build_report_keeps_curated_fields_separate_from_collected_fields():
    url="https://www.reddit.com/r/saas/comments/1/x/"
    report=tool.build_report([url],[{"url":url,"community_name":"saas","num_comments":4,"num_upvotes":6}],{url:{"url":url,"format":"question","reply_themes":["pricing"]}})
    row=report["posts"][0]
    assert row["format"]=="question" and row["reply_themes"]==["pricing"]
    assert row["provenance"]["format"]=="curated"
    assert row["provenance"]["num_comments"]=="collected"

def test_collect_posts_rejects_malformed_response_and_empty_response(monkeypatch):
    class Response:
        status=200
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self): return self.payload
    response=Response(); response.payload=b"not json"
    monkeypatch.setattr(tool.urllib.request,"urlopen",lambda *a,**k:response)
    try: tool.collect_posts(["https://www.reddit.com/r/saas/comments/1/x/"],"secret")
    except tool.BrightDataError as e: assert e.code=="invalid_response"
    else: assert False
    response.payload=b"[]"
    assert tool.collect_posts(["https://www.reddit.com/r/saas/comments/1/x/"],"secret")==[]
    response.status=202
    try: tool.collect_posts(["https://www.reddit.com/r/saas/comments/1/x/"],"secret")
    except tool.BrightDataError as e: assert e.code=="async_snapshot"
    else: assert False

def test_live_dry_run_needs_no_key_and_makes_no_request(monkeypatch,capsys):
    monkeypatch.delenv("BRIGHT_DATA_API_KEY",raising=False)
    monkeypatch.setattr(tool.urllib.request,"urlopen",lambda *a,**k:(_ for _ in ()).throw(AssertionError("network called")))
    assert tool.main(["launch_cohort.json","--live","--dry-run"])==0
    assert json.loads(capsys.readouterr().out)["live_calls"]==0
