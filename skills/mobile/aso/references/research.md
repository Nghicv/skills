# Phase 0 — keyword research from zero

Use for: an app not yet on the store, entering a new locale, or adding a feature that
needs new keyword coverage.

## The cold-start constraint

Rank = relevance × popularity. **A new app has popularity 0.** So do not pick keywords by
search volume — you cannot win high-volume terms with metadata alone. Pick terms with
*few competing apps* that still match real user intent, win those, collect downloads,
and use that popularity to climb harder terms later.

## Steps

### 1. Seed
List what the app actually does, per target locale, in the native language. Do not machine
translate — tokenization and idiom differ. Include: the category noun, the core action
verb, the outcome the user wants, and any well-known brand-adjacent terms.

### 2. Expand — App Store autocomplete
Apple's own suggestions come from real user queries and are free.

```
https://search.itunes.apple.com/WebObjects/MZSearchHints.woa/wa/hints?q=<term>&clientApplication=Software
```
Send the storefront in the `X-Apple-Store-Front` header. `scripts/discover_keywords.py`
does this and recurses one level.

### 3. Volume — Apple Ads Search Popularity
Apple Ads shows a **5–100 Search Popularity** score per keyword. A free Apple Ads account
reaches this screen with no campaign and no payment method. This is the best free volume
proxy for iOS.

Two cautions: the scale is **exponential** (50→60 is a far bigger jump than 20→30), and it
reflects *Search Ads* demand, which is correlated with but not identical to organic search.

### 4. Difficulty — free, two signals
- `result_count` from the Search API (see `measurement.md` for the threshold table)
- Does the #1 result have the query as its **app name**? If yes, treat the term as
  unavailable regardless of volume.

### 5. Intent fit
Would someone typing this actually want this app? A term you can rank for but not satisfy
produces impressions without installs, which hurts you.

### 6. Decide
Classify every candidate into exactly one of:

- **TITLE** — one, maybe two terms. Must be winnable *and* central to the app. Expensive
  to change later.
- **SUBTITLE** — medium weight, secondary positioning.
- **KEYWORDS** — everything else worth having.
- **SKIP** — record *why*, so nobody re-litigates it in six months.

### 7. Output
`aso/research/candidates.csv`:

```csv
country,keyword,popularity,result_count,top1_app,top1_exact_match,intent_fit,verdict
```

plus `aso/research/brief.md` with the reasoning, then graduate the survivors into
`keywords.yml` and `metadata/v1.0.yml`.

### 8. Baseline
Measure all chosen keywords **before** the app goes live. Everything will be `null`. That
null row is what every future comparison is anchored to.

## Adding a feature to a live app

Same machinery, narrower scope, plus three constraints:

1. **The keyword field is zero-sum.** 100 characters. Adding means retiring something —
   run `validate_metadata.py` to find dead keywords first.
2. **Ship the metadata with the app version** that contains the feature. The keyword field
   is versioned in App Store Connect.
3. **A new keyword needs a screenshot.** If you win rank for a feature that no slide shows,
   you get the traffic and lose the conversion. Checklist: keyword in field / slide exists /
   subtitle mentions it if it is a headline feature.
