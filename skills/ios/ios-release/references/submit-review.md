# Submit for review

Only after QC signs off on the TestFlight build, and with What's New written.

```bash
bundle exec fastlane ios submit build:72 release:manual              # plan only
bundle exec fastlane ios submit build:72 release:manual apply:true   # do it
```

## Release type: always explicit

| `release:` | ASC setting | After approval |
|---|---|---|
| `manual` | "Manually release this version" (`MANUAL`) | waits for `release_version` |
| `phased` | `MANUAL` + phased release | waits for `release_version`, then 7-day rollout |
| `auto` | "Automatically release" (`AFTER_APPROVAL`) | live immediately |

Default to recommending `manual` or `phased`; `auto` removes the window between approval and users. The version
keeps whatever type it had last, which is how a build ends up live untested: never rely on the current value.

## What the lane checks and does

- The build exists, is `VALID`, and its version equals the store version in progress.
- If a submission is already waiting or in review, it stops unless `replace:true`.
- With `apply:true`: cancels the old submission if replacing and waits for it to reach `COMPLETE`, attaches the
  build, sets the release type, creates or removes the phased release, then creates a review submission with the
  version and submits it.

## Swap the build of a version in review

`submit build:<new> release:<type> replace:true apply:true`. Underneath:

1. `PATCH /v1/reviewSubmissions/{id}` `{"canceled": true}`, then wait for state `COMPLETE`; the version becomes
   `DEVELOPER_REJECTED`.
2. `PATCH /v1/appStoreVersions/{id}/relationships/build` with the new build.
3. A new `reviewSubmissions` with one `reviewSubmissionItems` (the appStoreVersion), then `PATCH submitted: true`.

The review queue position is lost: the version waits again from the start.

## Rejections

Read the message in App Store Connect → App Review (Resolution Center). Metadata-only rejections are fixed by the
`aso` side and resubmitted without a new build; binary rejections need a new build and `replace:true` is not
needed because nothing is in review.
