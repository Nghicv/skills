#!/bin/sh

# Xcode Cloud runs this after every xcodebuild action. Upload the archive's
# dSYMs to Crashlytics so crashes from TestFlight/App Store builds symbolicate.
# Never fails the build: a missed upload can be redone with
# bundle exec fastlane ios dsym build:<build number>.

if [ "$CI_XCODEBUILD_ACTION" != "archive" ] || [ ! -d "$CI_ARCHIVE_PATH/dSYMs" ]; then
    exit 0
fi

GSP=$(ls "$CI_ARCHIVE_PATH"/Products/Applications/*.app/GoogleService-Info.plist | head -1)

"$CI_PRIMARY_REPOSITORY_PATH/Pods/FirebaseCrashlytics/upload-symbols" -gsp "$GSP" -p ios "$CI_ARCHIVE_PATH/dSYMs" \
    || echo "warning: Crashlytics dSYM upload failed"

exit 0
