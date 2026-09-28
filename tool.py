"""Summarize a founder's own curated public Reddit launch cohort."""
import argparse, json, os, re, sys, urllib.error, urllib.parse, urllib.request
SAMPLE=[{"url":"https://www.reddit.com/r/indiehackers/comments/a1/launch/","subreddit":"r/indiehackers","format":"show-and-tell","num_upvotes":42,"num_comments":14,"reply_themes":["pricing","onboarding"]},{"url":"https://www.reddit.com/r/saas/comments/b2/launch/","subreddit":"r/saas","format":"question-led","num_upvotes":25,"num_comments":8,"reply_themes":["integrations"]},{"url":"https://www.reddit.com/r/startups/comments/c3/launch/","subreddit":"r/startups","format":"show-and-tell","num_upvotes":19,"num_comments":5,"reply_themes":["pricing"]}]
def collect_posts(urls, key):
    if not 1 <= len(urls) <= 20: raise ValueError("Post collection accepts 1-20 post URLs per sync request")
    if not isinstance(key,str) or not key: raise ValueError("Bright Data API key is required")
    if any(not valid_post_url(u) for u in urls): raise ValueError("Only canonical public Reddit post URLs are accepted")
    if len(set(urls))!=len(urls): raise ValueError("Post URL inputs must be unique to avoid duplicate billable records")
    query=urllib.parse.urlencode({"dataset_id":"gd_lvz8ah06191smkebj4","format":"json"})
    req=urllib.request.Request("https://api.brightdata.com/datasets/v3/scrape?"+query,data=json.dumps([{"url":u} for u in urls]).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=75) as response:
        payload=response.read().decode()
        if response.status==202: raise BrightDataError("async_snapshot","Bright Data returned an async snapshot; no post records were treated as returned")
        try: result=json.loads(payload)
        except json.JSONDecodeError as e: raise BrightDataError("invalid_response","Bright Data response was not valid JSON") from e
        if not isinstance(result,list) or any(not isinstance(row,dict) or not isinstance(row.get("url"),str) for row in result): raise BrightDataError("invalid_response","Bright Data response did not contain records with URLs")
        return result

class BrightDataError(Exception):
    def __init__(self,code,message): self.code=code; super().__init__(message)

def valid_post_url(url):
    if not isinstance(url,str) or "?" in url or "#" in url: return False
    try: parts=urllib.parse.urlsplit(url)
    except (TypeError,ValueError): return False
    match=re.fullmatch(r"/r/[A-Za-z0-9_]+/comments/[A-Za-z0-9]+/((?:[A-Za-z0-9._~-]|%[0-9A-Fa-f]{2})+)/?",parts.path)
    return parts.scheme=="https" and parts.netloc=="www.reddit.com" and bool(match) and match.group(1) not in (".","..")

def build_report(requested_urls, records, curated_records=None):
    if any(not valid_post_url(url) for url in requested_urls): raise ValueError("Every requested URL must be a canonical Reddit post URL")
    curated_records=curated_records or {}
    requested=set(requested_urls); found={}
    for record in records:
        url=record.get("url")
        if url not in requested: raise BrightDataError("unexpected_record","Collection returned a record without a matching requested URL")
        if url in found: raise BrightDataError("duplicate_record","Collection returned more than one record for a requested URL")
        found[url]=record
    normalized=[]
    for url in requested_urls:
        row=found.get(url)
        if row is None: continue
        source=curated_records.get(url,{})
        curated=row.get("curated") or source.get("curated") or {"format":source.get("format"),"reply_themes":source.get("reply_themes",[]),"subreddit":source.get("subreddit")}
        collected=row.get("collected",row)
        subreddit=collected.get("community_name") or collected.get("subreddit") or curated.get("subreddit")
        fmt=curated.get("format")
        themes=curated.get("reply_themes",[])
        counters={k:collected.get(k) for k in ("num_comments","num_upvotes")}
        normalized.append({"url":url,"subreddit":subreddit,"format":fmt,"reply_themes":themes,**counters,"provenance":{"subreddit":"collected" if collected.get("community_name") or collected.get("subreddit") else "curated","format":"curated" if fmt is not None else "not supplied","reply_themes":"curated" if themes else "not supplied","num_comments":"collected" if counters["num_comments"] is not None else "not returned","num_upvotes":"collected" if counters["num_upvotes"] is not None else "not returned"}})
    report=retrospect(normalized) if normalized else {"post_count":0,"posts":[],"venues":{},"evidence":[],"recommendation":"No records returned; review missing URLs or rerun a smaller authorized collection.","limits":["Observed engagement is descriptive, not causal or attributable to venue/format.","Cohort is user-curated and not comparable unless collection windows and selection rules match.","No general market demand or prospect inference."]}
    missing=[url for url in requested_urls if url not in found]
    report["missing_urls"]=missing; report["partial_collection"]=bool(missing); report["requested_urls"]=requested_urls
    return report
