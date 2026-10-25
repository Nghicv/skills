# TestFlight testers and groups

## A build is processed but nobody sees it

Check `release_status`: the build's internal state.

| Internal state | Meaning | Fix |
|---|---|---|
| `PROCESSING` | Apple is still processing | wait |
| `MISSING_EXPORT_COMPLIANCE` | no encryption answer | set `ITSAppUsesNonExemptEncryption` in Info.plist, answer it once for this build in ASC |
| `READY_FOR_BETA_TESTING` | in no group | `testers build:N` |
| `IN_BETA_TESTING` | testers have it | check the tester is in the group and accepted the invite |
| `EXPIRED` | 90 days old | new build |

Groups with "automatic distribution" (`has_access_to_all_builds`) receive builds uploaded with Xcode or fastlane,
but not builds from Xcode Cloud. Adding a build that is already in a group does nothing, so `testers` is safe to
re-run.

## Adding testers

- **Internal** (up to 100, no review): they must be App Store Connect users of the team. Invite them in Users and
  Access with a role, then add them to an internal group under TestFlight → Internal Testing. They get every build
  added to that group.
- **External** (up to 10,000, by email or public link): create an external group, add testers, add the build. The
  first build of each version goes through Beta App Review (usually under a day) before testers get it; later
  builds of the same version usually pass automatically.

Inviting or removing testers is an App Store Connect write: confirm with the user first.

## By API

- Add a build to a group: `POST /v1/betaGroups/{groupId}/relationships/builds` with
  `{"data":[{"type":"builds","id":"<buildId>"}]}`.
- A build's TestFlight state: `GET /v1/builds/{id}/buildBetaDetail` (`internalBuildState`, `externalBuildState`).
- Groups: `GET /v1/betaGroups?filter[app]=<appId>` (`isInternalGroup`, `hasAccessToAllBuilds`).
