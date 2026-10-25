# Build with Xcode Cloud (`beta_cloud`)

```bash
bundle exec fastlane ios beta_cloud               # main
bundle exec fastlane ios beta_cloud branch:foo    # must match the workflow's manual start conditions
```

## What the lane does

1. Finds the Xcode Cloud product of the app and the workflow named `RELEASE[:xcode_cloud_workflow]`.
2. Finds the branch among the repository's git references (it must be pushed).
3. `POST /v1/ciBuildRuns` starts the run. **A run cannot be cancelled from the API**, only from Xcode or App Store
   Connect, so make sure the branch and commit are right before starting.
4. Polls the run until `COMPLETE`; any `completionStatus` other than `SUCCEEDED` fails the lane.
5. Waits for the build (number = run number) to be `VALID`.
6. Adds it to every internal group: Xcode Cloud builds skip the groups' automatic distribution.
7. Downloads the run's archive artifact and uploads its dSYMs.

## Facts that bite

- The build number is the run number, shared by all workflows of the product. To find the run behind a build,
  search every workflow (`dsym build:N` does).
- The workflow must have a TestFlight/App Store distribution post-action and an App Store–eligible archive, or the
  build never reaches App Store Connect.
- Xcode Cloud does not upload dSYMs anywhere. Add `ci_scripts/ci_post_xcodebuild.sh` (template in this skill) so
  every archive uploads them, and keep the lane's upload as the second chance.
- `ci_scripts/ci_post_clone.sh` must install what is not in git (CocoaPods, generated code).
- Cloud-managed signing creates profiles for existing App IDs only. A new extension fails at export (exit 70)
  until its App ID is registered in the portal; also check the target has no `[sdk=iphoneos*]` signing overrides
  pinning another target's profile.
- The ASC API endpoints are `ciProducts`, `ciWorkflows`, `ciBuildRuns`, `ciBuildActions/{id}/artifacts`,
  `ciArtifacts/{id}` (`downloadUrl`). Use `scripts/asc.py` for anything the lane does not do.