def retrospect(posts):
    if not posts: raise ValueError("A curated cohort must contain at least one post")
    venues={}
    for p in posts:
        key=p.get("subreddit","unknown"); v=venues.setdefault(key,{"post_count":0,"observed_comments":0,"observed_upvotes":0,"formats":{},"reply_themes":{}})
        v["post_count"]+=1; v["observed_comments"]+=p.get("num_comments") or 0; v["observed_upvotes"]+=p.get("num_upvotes") or 0
        fmt=p.get("format","unspecified"); v["formats"][fmt]=v["formats"].get(fmt,0)+1
        for t in p.get("reply_themes",[]): v["reply_themes"][t]=v["reply_themes"].get(t,0)+1
    return {"post_count":len(posts),"posts":posts,"venues":venues,"evidence":[{"url":p.get("url"),"subreddit":p.get("subreddit"),"format":p.get("format"),"provenance":p.get("provenance")} for p in posts],"recommendation":"Repeat venues/formats with useful observed replies; adjust the next test based on the linked themes.","limits":["Observed engagement is descriptive, not causal or attributable to venue/format.","Cohort is user-curated and not comparable unless collection windows and selection rules match.","No general market demand or prospect inference."]}
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("input",nargs="?"); p.add_argument("output",nargs="?",default="retrospective.json"); p.add_argument("--sample",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--dry-run",action="store_true"); a=p.parse_args(argv)
    try:
        if a.sample and a.live: raise ValueError("--sample is offline-only and cannot be combined with --live")
        if a.sample: data=SAMPLE
        elif a.input:
            with open(a.input,encoding="utf-8") as f: data=json.load(f)
        else: p.error("Supply curated launch cohort JSON or use --sample")
        if not isinstance(data,list) or any(not isinstance(r,dict) or not isinstance(r.get("url"),str) for r in data): raise ValueError("Input must be an array of records with URL fields")
        urls=[r["url"] for r in data]
        if any(not valid_post_url(u) for u in urls): raise ValueError("Input requires canonical public Reddit post URLs")
        if a.live and (not 1<=len(urls)<=20 or len(set(urls))!=len(urls)): raise ValueError("Live mode requires 1-20 unique canonical public Reddit post URLs")
        if a.dry_run: print(json.dumps({"posts":len(data),"live_calls":0,"dataset_id":"gd_lvz8ah06191smkebj4" if a.live else None})); return 0
        if a.live:
            key=os.environ.get("BRIGHT_DATA_API_KEY")
            if not key: raise ValueError("Set BRIGHT_DATA_API_KEY in the environment")
            fetched=collect_posts(urls,key)
            result=build_report(urls,fetched,{r["url"]:r for r in data})
        else:
            curated=[{"url":r["url"],"subreddit":r.get("subreddit"),"format":r.get("format"),"reply_themes":r.get("reply_themes",[]),"num_comments":r.get("num_comments"),"num_upvotes":r.get("num_upvotes"),"provenance":{"subreddit":"curated" if r.get("subreddit") else "not supplied","format":"curated" if r.get("format") else "not supplied","reply_themes":"curated" if r.get("reply_themes") else "not supplied","num_comments":"curated" if r.get("num_comments") is not None else "not supplied","num_upvotes":"curated" if r.get("num_upvotes") is not None else "not supplied"}} for r in data]
            result=retrospect(curated); result["requested_urls"]=urls; result["missing_urls"]=[]; result["partial_collection"]=False
        json.dump(result,open(a.output,"w",encoding="utf-8"),indent=2); print(json.dumps({"output":a.output,"posts":result["post_count"],"missing":len(result["missing_urls"])})); return 0
    except BrightDataError as e: print(json.dumps({"error":{"code":e.code,"message":str(e),"retryable":False}}),file=sys.stderr); return 1
    except urllib.error.HTTPError as e: print(json.dumps({"error":{"code":"http_error","message":f"Bright Data returned HTTP {e.code}","retryable":False}}),file=sys.stderr); return 1
    except (ValueError,OSError,KeyError,urllib.error.URLError,RuntimeError) as e: print(json.dumps({"error":{"code":"input_or_transport_error","message":str(e),"retryable":False}}),file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
