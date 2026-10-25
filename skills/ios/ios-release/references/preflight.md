# Preflight

Run before the first build of a version. Start with `bundle exec fastlane ios release_status`: it shows the
recent builds, their TestFlight state, the groups, the version in progress and the review submissions.

## Version and build number

- `new_version version:x.y.z` sets `MARKETING_VERSION` on the app and its extensions (they must match) and, with
  `apply:true`, creates the App Store version. It refuses a version that is not higher than the live one. Commit
  the bump before building.
- Do not set the build number by hand. `beta` takes the highest number on App Store Connect + 1; Xcode Cloud uses
  its run number. App Store Connect rejects a number it already has, across all versions.

## QA

- A Dev build on a real device has been tested (unless the user explicitly skips it).
- The branch is pushed and the tree is clean. `beta` refuses a dirty tree, because the build must match a commit.

## What's New

- One `fastlane/metadata/<locale>/release_notes.txt` per store locale. A locale without a file keeps its old text.
- Draft all locales, show them to the user, get approval, then `whats_new` (diff) and `whats_new apply:true`.
- Limit 4000 characters. What's New is not indexed for search, so no keyword stuffing.
- It needs a version in progress on App Store Connect (`new_version ... apply:true` first).

## ASO gate (only when the version ships new metadata or screenshots)

Ask the `aso` skill, do not redo its work:

- `validate_metadata.py` passes on the metadata version being shipped.
- Screenshots are on App Store Connect for every required size, including iPad when the app supports iPad (Apple
  rejects the submission without them).
- A rank baseline was measured before the metadata goes live (after that the counterfactual is gone).

The ASO side pushes its own text with `push_metadata` after approval. The release never does.
