---
name: ios-release
description: Use when shipping an iOS app build - deploying to TestFlight, building with fastlane (match/gym/pilot) or Xcode Cloud, adding a build to tester groups or inviting QC testers, uploading dSYMs to Crashlytics, filling What's New / release notes, submitting a version for App Store review, swapping the build of a version in review, choosing manual/phased/automatic release, releasing or pausing a rollout, or a build that never showed up in TestFlight / went live without QC. Triggers on "release iOS", "deploy TestFlight", "đẩy TestFlight", "submit review", "nộp duyệt", "release notes", "What's New", "dSYM", "tester group", "phased release", "phát hành bản mới".
---

# iOS release

Ship a build from a commit to users with a QC window that cannot be skipped by accident.

## The rule that prevents the worst mistake

**Pick the release type before you submit, every time.** `AFTER_APPROVAL` ("Automatically release") sends the
build to every user the moment Apple approves it: no QC on TestFlight, no monitoring window. A version keeps the
release type it was last given, so it silently carries over from the previous submission. The `submit` lane has no
default for `release:`; say which one the user chose. If they did not choose, ask.

## Where each step lives

All steps are lanes in `<repo>/fastlane/Releasefile`, imported from the Fastfile. If the repo has none, set it
up first (`references/setup-new-app.md`).

| Situation | Read |
|---|---|
| Starting a release: version, QA, What's New, ASO gate | `references/preflight.md` |
| Build locally with fastlane (default) | `references/build-fastlane.md` |
| Build with Xcode Cloud | `references/build-xcode-cloud.md` |
| Testers, groups, build not visible in TestFlight | `references/testflight.md` |
| Submit, release type, swap build in review | `references/submit-review.md` |
| Release, phased rollout, crashes, hotfix | `references/release-monitor.md` |
| Something failed | `references/troubleshooting.md` |
| App has no Releasefile yet | `references/setup-new-app.md` |

Read only the file for the step you are on. The app's own `docs/release-runbook.md`, when present, holds its ids
(groups, workflows) and overrides anything generic here.

## Flow

```
preflight → beta | beta_cloud → QC on TestFlight → whats_new → submit → (approved) → release_version → monitor
```

Both build paths converge on "build VALID on App Store Connect, in the internal groups, dSYMs on Crashlytics".
Everything after that is the same whichever built it.

## Gates

- **Device before TestFlight.** A Dev build on a real device gets tested before any TestFlight build, unless the
  user explicitly asks to skip it.
- **Every App Store Connect write needs approval.** Lanes that write (`new_version`, `whats_new`, `submit`,
  `release_version`, `phased`) print a plan and stop without `apply:true`. Show the plan, get a yes, then re-run
  with `apply:true`. `beta`/`beta_cloud` upload by design: run them only when asked to deploy.
- **QC sign-off before submit.** Submit the exact build QC tested, never a rebuild of it.
- **Report each build's state from the API** (`release_status`), not from what the lane logged.

## Boundary with the `aso` skill

| `ios-release` owns | `aso` owns |
|---|---|
| version, build number, binary, signing | title, subtitle, keywords, description, promo text |
| TestFlight, tester groups, dSYMs | screenshots and their Drive archive, PPO |
| What's New (`release_notes.txt`, not indexed) | `validate_metadata.py`, rank measurement |
| submit, release type, release, rollout | `push_metadata` lane |

- Never run `push_metadata` or upload screenshots from a release. A release changes What's New only, with the
  `whats_new` lane.
- If the version carries new metadata or screenshots, `aso`'s checks are a preflight gate (see `preflight.md`).
- After the version is live, hand over to `aso`: it records `live_from` and measures ranks.

## Common mistakes

- Submitting without checking the release type → went live without QC. Pass `release:` explicitly.
- Expecting an Xcode Cloud build to reach testers on its own → it skips automatic distribution; add it to the group.
- Mixing local and Xcode Cloud builds without moving Xcode Cloud's next build number → duplicate number at upload.
- Submitting right after upload → the build is still `PROCESSING`; the lanes wait for `VALID`.
- Shipping without dSYMs → unsymbolicated crashes for the whole release.
