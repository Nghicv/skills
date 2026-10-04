# Measuring keyword rank

## Method

`scripts/measure_keywords.py` queries the public iTunes Search API per storefront and
records the position of the app's `adam_id` in the result list.

```
https://itunes.apple.com/search?term=<kw>&country=<cc>&entity=software&limit=200
```

`[VERIFIED]` This tracks reality well for terms where the app ranks at all — positions it
reported (#1, #2, #4, #10) matched the live store. Paid ASO tools add modelling on top;
for tracking *your own* app's movement over time, consistency of method matters more than
absolute precision. **Never mix methods inside one `rank-history.csv`.**

## Always record `result_count`

The number of results the query returned, alongside the rank. This one column separates
two completely different problems:

| rank | result_count | Meaning |
|---|---|---|
| `null` | 200 | Ranked below the cutoff — a *popularity* problem |
| `null` | 176 | Apple returned everything it had and you were not in it — an **indexing/relevance** problem |

Without it you cannot tell "we rank badly" from "we are not eligible at all", and those
need opposite fixes.

`[VERIFIED]` Observed relationship between `result_count` and achievable rank for a small
app in one storefront:

| result_count | Rank achieved |
|---|---|
| 8 | #1 |
| 32 | #2 |
| 48 | #4 |
| 191 | #10 |
| 176 | not ranked |
| 177 | not ranked |

Rule of thumb: **under ~50 results a small app can take the top 5; over ~150 you need real
popularity and metadata alone will not do it.**

## Baseline discipline

1. Measure **before** the new metadata version goes live. This is the only chance.
2. Store it as `measure/<date>.json` and set `baseline:` in `config.yml`.
3. Record which metadata version each measurement corresponds to. Comparing dates without
   knowing the version behind them is meaningless.

## Cadence

Apple re-indexes within days, but ranking settles slower.

- Baseline: day 0 (before release)
- Then +3, +7, +14 days after the version is live
- Steady state: every 2 weeks

Do not judge a metadata change before +7 days.

## Compare in two directions

These answer different questions and both belong in the report:

- **vs baseline** — cumulative effect of everything since we started
- **vs previous measurement** — what moved in this most recent period

A keyword can be up 40 places vs baseline while falling 15 this month. Reporting only the
first hides an active problem.

`compare_measures.py` produces both, plus: new entries to top 200, drop-outs, and any CORE
keyword breaching the rollback threshold.

## Rollback threshold

Set in `config.yml` before shipping, e.g. a CORE keyword falling more than 5 positions,
sustained over 7 days. Two measurements a week apart both breaching it = roll back.

A threshold decided *after* a drop is not a threshold, it is a negotiation.
