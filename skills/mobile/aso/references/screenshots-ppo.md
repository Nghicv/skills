# Screenshots, localization, and PPO

## Screenshots do not affect ranking

Apple does not index text inside images. Screenshots are a **conversion** lever only.
A screenshot change can never explain a rank change, and a keyword change can never
explain a conversion change. Keep the two analyses separate.

## Localized sets

Ordering by return on effort:

1. **Localize the store page at all** for markets where you already rank. Ranking in a
   market while showing English screenshots is the most common wasted opportunity.
2. **Match slides to the keywords you rank for.** If you place well for a feature, that
   feature needs a slide. See the coverage-gap section in `iterate.md`.
3. Aesthetic refinement — real, but smallest of the three.

## The IP gate — blocking

Every asset needs cleared provenance before submission: fonts, icons, stock media, music,
and any third-party brand or character.

`screenshots/manifest.yml` carries `ip_cleared: true|false` per slide.
`validate_metadata.py` fails if a set is marked submission-ready with any slide uncleared.

This exists because it is cheap to add a borrowed asset during design and very expensive to
discover it after the set is live in twelve locales.

## Images stay out of git

Store binaries outside the repo. The manifest holds path, checksum, source and IP status. A
repo that accumulated screenshot binaries needed a history rewrite to shed ~380MB, and a set
that lived only in an `exports/` folder was lost and had to be pulled back from Apple's CDN.

### Archive every release to Google Drive

Archive a **release folder** (the immutable set that was or will be uploaded, with its
manifest), never a working `exports/` folder that is overwritten on every export.

| Moment | Archive |
|---|---|
| A release folder is created | yes — the export it came from can vanish |
| A set is uploaded to App Store Connect / Play | yes, after updating its manifest status |
| A PPO treatment is promoted or stopped | re-run to push the updated manifest |

```bash
S="$(ls -d ~/.claude/skills/aso/scripts ~/.agents/skills/aso/scripts 2>/dev/null | head -1)"
python3 $S/drive_sync.py aso/ store-screenshots/releases/v4-light --dry-run
python3 $S/drive_sync.py aso/ store-screenshots/releases/v4-light store-screenshots/releases/v4-dark
```

The folder id comes from `screenshots.drive_folder` in `config.yml`. Each release becomes a
Drive folder of the same name with its tree mirrored. Re-running is safe: files with the same
MD5 are skipped, changed ones are overwritten in place (links keep working), nothing on Drive
is deleted. The last line prints the folder link; give it to the user. Run the per-locale image
count first: Drive will happily store a set that is missing images.

### Drive login (once per machine)

The script borrows gcloud's login, and a normal gcloud login has no Drive access. When it exits
with "no Drive scope" or "no usable login", stop and give the user these steps; only they can
do them, it is a browser sign-in.

1. In the Claude Code prompt, type this and press Enter (the leading `!` runs it in the session;
   `CLOUDSDK_PYTHON` is only needed where gcloud's bundled Python is broken):
   ```
   ! CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.14 gcloud auth login --enable-gdrive-access
   ```
2. A browser tab opens on Google sign-in. If none opens, copy the long
   `https://accounts.google.com/...` link the terminal prints into a browser.
3. Pick the Google account that can **edit** the Drive folder (its owner, or shared as Editor).
4. On "Google Cloud SDK wants to access your Google Account", tick every box, including
   "See, edit, create and delete all of your Google Drive files", then press **Continue**.
5. The tab says "You are now authenticated with the gcloud CLI!" and the terminal prints
   `You are now logged in as [email]`. The user tells you it is done.

That account becomes gcloud's active account. If gcloud normally runs as another account
(Firebase, GA4 impersonation), switch back with `gcloud config set account <usual>` and pass
the Drive one to the script with `--account <email>`. `gcloud auth list` shows who is logged in.

## Product Page Optimization (PPO)

Apple's built-in A/B test: up to 3 treatments against the original, traffic split evenly,
measured on conversion.

**Traffic requirements — check before starting, not after:**

| Daily product page views | What you can detect |
|---|---|
| < 500 | Struggles to reach significance in under 30 days for anything below a ~10% relative change; may need the full 90 |
| 2,000+ | ~5% relative change within about 2 weeks |

Rules:
- **Never read a result before day 14.** Early readings are noise.
- Most healthy tests settle at 14–30 days; small apps need longer, up to Apple's 90-day max.
- Statistical significance is not business impact. A significant +2% may not be worth a
  quarter of design effort.
- A treatment splitting traffic means most visitors see something other than your best
  asset for the duration. Factor that cost in for long tests.

If the app is well under 500 daily page views, PPO will likely not produce a trustworthy
answer. Say so before the test starts rather than analysing noise for three months.

## Sources

- https://appbot.co/blog/product-page-optimization/
- https://www.apptweak.com/en/aso-blog/product-page-optimization-a-guide-to-app-store-a-b-testing
