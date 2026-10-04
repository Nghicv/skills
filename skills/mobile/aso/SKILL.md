---
name: aso
description: Use when working on App Store Optimization for an iOS or Android app - picking keywords for an app that is not on the store yet, writing or changing store metadata (title/subtitle/keywords/short description), checking where keywords currently rank, explaining why a keyword dropped, or planning the next metadata version. Triggers on ASO, App Store Optimization, keyword research, keyword ranking, app metadata, title/subtitle/keywords, App Store Connect, Google Play Console, product page optimization, PPO, store listing experiments, short description, screenshot localization, "tối ưu App Store", "nghiên cứu từ khoá", "đo ranking", "app tụt hạng".
---

# ASO

Manage App Store keyword ranking and metadata as versioned, measurable work.

## The one rule that prevents most mistakes

**Rank = relevance × popularity.**

- *Relevance* comes from metadata text (title, subtitle, keywords). You control it directly.
- *Popularity* comes from downloads/engagement for that query. You cannot edit it.

Two consequences that people get wrong constantly:

1. **Screenshots do not affect ranking.** Apple does not index text inside images. Screenshots move *conversion*; metadata moves *rank*. Never explain a rank change with a screenshot change, and never explain a conversion change with a keyword change.
2. **Restoring lost relevance does not restore lost popularity.** If a term drops and you lose its downloads, putting the words back may do nothing — the popularity component is gone. Check whether relevance was ever actually lost before "rolling back".

## Which phase are you in?

**First establish the platform.** `config.yml` carries `platform: ios | android | both`.
The two stores follow different — sometimes opposite — rules, and the single most common
ASO mistake is applying one store's playbook to the other.

| Situation | Go to |
|---|---|
| App not on store yet / no keywords chosen | `references/research.md` |
| Writing or changing **iOS** metadata | `references/apple-indexing.md` |
| Writing or changing **Android** metadata | `references/play-indexing.md` |
| Need current ranks / did our change work? | `references/measurement.md` |
| A keyword dropped and we don't know why | `references/diagnosis.md` |
| vN is live and measured, plan vN+1 | `references/iterate.md` |
| Screenshots, locales, A/B testing | `references/screenshots-ppo.md` |
| Pulling ASC / Search API data | `references/data-access.md` |

Read only the file you need. They are independent.

## Per-app data lives in the app repo

Never store app data in this skill. Each app gets `<repo>/aso/`:

```
aso/
  config.yml           # adam_id, storefronts, rollback thresholds
  keywords.yml         # tracked keywords + what we learned about each
  rank-history.csv     # append-only rank time series (source of truth)
  metadata/v1.0.yml    # one file per version, never edited after ship
  measure/<date>.json  # raw measurement runs
  research/            # phase 0 output (new apps / new features)
  screenshots/manifest.yml
  reports/
  CHANGELOG.md
```

Copy starting files from `templates/`. Bootstrap a new app with
`scripts/init_app.py <repo>/aso --adam-id <id>`.

**Screenshot images never go in git.** `manifest.yml` holds paths, checksums and IP
provenance only; the binaries live outside the repo.

## Scripts

All read `<repo>/aso/config.yml`. Run from the repo root.

```bash
S="$(ls -d ~/.claude/skills/aso/scripts ~/.agents/skills/aso/scripts 2>/dev/null | head -1)"
python3 $S/discover_keywords.py aso/ --country us --seed "budget tracker"  # iOS
python3 $S/measure_keywords.py  aso/           # rank iOS
python3 $S/measure_play.py      aso/           # rank Android
python3 $S/compare_measures.py  aso/           # cả hai, tách theo nền tảng
python3 $S/validate_metadata.py aso/metadata/v2.0.yml
```

`rank-history.csv` has a `platform` column; iOS and Android rows live in one file and are
compared separately. Never compare a rank across platforms — the measurement depths differ
(see below).

`validate_metadata.py` must pass before any App Store submission.

## Measurement depth differs by platform

| | iOS | Android |
|---|---|---|
| Source | iTunes Search API | scraping Play web search |
| Depth | up to 200 | **only ~20-30** |
| `result_count` | real total → usable as a difficulty signal | render depth only → **not** a difficulty signal |

So on Android an unranked result means "not in the visible top ~30", **not** "outside the
top 200". Say that plainly in any Android report; do not imply iOS-grade precision.

## Working rules

- **Baseline before you ship.** Measure ranks *before* a metadata version goes live. Once
  it is live the counterfactual is gone forever.
- **Define CORE + a rollback threshold before changing anything.** Without a pre-agreed
  threshold nobody ever dares roll back.
- **Compare in two directions.** vs baseline answers "has this version helped overall"; vs
  the previous measurement answers "what moved recently". Different questions — report both.
- **Never hand-edit `rank-history.csv`.** It is generated from `measure/<date>.json`.
- **Do not write to App Store Connect or Apple Ads without explicit approval.** Produce a
  review document; let the human click. Reading is fine.
- **Record failures in CHANGELOG.md**, not just diffs. "We tried X, it failed, here is why"
  is the single most valuable line in the whole folder.

## Confidence labels

Apple does not document its ranking algorithm. `references/apple-indexing.md` tags every
rule `[APPLE]` (official docs), `[VERIFIED]` (measured first-hand) or `[FOLKLORE]`
(community consensus, no primary source). Never present `[FOLKLORE]` as fact to a user —
say what it is and suggest testing it on their own app.
