# Release and monitor

## Release

- `release_version` (plan) then `release_version apply:true` releases a version approved under `manual` or
  `phased` (state `PENDING_DEVELOPER_RELEASE`).
- Approval usually lands within 24–48 h. Tell the user when it does; release only on their word.

## Phased release

Seven days, 1% → 2% → 5% → 10% → 20% → 50% → 100% of automatic updaters. Anyone can still download it manually
from the store page from day one, so phased release limits blast radius, not exposure.

```bash
bundle exec fastlane ios phased action:pause      # up to 30 days in total
bundle exec fastlane ios phased action:resume
bundle exec fastlane ios phased action:complete   # everyone now
```

## What to watch (first 48 h)

- Crashlytics: crash-free users for the new build against the previous one, and any new top issue. If its stack
  traces are not symbolicated, the dSYMs are missing: `dsym build:N`.
- Reviews and ratings in App Store Connect.
- Analytics for the flows the release touched.

## Hotfix

A shipped build cannot be pulled back. Pause the phased rollout if there is one, then ship a fix as a new version
(`new_version version:x.y.z+1`) through the same flow. Expedited review can be requested in App Store Connect for
a critical bug; use it sparingly.

## Handover to ASO

Once the version is live, tell the `aso` side: it fills `live_from` in the metadata version that shipped and
measures ranks against the baseline. Screenshot A/B tests (PPO) only start on a live version.
