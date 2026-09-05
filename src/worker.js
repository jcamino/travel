// travel.jcamino.net worker: serves ./public as static assets and adds a
// small JSON relay for the /ameya live-tracking page (the ADS-B aggregators
// send no CORS headers, and some rate-limit shared egress IPs, so we try
// several and cache the merged answer at the edge for a few seconds).

const UA = 'travel.jcamino.net/ameya (claude@jcamino.net)';
const JFK = { lat: 40.6413, lon: -73.7781 };
const SOURCES = [
  {
    name: 'adsb.lol',
    reg: (r) => `https://api.adsb.lol/v2/registration/${r}`,
    point: (lat, lon, d) => `https://api.adsb.lol/v2/point/${lat}/${lon}/${d}`,
  },
  {
    name: 'adsb.fi',
    reg: (r) => `https://opendata.adsb.fi/api/v2/registration/${r}`,
    point: (lat, lon, d) => `https://opendata.adsb.fi/api/v2/lat/${lat}/lon/${lon}/dist/${d}`,
  },
];

async function getJson(url) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), 6000);
  try {
    const r = await fetch(url, { headers: { 'user-agent': UA, accept: 'application/json' }, signal: ctl.signal });
    if (!r.ok) return { error: 'upstream ' + r.status };
    const j = await r.json();
    if (!j || !Array.isArray(j.ac)) return { error: 'bad shape' };
    return j;
  } catch (e) {
    return { error: String((e && e.message) || e) };
  } finally {
    clearTimeout(t);
  }
}

// Try each source in order until one answers with a usable list.
async function firstGood(kind, ...args) {
  const errors = [];
  for (const s of SOURCES) {
    const j = await getJson(s[kind](...args));
    if (!j.error) return { data: j, source: s.name, errors };
    errors.push(s.name + ': ' + j.error);
  }
  return { data: null, source: null, errors };
}

function slimAircraft(a) {
  if (!a) return null;
  return {
    hex: a.hex,
    type: a.t,
    alt: a.alt_baro,
    alt_geom: a.alt_geom,
    gs: a.gs,
    track: a.track,
    vs: a.baro_rate ?? a.geom_rate ?? null,
    lat: a.lat,
    lon: a.lon,
    squawk: a.squawk,
    seen: a.seen,
    seen_pos: a.seen_pos,
  };
}

function slimTraffic(d) {
  if (!d || !Array.isArray(d.ac)) return [];
  return d.ac
    .filter((a) => typeof a.alt_baro === 'number' && a.alt_baro < 3000 && typeof a.lat === 'number')
    .map((a) => ({
      flight: (a.flight || '').trim(),
      alt: a.alt_baro,
      gs: a.gs,
      track: a.track,
      vs: a.baro_rate ?? a.geom_rate ?? null,
      lat: a.lat,
      lon: a.lon,
    }));
}

async function buildState(reg) {
  const [ac, traffic] = await Promise.all([firstGood('reg', reg), firstGood('point', JFK.lat, JFK.lon, 8)]);
  const a = ac.data && ac.data.ac[0];
  return {
    now: Date.now(),
    reg,
    aircraft: slimAircraft(a),
    aircraft_source: ac.source,
    aircraft_error: ac.errors.length ? ac.errors.join('; ') : undefined,
    traffic: slimTraffic(traffic.data),
    traffic_source: traffic.source,
    traffic_error: traffic.errors.length ? traffic.errors.join('; ') : undefined,
  };
}

async function state(request, ctx, reg) {
  const cache = caches.default;
  const key = new Request('https://travel.jcamino.net/ameya/api/state?reg=' + reg, { method: 'GET' });
  const hit = await cache.match(key);
  if (hit) {
    const h = new Headers(hit.headers);
    h.set('x-relay-cache', 'hit');
    return new Response(hit.body, { status: hit.status, headers: h });
  }
  const body = await buildState(reg);
  const res = new Response(JSON.stringify(body), {
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'public, max-age=4, s-maxage=4',
      'access-control-allow-origin': '*',
      'x-relay-cache': 'miss',
    },
  });
  ctx.waitUntil(cache.put(key, res.clone()));
  return res;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/ameya/api/state') {
      const reg = (url.searchParams.get('reg') || 'N2884D').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8) || 'N2884D';
      return state(request, ctx, reg);
    }
    return env.ASSETS.fetch(request);
  },
};
