# Build locally with fastlane (`beta`)

```bash
bundle exec fastlane ios beta                # build, dSYMs, upload, wait, internal groups
bundle exec fastlane ios beta upload:false   # build and sign only: the signing check
```

## What the lane does

1. Refuses a dirty tree (`.DS_Store` aside).
2. Build number = highest on App Store Connect + 1, passed as `CURRENT_PROJECT_VERSION` through `xcargs`, so the
   app and every extension get the same `CFBundleVersion`.
3. `match readonly:true` installs the distribution cert and one App Store profile per bundle id in `RELEASE[:targets]`.
4. Switches each shipped target to manual signing with its `match AppStore <bundle id>` profile, for the Release
   configuration only. Afterwards every tracked file the build changed is restored: the signing edit, and files
   that build phases regenerate (R.swift rewrites `R.generated.swift` for the Release xcconfig). Without that the
   next `beta` refuses the dirty tree.
5. `build_app` archives into `build/fastlane/` with matching `export_options`.
6. Uploads the archive's dSYMs to Crashlytics (before upload, so a processing failure still leaves symbols).
7. `upload_to_testflight` without waiting, then waits for `VALID` itself and adds the build to every internal group.

## Signing

**match, not automatic signing.** Certs and profiles live encrypted in one private git repo shared by the team's
apps (match keeps them apart by bundle id). A new machine needs only the repo access and `MATCH_PASSWORD`.

- `certs` (readonly:false) is the only lane that creates profiles. Run it once per app, when a target is added, and
  when a profile expires. It writes to the Developer portal and the match repo, so get approval first.
- Build lanes always use `readonly:true`: a build must never create or revoke a cert.
- Why the temporary manual signing: Xcode Cloud needs the project on automatic signing, and `CODE_SIGN_STYLE=Manual`
  in `xcargs` would also hit the Pods/SPM targets, which then fail with "requires a development team".
- The ASC API key cannot drive `xcodebuild -allowProvisioningUpdates` (rejected as "Authentication failed"), and it
  cannot link an App Group to an App ID. If a target uses App Groups, tick the group on the App ID in the portal
  once (a human step), then `certs` can generate a profile that includes it.
- A new extension needs its explicit App ID registered in the portal before `certs` can make its profile.

## Build number and Xcode Cloud

Local builds and Xcode Cloud share one sequence on App Store Connect, but Xcode Cloud numbers builds by its own
run counter and does not look at App Store Connect. After a local build, set Xcode Cloud's next build number
(product settings → Build Number) above the latest, or its next upload fails as a duplicate.

## Timing

Archive 5–15 min depending on the app, upload 1–3 min, processing 5–30 min. Run `beta` in the background and
report when the build is `VALID` and in the groups.
