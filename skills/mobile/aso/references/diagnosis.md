# A keyword dropped — playbook

Work in this order. Most people jump to step 5 and edit text that was never the problem.

## 1. Is it a rank problem at all?

| Symptom | Cause | Fix lives in |
|---|---|---|
| Impressions flat/down | Ranking | metadata |
| Impressions up, installs flat | Conversion | screenshots / subtitle |
| Installs up, revenue flat | Traffic quality | targeting / monetization |

Pull impressions per storefront (`data-access.md`) before touching any text.

## 2. Was the relevance actually lost?

Read the metadata that was live before and after. Check whether the term still appears in
**Title + Subtitle + Keywords combined**, remembering that words combine across fields.

> Failure case worth memorising: a team removed a phrase from the keyword field, rank
> collapsed, and they "rolled back" by restoring it. Nothing happened — because the phrase
> had been in the **Title** the whole time, in all three versions. Relevance never changed.
> The rollback was a no-op against the index, and four weeks were lost waiting.

If relevance never changed, the cause is popularity or competition. Stop editing text.

## 3. Isolate the blocking token `[VERIFIED]`

The sharpest diagnostic available. Measure the failing multi-word query, then measure each
component separately.

> Shape of a real result, one storefront:
>
> | Query | Rank |
> |---|---|
> | `expense tracker` | #10 |
> | `simple expense tracker` | #4 |
> | `expense tracker budget` | **not ranked** |
> | `budget` | **not ranked** |
>
> Every query containing `budget` failed; every query without it ranked. The blocker was
> not the term anyone was arguing about — it was the other half of the phrase, the most
> competitive token in that market.

Write the finding into `keywords.yml` under `blocker:` so nobody re-derives it.

## 4. Check who holds #1

If the top app's **name is the query**, the term is not winnable with metadata. Record
`competitor_exact_match: true` and `verdict: SKIP`. Redirect effort to terms you already
place in.

## 5. Only now consider editing

And prefer terms where you rank #5–30 — cheapest distance to a real gain — over trying to
resurrect something that has left the index entirely.

## The death spiral

Rank drop → fewer downloads from that term → lower popularity for that term → harder to
return. This is why the fix window is short and why baselines matter. Once a term is gone
for a month, restoring the text is usually not enough; you need download velocity from
somewhere else.
