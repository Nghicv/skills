# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Build went live without QC | release type was `AFTER_APPROVAL` from an earlier submission | `submit` with an explicit `release:`; next time `manual`/`phased` |
| Build `VALID` but no tester sees it | Xcode Cloud build, in no group | `testers build:N` |
| Upload rejected: build number already used | local and Xcode Cloud numbering collided | rebuild with a higher number (`beta build:N`); move Xcode Cloud's next build number |
| `match` "Could not find profile" | `certs` never run for this bundle id, or profile expired | `certs` (with approval) |
| `match` asks for a passphrase | `MATCH_PASSWORD` not in `fastlane/.env` | add it |
| `requires a development team` on a Pods target | manual signing passed via `xcargs` | sign per target (`update_code_signing_settings`), as the Releasefile does |
| Export fails, exit 70 (Xcode Cloud) | extension App ID not registered, or `[sdk=iphoneos*]` override pins another profile | register the App ID; remove the overrides |
| Profile has no App Group | the API key cannot link groups | tick the group on the App ID in the portal, then `certs` |
| `xcodebuild` "Authentication failed: bearer token" | ASC key used for `-allowProvisioningUpdates` | use match profiles instead |
| `MISSING_EXPORT_COMPLIANCE` | no `ITSAppUsesNonExemptEncryption` | add the key; answer once in ASC for the stuck build |
| `submit`: build version ≠ store version | built before `new_version` | bump, commit, rebuild |
| `whats_new`: "No editable App Store version" | the version does not exist on ASC yet | `new_version version:x.y.z apply:true` |
| Crashes unsymbolicated | dSYMs not uploaded | `dsym build:N`; check the UUID with `dwarfdump --uuid` |
| `beta_cloud` started the wrong branch | runs cannot be cancelled by API | cancel in Xcode → Report navigator or App Store Connect → Xcode Cloud |
| Lane fails with "app not visible to this API key" | key of another team | use the app's own `<PREFIX>_ASC_*` key |
