"""Summarize a founder's own curated public Reddit launch cohort."""
import argparse, json, os, sys, urllib.error, urllib.parse, urllib.request
SAMPLE=[{"url":"https://www.reddit.com/r/indiehackers/comments/a1/launch/","subreddit":"r/indiehackers","format":"show-and-tell","num_upvotes":42,"num_comments":14,"reply_themes":["pricing","onboarding"]},{"url":"https://www.reddit.com/r/saas/comments/b2/launch/","subreddit":"r/saas","format":"question-led","num_upvotes":25,"num_comments":8,"reply_themes":["integrations"]},{"url":"https://www.reddit.com/r/startups/comments/c3/launch/","subreddit":"r/startups","format":"show-and-tell","num_upvotes":19,"num_comments":5,"reply_themes":["pricing"]}]
def collect_posts(urls, key):
    if not 1 <= len(urls) <= 20: raise ValueError("Post collection accepts 1-20 post URLs per sync request")
    if any(not u.startswith("https://www.reddit.com/") for u in urls): raise ValueError("Only canonical public Reddit URLs are accepted")
    query=urllib.parse.urlencode({"dataset_id":"gd_lvz8ah06191smkebj4","format":"json"})
    req=urllib.request.Request("https://api.brightdata.com/datasets/v3/scrape?"+query,data=json.dumps([{"url":u} for u in urls]).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=75) as response:
        payload=response.read().decode()
        if response.status==202: raise RuntimeError("Bright Data returned async snapshot; post sync call returned no post records")
        return json.loads(payload)
def retrospect(posts):
    if not posts: raise ValueError("A curated cohort must contain at least one post")
    venues={}
    for p in posts:
        key=p.get("subreddit","unknown"); v=venues.setdefault(key,{"post_count":0,"observed_comments":0,"observed_upvotes":0,"formats":{},"reply_themes":{}})
        v["post_count"]+=1; v["observed_comments"]+=p.get("num_comments") or 0; v["observed_upvotes"]+=p.get("num_upvotes") or 0
        fmt=p.get("format","unspecified"); v["formats"][fmt]=v["formats"].get(fmt,0)+1
        for t in p.get("reply_themes",[]): v["reply_themes"][t]=v["reply_themes"].get(t,0)+1
    return {"post_count":len(posts),"venues":venues,"evidence":[{"url":p.get("url"),"subreddit":p.get("subreddit"),"format":p.get("format")} for p in posts],"recommendation":"Repeat venues/formats with useful observed replies; adjust the next test based on the linked themes.","limits":["Observed engagement is descriptive, not causal or attributable to venue/format.","Cohort is user-curated and not comparable unless collection windows and selection rules match.","No general market demand or prospect inference."]}
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("input",nargs="?"); p.add_argument("output",nargs="?",default="retrospective.json"); p.add_argument("--sample",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--dry-run",action="store_true"); a=p.parse_args()
    try:
        data=SAMPLE if a.sample else json.load(open(a.input,encoding="utf-8"))
        if a.dry_run: print(json.dumps({"posts":len(data),"live_calls":0,"dataset_id":"gd_lvz8ah06191smkebj4" if a.live else None})); return 0
        if a.live:
            key=os.environ.get("BRIGHT_DATA_API_KEY")
            if not key: raise ValueError("Set BRIGHT_DATA_API_KEY in the environment")
            original={r["url"]:r for r in data}
            fetched=collect_posts(list(original),key)
            data=[]
            for row in fetched:
                prior=original.get(row.get("url"),{})
                data.append({**prior,**row,"url":row.get("url") or prior.get("url"),"subreddit":row.get("community_name") or prior.get("subreddit"),"num_upvotes":row.get("num_upvotes",prior.get("num_upvotes")),"num_comments":row.get("num_comments",prior.get("num_comments"))})
        json.dump(retrospect(data),open(a.output,"w",encoding="utf-8"),indent=2); print(json.dumps({"output":a.output,"posts":len(data)})); return 0
    except (ValueError,OSError,KeyError,urllib.error.URLError,RuntimeError) as e: print(str(e),file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
