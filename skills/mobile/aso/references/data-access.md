# Pulling data

## Public — no login

App metadata per storefront (title, description, rating):
```
https://itunes.apple.com/lookup?id=<adam_id>&country=<cc>
```

Search results and total result count:
```
https://itunes.apple.com/search?term=<kw>&country=<cc>&entity=software&limit=200
```

Autocomplete suggestions (storefront via `X-Apple-Store-Front` header):
```
https://search.itunes.apple.com/WebObjects/MZSearchHints.woa/wa/hints?q=<term>&clientApplication=Software
```

The subtitle is not in the lookup API. It is the `<h2>` immediately after the `<h1>` on the
store HTML page.

Storefront header format is `<id>-<lang>,29`, e.g. US `143441-1,29`, VN `143471-2,29`,
JP `143462-9,29`. The Analytics API instead wants the bare id (`143441`).

## App Store Connect internal API `[VERIFIED]`

Undocumented and may break without notice. Run from the browser console while logged in.
`scripts/asc_pull.js` wraps this.

**The required header is `x-requested-by: appstoreconnect.apple.com`.** Without it every
request returns HTTP 400 with a generic "URL is invalid" message that suggests a wrong
path. This wastes a lot of time if you do not know it.

```js
fetch('/analytics/api/v1/data/timeseries', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'x-requested-by': 'appstoreconnect.apple.com'
  },
  body: JSON.stringify({
    adamId: ['<adam_id>'],
    startTime: '2026-07-06T00:00:00Z',   // full ISO datetime, a bare date is rejected
    endTime:   '2026-09-04T00:00:00Z',   // must not exceed available data
    measures: ['units'],                  // exactly ONE measure per call
    dimensionFilters: [{ dimensionKey: 'storefront', optionKeys: ['143471'] }],
    frequency: 'day'
  })
})
```

Gotchas, each of which produces the same unhelpful 400:
- more than one entry in `measures`
- a date without a time component
- an `endTime` beyond the last day with data

Useful measures: `units`, `proceeds`, `sales`, `impressionsTotalUnique`, `pageViewCount`,
`conversionRate`, `crashes`, `payingUsers`, `activeDevices`.

List available storefront ids:
```
POST /analytics/api/v1/data/dimension-values
{ adamId, startTime, endTime, dimensions:[{dimension:'storefront'}],
  measures:['units'], frequency:'day', dimensionFilters:[] }
```

Version metadata (title/subtitle live under `appInfos`, keywords under the version):
```
GET /iris/v1/appStoreVersions/<versionId>/appStoreVersionLocalizations?limit=50
GET /iris/v1/apps/<adamId>/appInfos
GET /iris/v1/appInfos/<appInfoId>/appInfoLocalizations?limit=50
```

## Revenue per download — the number that anchors paid spend

```
revenue_per_download = proceeds / units      (per storefront, per month)
```

This is the ceiling for any paid acquisition CPI in that market. Compute it before
evaluating Search Ads or Meta, not after.

Watch for a false tail: if monthly proceeds track that month's downloads rather than
compounding as the installed base grows, there is little recurring revenue and LTV is
close to first-month revenue. Test it — do not assume a subscription tail exists.
