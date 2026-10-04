# Screenshots, localization, and PPO

## Screenshots do not affect ranking

Apple does not index text inside images. Screenshots are a **conversion** lever only.
A screenshot change can never explain a rank change, and a keyword change can never
explain a conversion change. Keep the two analyses separate.

## Localized sets

Ordering by return on effort:

1. **Localize the store page at all** for markets where you already rank. Ranking in a
   market while showing English screenshots is the most common wasted opportunity.
2. **Match slides to the keywords you rank for.** If you place well for a feature, that
   feature needs a slide. See the coverage-gap section in `iterate.md`.
3. Aesthetic refinement — real, but smallest of the three.

## The IP gate — blocking

Every asset needs cleared provenance before submission: fonts, icons, stock media, music,
and any third-party brand or character.

`screenshots/manifest.yml` carries `ip_cleared: true|false` per slide.
`validate_metadata.py` fails if a set is marked submission-ready with any slide uncleared.

This exists because it is cheap to add a borrowed asset during design and very expensive to
discover it after the set is live in twelve locales.

## Images stay out of git

Store binaries outside the repo (design tool, object storage, shared drive). The manifest
holds path, checksum, source and IP status. A repo that accumulated screenshot binaries
needed a history rewrite to shed ~380MB.

## Product Page Optimization (PPO)

Apple's built-in A/B test: up to 3 treatments against the original, traffic split evenly,
measured on conversion.

**Traffic requirements — check before starting, not after:**

| Daily product page views | What you can detect |
|---|---|
| < 500 | Struggles to reach significance in under 30 days for anything below a ~10% relative change; may need the full 90 |
| 2,000+ | ~5% relative change within about 2 weeks |

Rules:
- **Never read a result before day 14.** Early readings are noise.
- Most healthy tests settle at 14–30 days; small apps need longer, up to Apple's 90-day max.
- Statistical significance is not business impact. A significant +2% may not be worth a
  quarter of design effort.
- A treatment splitting traffic means most visitors see something other than your best
  asset for the duration. Factor that cost in for long tests.

If the app is well under 500 daily page views, PPO will likely not produce a trustworthy
answer. Say so before the test starts rather than analysing noise for three months.

## Sources

- https://appbot.co/blog/product-page-optimization/
- https://www.apptweak.com/en/aso-blog/product-page-optimization-a-guide-to-app-store-a-b-testing
