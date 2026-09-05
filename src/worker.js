// travel.jcamino.net worker: serves ./public as static assets and adds a
// small JSON proxy for the /ameya live-tracking page (adsb.lol has no CORS).

const UA = 'travel.jcamino.net/ameya (claude@jcamino.net)';
const JFK = { lat: 40.6413, lon: -73.7781 };

async function upstream(url, ttl) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), 7000);
  try {
    const r = await fetch(url, {
      headers: { 'user-agent': UA, accept: 'application/json' },
      signal: ctl.signal,
      cf: { cacheTtl: ttl, cacheEverything: true },
    });
    if (!r.ok) return { error: 'upstream ' + r.status };
    return await r.json();
  } catch (e) {
    return { error: String(e && e.message || e) };
  } finally {
    clearTimeout(t);
  }
}

function slimTraffic(d) {
  if (!d || !Array.isArray(d.ac)) return [];
  return d.ac
    .filter((a) => typeof a.alt_baro === 'number' && a.alt_baro < 3000)
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

async function state(reg) {
  const [ac, traffic] = await Promise.all([
    upstream('https://api.adsb.lol/v2/registration/' + encodeURIComponent(reg), 5),
    upstream(`https://api.adsb.lol/v2/point/${JFK.lat}/${JFK.lon}/8`, 15),
  ]);
  const a = ac && Array.isArray(ac.ac) && ac.ac[0];
  const body = {
    now: Date.now(),
    reg,
    aircraft: a
      ? {
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
        }
      : null,
    aircraft_error: ac && ac.error ? ac.error : undefined,
    traffic: slimTraffic(traffic),
    traffic_error: traffic && traffic.error ? traffic.error : undefined,
  };
  return new Response(JSON.stringify(body), {
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'public, max-age=5',
      'access-control-allow-origin': '*',
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/ameya/api/state') {
      const reg = (url.searchParams.get('reg') || 'N2884D').toUpperCase().slice(0, 8);
      return state(reg);
    }
    return env.ASSETS.fetch(request);
  },
};
