// Dán vào DevTools console khi đang đăng nhập App Store Connect.
// Bắt buộc có header x-requested-by, thiếu là 400 với thông báo đánh lạc hướng.
//
//   await asoPull({ adamId: '1234567890', start: '2026-07-01', end: '2026-09-04' })

async function asoPull({ adamId, start, end, storefronts = null,
                         measures = ['units', 'proceeds', 'impressionsTotalUnique'] }) {
  const H = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'x-requested-by': 'appstoreconnect.apple.com'
  };
  const iso = d => (d.length === 10 ? d + 'T00:00:00Z' : d);

  async function series(measure, sfId) {
    const r = await fetch('/analytics/api/v1/data/timeseries', {
      method: 'POST', headers: H,
      body: JSON.stringify({
        adamId: [String(adamId)],
        startTime: iso(start), endTime: iso(end),
        measures: [measure],                       // đúng MỘT measure mỗi call
        dimensionFilters: sfId
          ? [{ dimensionKey: 'storefront', optionKeys: [String(sfId)] }] : [],
        frequency: 'day'
      })
    });
    if (!r.ok) return { error: r.status, body: (await r.text()).slice(0, 200) };
    const j = await r.json();
    const d = ((j.results || [])[0] || {}).data || [];
    return { total: d.reduce((s, p) => s + (p[measure] || 0), 0), daily: d };
  }

  const out = {};
  for (const sf of (storefronts || [null])) {
    const key = sf || 'ALL';
    out[key] = {};
    for (const m of measures) out[key][m] = await series(m, sf);
    const u = out[key].units?.total, p = out[key].proceeds?.total;
    if (u && p != null) out[key].revenue_per_download = +(p / u).toFixed(4);
  }
  console.table(Object.entries(out).map(([k, v]) => ({
    storefront: k, units: v.units?.total, proceeds: v.proceeds?.total,
    rev_per_dl: v.revenue_per_download
  })));
  return out;
}

// Liệt kê id storefront khả dụng
async function asoStorefronts({ adamId, start, end }) {
  const r = await fetch('/analytics/api/v1/data/dimension-values', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json',
               'x-requested-by': 'appstoreconnect.apple.com' },
    body: JSON.stringify({
      adamId: [String(adamId)],
      startTime: start + 'T00:00:00Z', endTime: end + 'T00:00:00Z',
      dimensions: [{ dimension: 'storefront' }], measures: ['units'],
      frequency: 'day', dimensionFilters: []
    })
  });
  const j = await r.json();
  return ((j.results || [])[0] || {}).values || [];
}
