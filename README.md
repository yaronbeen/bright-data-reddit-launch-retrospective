# Reddit Launch Retrospective

Compare a founder's own user-curated cohort of public launch-post URLs across chosen Reddit communities. Summarize observed engagement counters and reply themes by venue and post format to prepare a repeat/change/avoid brief for the next launch.

## Who, why, decision

For founders and launch marketers reviewing posts they authored. Provide a JSON cohort with each post URL, subreddit, format, observed counters, and optional manually curated reply themes. The tool helps decide what to repeat, change, or avoid in a next test. It does not search for market demand, identify prospects, or claim that venue or format caused engagement.

## Workflow and synthetic example -> decision

The bundled invented cohort contains three posts: r/indiehackers has 14 observed comments with pricing/onboarding themes; r/saas has 8 comments; r/startups has 5. Run `python3 tool.py --sample`. Output groups these counts and preserves evidence links. A reasonable next step is to inspect the source threads and decide whether to repeat or adapt the format, not conclude that a venue caused better results.

## Quick start

```bash
python3 tool.py --sample
python3 tool.py launch_cohort.json retrospective.json
python3 -m pytest -q
```

Input is JSON. Keep the cohort limited to posts you own/are authorized to review. Live collection is explicitly opt-in and limited to 20 supplied URLs per synchronous request:

```bash
python3 tool.py launch_cohort.json retrospective.json --live --dry-run
BRIGHT_DATA_API_KEY="your-key" python3 tool.py launch_cohort.json retrospective.json --live
```

Current [Bright Data Reddit docs](https://docs.brightdata.com/products/scrapers/reddit/introduction) document Posts dataset `gd_lvz8ah06191smkebj4`, collect-by-URL, sync requests up to 20 URLs, and pay-per-successful-record pricing. If Bright Data returns `202`, the tool reports the snapshot response instead of treating it as records. No live request runs in tests or CI; check [current pricing](https://brightdata.com/pricing/web-scraper) first.

## Outputs and limitations

The JSON report contains post count, venue totals, format counts, manually supplied reply-theme counts, and source URLs. Inputs are user-curated, and counters depend on capture timing. Comparisons can be confounded by audience, timing, post content, moderation, and selection. No causal attribution, market-demand conclusion, or individual prospect inference is made.

## Differentiation

Unlike `bright-data-reddit-demand-radar`, this is not general market problem clustering; it analyzes only a curated cohort of the user's own launch posts. Unlike `bright-data-reddit-outreach` and `hand-raisers`, it does not discover or extract leads or draft replies. The decision is what to adapt for a subsequent launch, not who to contact or what the market broadly wants.

## Safety and FAQ

No login, private community access, user profiling, outreach, or posting. The sample is synthetic. `.env` is ignored; no key is needed offline.

**Does a higher comment count mean the format worked?** No; this report is descriptive and cannot establish causality.

**Can it include any launch post?** Only posts the operator is authorized to analyze; the intended cohort is the user's own public launch posts.

MIT License. Independent demonstration; not affiliated with or endorsed by Bright Data.
