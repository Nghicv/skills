# Set up a new app

```bash
S="$(ls -d ~/.claude/skills/ios-release ~/.agents/skills/ios-release 2>/dev/null | head -1)"
```

## fastlane

1. `Gemfile` with `gem "fastlane"`, then `bundle install`.
2. `fastlane/Appfile` with `app_identifier` and `team_id`.
3. `cp $S/templates/Releasefile fastlane/` and fill `RELEASE`:
   - `targets`: every target embedded in the shipped app with its Release bundle id (`xcodebuild -list`, then
     `-showBuildSettings -configuration Release` per target).
   - `key_env`: the prefix of the app's ASC key variables. Use a per-app prefix when the machine has keys of
     several teams.
   - `upload_symbols`: path of Crashlytics' `upload-symbols` (Pods or SPM checkout).
4. Add `import "Releasefile"` near the top of `fastlane/Fastfile`. Keep the ASO lanes (`pull_metadata`,
   `push_metadata`) in the Fastfile; do not merge them into the Releasefile.
5. `cp $S/templates/Matchfile fastlane/` and set `team_id`.
6. `fastlane/.env.example` lists `<PREFIX>_KEY_ID`, `<PREFIX>_ISSUER_ID`, `<PREFIX>_KEY_PATH`, `MATCH_PASSWORD`;
   `fastlane/.env` is gitignored. `build/` is gitignored.
7. `bundle exec fastlane lanes` loads without errors, `release_status` prints the app.

## Signing (once, with approval)

1. Every bundle id in `targets` is registered in the portal, with its capabilities (App Groups ticked by hand).
2. `bundle exec fastlane ios certs` creates the profiles in the match repo.
3. `bundle exec fastlane ios beta upload:false` builds and signs; check
   `codesign -dvv build/fastlane/*.app` or the IPA's embedded profile.

## Xcode Cloud (optional)

1. Workflow "Testflight": manual start on the release branches, archive with an App Store–eligible distribution.
2. `cp $S/templates/ci_post_xcodebuild.sh ci_scripts/` for dSYMs, plus a `ci_post_clone.sh` that installs Pods.
3. Set `RELEASE[:xcode_cloud_workflow]` to the workflow's name.

## Runbook

Write `docs/release-runbook.md` in the app repo with its specifics (group names and ids, workflows, quirks) and
point the repo's CLAUDE.md/AGENTS.md at it. Keep generic facts in this skill, not there.
