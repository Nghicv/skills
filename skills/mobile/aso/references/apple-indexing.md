# How the App Store indexes metadata

> **iOS only.** Several rules here are the *opposite* on Google Play — most importantly
> word repetition, which is wasteful on iOS and necessary on Play. For Android read
> `play-indexing.md` instead; never apply this file to a Play listing.

Every rule is tagged:
- `[APPLE]` — stated in Apple's own documentation
- `[VERIFIED]` — measured first-hand on a real app
- `[FOLKLORE]` — strong community consensus, no primary source. Treat as a hypothesis.

## Field limits `[APPLE]`

| Field | Limit | Indexed for search? |
|---|---|---|
| App Name (Title) | 30 | Yes — strongest weight |
| Subtitle | 30 | Yes |
| Keywords | 100 | Yes — never shown to users |
| Promotional Text | 170 | **No** |
| Description | 4000 | **No** (iOS; differs from Google Play) |
| What's New | 4000 | **No** |

Only the first three affect ranking. Writing keywords into the description is wasted
effort on iOS.

## Keyword field syntax `[FOLKLORE]`

- Comma-separated, **no space after commas** — a space costs a character
- No need to repeat plurals; Apple handles basic singular/plural
- Do not use commas inside a phrase you want matched as a phrase
- Skip your own app name, your category name, and the word "app"

## Words combine across fields `[FOLKLORE]`

Apple builds searchable phrases by combining single words drawn from Title + Subtitle +
Keywords. You do not need the exact phrase in one field; `budget` in the title and
`tracker` in the keyword field can together match "budget tracker".

**Practical effect:** think in unique *words*, not phrases. A phrase already achievable
by combination is wasted space.

## No credit for repeating a word `[FOLKLORE]`

A word already in the Title gains nothing by appearing again in the Subtitle or Keywords.
Each word is counted once. Repeats burn characters.

> Measured case: a Vietnamese keyword field used 99/100 characters, of which 17 repeated
> a phrase already present verbatim in the Title. Those 17 characters bought nothing.

This is the highest-value rule in this file **and it is folklore.** If a user's ranking
depends on it, say so and suggest testing: remove one duplicated word, ship, measure.

## Cross-localization — extra keyword fields `[FOLKLORE]`

Each storefront has a primary language plus secondary languages that are *also* indexed
there. Filling a secondary locale gives you another Title + Subtitle + Keywords set for
that same storefront.

Example — the US storefront also indexes: `ar`, `zh-Hans`, `zh-Hant`, `fr`, `ko`, `pt-BR`,
`ru`, `es-MX`, `vi`.

Two hard constraints:
- **Phrases never combine across locales.** Words from `en-US` and `es-MX` will not form a
  phrase together. Every phrase must be formable inside one localization.
- Only add locales whose keywords attract users who will actually convert. Impressions
  without installs hurt you.

Verify the current locale table for the storefronts you care about before relying on this.

## Changing the Title is expensive `[FOLKLORE]`

A Title change resets accumulated ranking history for the terms it carried. Prefer the
keyword field for new terms; use the Subtitle for medium-weight additions; change the
Title only for a deliberate repositioning.

## Head terms you cannot win `[VERIFIED]`

If the app ranked #1 for a query has that exact query as its app name, a smaller app will
not take it with metadata alone — that competitor has exact-match relevance *and* the
popularity that comes from owning the term.

> Measured case: an app with the exact phrase in its own Title still sat outside the top
> 200 for that phrase, because the #1 result was an app literally named that phrase.

Check the SERP before committing Title space to a head term.

## Non-English tokenization `[FOLKLORE]`

Languages without spaces between words (ja, zh, th) and analytic languages with
multi-syllable words (vi) do not tokenize like English. Do not assume a
space-separated keyword list behaves the same way. Have a native speaker sanity-check the
keyword field, and prefer measuring over theorising.

## China `[APPLE]`

Do not mention AI in metadata for mainland China without the required certification —
apps have been removed for it.

## Sources

Community/secondary, not Apple primary:
- https://aso.dev/metadata/cross-localization/
- https://appradar.com/academy/ios-keyword-field
- https://respectaso.com/diagnose/keywords-not-indexing/
