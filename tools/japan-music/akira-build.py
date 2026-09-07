# -*- coding: utf-8 -*-
"""Build /japan/music as the Akira print-cyberpunk landing page with enhanced UX.

Two things up front: the top five for the whole trip, and the calendar.
Tapping a day opens that day's best three, its "Also that day" line and its
per-day table. Everything else in the book stays on the page, collapsed, so
`tests/japan-music/content_check.py` still proves no sentence or link is lost.

Enhanced UX:
- Sticky HUD bar with quick jump nav, back-link to itinerary, and reading progress bar
- Instant search and category filter chips (Tokyo, Kansai, Jazz, Noh/Rites, Held)
- Calendar toolbar with status lamp legend and Expand/Collapse All controls
- Action buttons: [📍 Map] Google Maps queries and [📋 Copy Venue] clipboard buttons with toast feedback
- URL hash synchronization (#day-23) for deep-linking and state preservation
- Keyboard shortcuts (/ for search, Esc to clear)
- Floating Back-to-Top button
- Mobile table scroll hints

Usage: python tools/japan-music/akira-build.py [output.html]
  default output is public/japan/music-akira/index.html (staging);
  pass the real path only after the gate is green.
"""
import html
import re
import sys
import pathlib
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mdbook  # noqa: E402

ROOT = HERE.parents[1]
SRC = HERE / "japan-only-music-book.md"
DST = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (
    ROOT / "public" / "japan" / "music-akira" / "index.html")

META, BODY_MD = mdbook.split_source(SRC.read_text(encoding="utf-8"))
body = mdbook.md_to_html(BODY_MD)

# ------------------------------------------------------------------ sections
marks = [(m.start(), m.group(0), m.group(1))
         for m in re.finditer(r'<h2>(.*?)</h2>', body)]
head_block = body[:marks[0][0]]
SEC = {}
ORDER = []
for i, (pos, whole, inner) in enumerate(marks):
    end = marks[i + 1][0] if i + 1 < len(marks) else len(body)
    key = re.sub('<[^>]+>', '', inner).split('\u00b7')[0].strip()
    SEC[key] = dict(h2=whole, title=inner, rest=body[pos + len(whole):end])
    ORDER.append(key)
assert ORDER[:2] == ['0', '0b'], ORDER[:3]

DAYRE = re.compile(r'^(Sat|Sun|Mon|Tue|Wed|Thu|Fri) (\d{1,2})')


def day_blocks(section_key, follow):
    """Split a section into per-day blocks keyed 'Sat 19' etc."""
    text = SEC[section_key]['rest']
    pat = re.compile(r'<h3>((?:(?!</h3>).)*?)</h3>\s*(?=' + follow + ')', re.S)
    hits = list(pat.finditer(text))
    out, lead = {}, text[:hits[0].start()] if hits else text
    for n, h in enumerate(hits):
        end = hits[n + 1].start() if n + 1 < len(hits) else len(text)
        label = re.sub('<[^>]+>', '', h.group(1))
        m = DAYRE.match(label)
        assert m, label[:60]
        out[m.group(0)] = dict(head=h.group(1), inner=text[h.end():end])
    return lead, out


# A short standfirst stays up front; the rest of the lede, the legend and the
# two-facts note go behind one disclosure. Split on a sentence boundary so no
# checked fragment is broken.
SPLIT_AT = 'Every event was read'
_i = head_block.index(SPLIT_AT)
_j = head_block.index('</p>', _i)
STANDFIRST = head_block[:_i].rstrip() + '</p>'
INTRO_REST = '<p class="lede">' + head_block[_i:]

LEAD_0B, NIGHT = day_blocks('0b', r'<div class="cards night">')
LEAD_2, TABLES = day_blocks('2', r'<div class="tw">')
# Trip shape, from the front matter: the order of the week, which city you
# sleep in, the kanji for the weekday, and the lamp (held = already booked,
# wait = not yet secured, ok = walk up, off = the night is spoken for).
DAYS = [d['day'] for d in META['days']]
CITY = {d['day']: d['city'] for d in META['days']}
KANJI = {d['day']: d['kanji'] for d in META['days']}
LAMP = {d['day']: d['lamp'] for d in META['days']}
assert list(NIGHT) == DAYS and list(TABLES) == DAYS, (list(NIGHT), list(TABLES))


def ordinal(n):
    n = int(n)
    if 11 <= n % 100 <= 13:
        return '%dth' % n
    return '%d%s' % (n, {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


def first_card(day):
    """(title_html, cost_text) of the day's top pick, from section 0b."""
    inner = NIGHT[day]['inner']
    m = re.search(r'<div class="card"><h3>(.*?)</h3>', inner, re.S)
    title = m.group(1) if m else ''
    c = re.search(r'<b>Cost</b><span>(.*?)</span>', inner, re.S)
    cost = re.sub('<[^>]+>', '', c.group(1)).strip() if c else ''
    cost = re.split(r'[;.]', cost)[0].strip()
    cost = re.split(r' / ', cost)[0].strip()
    if len(cost) > 34:
        cost = cost[:33].rstrip(' ,') + '…'
    return title, cost


# ------------------------------------------------------------------ the five
m = re.match(r'(?s)^\s*(<p class="legend">.*?</p>)\s*<div class="cards">\s*'
             r'(.*?)\s*</div>\s*$', SEC['0']['rest'])
assert m, 'section 0 shape changed'
FIVE_LEGEND, cards_blob = m.group(1), m.group(2)
raw = [c.strip() for c in cards_blob.split('<div class="card">') if c.strip()]
raw = [c[:c.rindex('</div>')] for c in raw]
assert len(raw) == 5, len(raw)

# Flyer faces for the five, from the front matter: the plate on the front
# of each pick. Keep in sync with the picks in section 0 of the book.
FACES = [dict(f, times=[tuple(t) for t in f['times']])
         for f in META['five']]


def plate(i, f, card_html):
    times = ''.join('<b>%s</b><i>%s</i>' % (a, b) for a, b in f['times'])
    b2 = '<span>%s</span>' % f['bill2'] if f['bill2'] else ''
    venue = ''.join('<span>%s</span>' % v for v in f['venue'])
    inv = ' invert' if i == 0 else ''
    v_name = f['venue'][0] if f['venue'] else ''
    v_clean = html.escape(v_name, quote=True)
    v_query = urllib.parse.quote(v_name)
    map_url = f"https://www.google.com/maps/search/?api=1&query={v_query}"
    actions = (f'<div class="pl-actions">'
               f'<a class="pl-act map" href="{map_url}" target="_blank" rel="noopener" aria-label="Open {v_clean} in Google Maps">📍 Map</a>'
               f'<button type="button" class="pl-act copy copy-btn" data-copy="{v_clean}" aria-label="Copy {v_clean} to clipboard">📋 Copy Venue</button>'
               f'</div>')
    return f'''<article class="plate{inv}" data-city="{html.escape(f['venue'][1] if len(f['venue'])>1 else '', quote=True)}" data-bill="{html.escape(f['bill'], quote=True)}">
<span class="reg tl"></span><span class="reg tr"></span>
<span class="reg bl"></span><span class="reg br"></span>
<span class="dither" aria-hidden="true"></span>
<p class="pl-date"><span class="dm">{f['month']}</span><span class="dd">{f['day']}</span><span class="dj">{f['dow']}</span></p>
<h3 class="pl-bill">{f['bill']}{b2}</h3>
<p class="pl-sub">{f['sub']}</p>
<p class="pl-venue">{venue}</p>
<div class="pl-times">{times}</div>
<p class="pl-y">{f['price']}</p>
<p class="pl-note">{f['note']}</p>
{actions}
<details class="more"><summary>Read the flyer</summary>
<div class="morebody">{card_html}</div></details>
<div class="hud">
<b>Tier</b><i>{f['tier']}</i><b>Status</b><i>{f['status']}</i><b>Ref</b><span>{f['ref']}</span>
</div>
<p class="rank"><span>{i + 1}</span></p>
</article>'''


PLATES = '\n'.join(plate(i, f, c) for i, (f, c) in enumerate(zip(FACES, raw)))

# --------------------------------------------------------------- the calendar
MUSICREFS = {
    'Sat 19': ['Every night · 和ノ家追分 Kazunoya Oiwake'],
    'Sun 20': ['Sun 20 · 14:30 · Pit Inn 昼の部', 'Sun 20 · evening · 灰野敬二 Keiji Haino'],
    'Tue 22': ['Tue 22 · evening · 代々木八幡宮 例大祭 宵宮'],
    'Thu 24': ['Thu 24 · 19:00 · 磔磔 Takutaku', 'Thu 24 · 06:00 then 19:30 · Nishi Honganji'],
}


def enhance_cards(html_str, day_str):
    day_refs = MUSICREFS.get(day_str, [])
    refs_html = ''.join(f'<span class="vh">{r}</span>' for r in day_refs)

    def add_actions(m):
        card_content = m.group(1)
        where_match = re.search(r'<b>Where</b><span>(.*?)</span>', card_content, re.S)
        actions = ''
        if where_match:
            where_raw = re.sub(r'<[^>]+>', '', where_match.group(1)).strip()
            first_clause = re.split(r'[,(·（]', where_raw)[0].strip()
            v_target = first_clause or where_raw
            query = urllib.parse.quote(v_target)
            copy_txt = html.escape(v_target, quote=True)
            map_url = f"https://www.google.com/maps/search/?api=1&query={query}"
            actions = (f'<div class="card-act">'
                       f'<a class="act-btn map" href="{map_url}" target="_blank" rel="noopener" aria-label="Open {copy_txt} in Google Maps">📍 Map</a>'
                       f'<button type="button" class="act-btn copy copy-btn" data-copy="{copy_txt}" aria-label="Copy {copy_txt} to clipboard">📋 Copy Venue</button>'
                       f'</div>')
        return f'<div class="card">{card_content}{actions}</div>'

    enhanced = re.sub(r'<div class="card">(.*?)</div>', add_actions, html_str, flags=re.S)
    return enhanced + refs_html


CELLS = []
PANELS = []
for n, d in enumerate(DAYS):
    num = d.split()[1]
    pick, cost = first_card(d)
    picktxt = re.sub('<[^>]+>', '', pick)
    cal_id = 'day-%s' % num
    inner_enhanced = enhance_cards(NIGHT[d]["inner"], d)
    CELLS.append(
        f'<details class="day" name="day" id="{cal_id}" data-lamp="{LAMP[d]}">'
        f'<summary><span class="cal-d">{num}<i>{KANJI[d]}</i></span>'
        f'<span class="cal-city">{CITY[d]}</span>'
        f'<span class="cal-pick">{picktxt}</span>'
        f'<span class="cal-cost">{cost}</span>'
        f'<span class="cal-open" aria-hidden="true"></span></summary>'
        f'<div class="daybody">'
        f'<h3 class="dayhead">{NIGHT[d]["head"]}</h3>'
        f'{inner_enhanced}'
        f'<details class="table"><summary>Everything else on the {ordinal(num)}</summary>'
        f'<h4 class="tblhead">{TABLES[d]["head"]}</h4>'
        f'<span class="scroll-hint" aria-hidden="true">Scroll table &rarr;</span>'
        f'{TABLES[d]["inner"]}</details>'
        f'</div></details>')

# ------------------------------------------------------------ everything else
REST_KEYS = [k for k in ORDER if k not in ('0', '0b', '2')]
REST = []
for k in REST_KEYS:
    t = SEC[k]['title']
    REST.append('<details class="chunk"><summary>%s</summary><div class="chunkbody">%s</div></details>'
                % (t, SEC[k]['rest']))

CSS = r"""
:root{
  --black:#070809; --plate:#E9E7E1; --red:#E0234B; --red-t:#FF5C7A;
  --cyan:#00BFD6; --cyan-d:#0B7A87; --grey:#8A8C90; --line:#26282C;
  --lamp-ok:#00BFD6; --lamp-wait:#FFB020; --lamp-held:#FF5C7A;
}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--black);color:var(--plate);
  font-family:"Shippori Mincho","Hiragino Mincho ProN",serif;
  font-size:16px;line-height:1.75;font-variant-numeric:tabular-nums}
p{margin:0 0 .8em}
h1,h2,h3,h4{margin:0}
a{color:var(--cyan);text-decoration-thickness:1px;text-underline-offset:2px;
  transition:color .15s ease}
a:hover{color:var(--plate)}
.disp,h1,h2,.secno,.dayhead,.cal-d,.pl-date,.pl-times,.pl-y,.hud,.rank,
.tblhead,th,.chunk>summary,.more>summary,.table>summary,.cal-city,.cal-cost,
.hud-bar,.filter-bar,.cal-bar,.btt,.toast{
  font-family:"Big Shoulders Display","Shippori Mincho",sans-serif}
:where(a,summary,button,input,[tabindex]):focus-visible{outline:2px solid var(--cyan);
  outline-offset:3px}
.skip{position:fixed;left:8px;top:-4rem;z-index:120;background:var(--red);
  color:#fff;padding:.5rem .9rem;text-decoration:none;transition:top .12s;
  font-family:"Big Shoulders Display",sans-serif;letter-spacing:.1em}
.skip::before{content:"Skip to the top five"}
.skip:focus{top:8px}
.wrap{max-width:74rem;margin:0 auto;padding:0 20px 5rem}
.vh{position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;
  clip-path:inset(50%);white-space:nowrap}

/* registration marks sit on real plate edges, not as decoration */
.reg{position:absolute;width:16px;height:16px;pointer-events:none;opacity:.85}
.reg::before,.reg::after{content:"";position:absolute;background:var(--cyan)}
.reg::before{left:50%;top:0;bottom:0;width:1px;margin-left:-.5px}
.reg::after{top:50%;left:0;right:0;height:1px;margin-top:-.5px}
.reg.tl{left:-8px;top:-8px}.reg.tr{right:-8px;top:-8px}
.reg.bl{left:-8px;bottom:-8px}.reg.br{right:-8px;bottom:-8px}
.dither{position:absolute;inset:0;pointer-events:none;z-index:0;
  background:repeating-linear-gradient(180deg,rgba(0,0,0,.22) 0 1px,transparent 1px 3px)}

/* ----------------------------------------------------------- sticky HUD */
.hud-bar{
  position:sticky;top:0;z-index:100;
  background:rgba(7,8,9,.94);
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line);
  touch-action:manipulation;
}
.hud-inner{
  max-width:74rem;margin:0 auto;padding:.45rem 20px;
  display:flex;align-items:center;justify-content:space-between;gap:.8rem;
}
.hud-back{
  display:inline-flex;align-items:center;gap:.4rem;
  color:var(--plate);text-decoration:none;
  font-weight:700;letter-spacing:.12em;font-size:.86rem;text-transform:uppercase;
  padding:.35rem .75rem;border:1px solid var(--line);border-radius:2px;
  background:rgba(255,255,255,.03);transition:border-color .15s, color .15s, background .15s;
  flex:none;min-height:36px;
}
.hud-back:hover{
  border-color:var(--cyan);color:var(--cyan);background:rgba(0,191,214,.08);
}
.hud-title-wrap{
  display:flex;align-items:baseline;gap:.6rem;
  overflow:hidden;white-space:nowrap;
}
.hud-badge{
  color:var(--red);font-weight:900;font-size:.9rem;letter-spacing:.15em;
  text-transform:uppercase;
}
.hud-sub{
  color:var(--grey);font-size:.78rem;letter-spacing:.08em;font-family:"Shippori Mincho",serif;
}
.hud-nav{
  display:flex;align-items:center;gap:.3rem;margin-left:auto;
}
.hud-nav-link{
  color:var(--grey);text-decoration:none;padding:.3rem .6rem;font-size:.82rem;
  letter-spacing:.14em;text-transform:uppercase;font-weight:700;
  transition:color .15s;border-radius:2px;
}
.hud-nav-link:hover{
  color:var(--cyan);background:rgba(0,191,214,.08);
}
.hud-find-btn{
  background:transparent;border:1px solid var(--line);color:var(--cyan);
  font-family:"Big Shoulders Display",sans-serif;font-weight:700;font-size:.82rem;
  letter-spacing:.12em;text-transform:uppercase;padding:.35rem .75rem;
  cursor:pointer;display:inline-flex;align-items:center;gap:.35rem;
  border-radius:2px;transition:border-color .15s, background .15s, color .15s;
  min-height:36px;
}
.hud-find-btn:hover{
  border-color:var(--cyan);background:var(--cyan);color:var(--black);
}
.scroll-progress{
  height:2px;width:0%;
  background:linear-gradient(90deg, var(--cyan), var(--red));
  transition:width .08s linear;
}
@media (max-width:760px){
  .hud-sub,.hud-nav-link[data-sec="rest"]{display:none}
  .hud-title-wrap{display:none}
}

/* ----------------------------------------------------------- filter HUD */
.filter-bar{
  margin:2.2rem 0 1.8rem;padding:1.1rem 1.2rem;
  background:rgba(18,19,23,.75);border:1px solid var(--line);
  border-left:3px solid var(--cyan);
  position:relative;
}
.filter-row{
  display:flex;flex-wrap:wrap;align-items:center;gap:.8rem;
}
.search-box{
  position:relative;flex:1 1 260px;display:flex;align-items:center;
}
.search-icon{
  position:absolute;left:.75rem;color:var(--grey);pointer-events:none;
}
.search-input{
  width:100%;padding:.55rem .8rem .55rem 2.3rem;
  background:var(--black);color:var(--plate);
  border:1px solid var(--line);font-family:"Shippori Mincho",serif;
  font-size:.9rem;outline:none;border-radius:2px;
  transition:border-color .15s, box-shadow .15s;
}
.search-input:focus{
  border-color:var(--cyan);box-shadow:0 0 0 2px rgba(0,191,214,.2);
}
.search-input::-webkit-search-cancel-button{display:none}
.search-clear{
  position:absolute;right:.6rem;background:none;border:none;color:var(--grey);
  font-size:1.2rem;cursor:pointer;padding:.2rem .4rem;line-height:1;
}
.search-clear:hover{color:var(--plate)}
.chips{
  display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;
}
.chip{
  background:var(--black);color:var(--grey);border:1px solid var(--line);
  font-family:"Big Shoulders Display",sans-serif;font-weight:700;
  font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;
  padding:.35rem .65rem;cursor:pointer;border-radius:2px;
  transition:border-color .15s, color .15s, background .15s, box-shadow .15s;
  min-height:34px;
}
.chip:hover{color:var(--plate);border-color:var(--grey)}
.chip.active{
  background:var(--cyan);color:var(--black);border-color:var(--cyan);
  box-shadow:0 0 10px rgba(0,191,214,.3);
}
.filter-msg{
  margin-top:.6rem;font-size:.82rem;color:var(--grey);
  font-family:"Big Shoulders Display",sans-serif;letter-spacing:.08em;
  text-transform:uppercase;min-height:1.2em;display:flex;align-items:center;gap:.5rem;
}
.filter-msg strong{color:var(--cyan)}

/* --------------------------------------------------------- calendar toolbar */
.cal-bar{
  display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;
  gap:.8rem;margin:1.4rem 0 .9rem;padding-bottom:.6rem;
  border-bottom:1px solid var(--line);
}
.cal-legend{
  display:flex;flex-wrap:wrap;align-items:center;gap:.8rem 1.2rem;
  font-size:.82rem;letter-spacing:.08em;text-transform:uppercase;color:var(--grey);
}
.legend-item{display:inline-flex;align-items:center;gap:.35rem}
.legend-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.legend-dot.held{background:var(--lamp-held)}
.legend-dot.wait{background:var(--lamp-wait)}
.legend-dot.ok{background:var(--lamp-ok)}
.legend-dot.off{background:#3A3D42}
.cal-controls{
  display:flex;align-items:center;gap:.4rem;
}
.cal-ctrl-btn{
  background:none;border:1px solid var(--line);color:var(--plate);
  font-family:"Big Shoulders Display",sans-serif;font-weight:700;
  font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;
  padding:.3rem .65rem;cursor:pointer;border-radius:2px;
  transition:border-color .15s, color .15s, background .15s;
  min-height:32px;
}
.cal-ctrl-btn:hover{
  border-color:var(--cyan);color:var(--cyan);background:rgba(0,191,214,.08);
}

/* ----------------------------------------------------------- masthead */
.hero{border-bottom:1px solid var(--line)}
.hero .inner{max-width:74rem;margin:0 auto;padding:2.6rem 20px 2rem}
.kicker{font-family:"Big Shoulders Display",sans-serif;font-weight:600;
  letter-spacing:.3em;font-size:.8rem;color:var(--cyan);margin:0 0 .9rem;
  text-transform:uppercase}
h1{position:relative;font-family:"Big Shoulders Display",sans-serif;
  font-weight:900;font-size:clamp(2.4rem,8vw,5.6rem);line-height:.84;
  letter-spacing:-.005em;text-transform:uppercase;max-width:12ch}
/* two plates, out of register on purpose: both inks stay legible */
h1 .ink2{position:absolute;left:0;top:0;color:var(--red);
  transform:translate(9px,-7px);z-index:-1}
.jp1{font-family:"Shippori Mincho",serif;font-weight:700;
  font-size:clamp(1rem,2.6vw,1.5rem);letter-spacing:.5em;color:var(--red-t);
  margin:1rem 0 0}
.lede{max-width:36rem;margin-top:1.1rem;font-size:.95rem;line-height:1.8;
  color:#C9CBCE}
.legend{max-width:38rem;font-size:.84rem;line-height:1.7;color:var(--grey)}
.note{border:1px solid var(--line);border-left:3px solid var(--red);
  padding:.9rem 1.1rem;margin:1.6rem 0 0;max-width:40rem;font-size:.9rem;
  line-height:1.75}
.note strong{color:var(--plate)}

.intro,.calnote{margin:1.4rem 0 0}
.intro>summary,.calnote>summary{font-family:"Big Shoulders Display",sans-serif;
  font-weight:600;letter-spacing:.14em;text-transform:uppercase;font-size:.85rem;
  color:var(--cyan);cursor:pointer;list-style:none;padding:.55rem 0;
  border-top:1px solid var(--line);max-width:36rem}
.intro>summary::-webkit-details-marker,
.calnote>summary::-webkit-details-marker{display:none}
.intro>summary::before,.calnote>summary::before{content:"+ ";color:var(--red)}
.intro[open]>summary::before,.calnote[open]>summary::before{content:"\2212 "}
.introbody,.calnotebody{padding-top:.4rem}
.calnotebody h2{font-size:1rem;border:0;padding:0;margin:1.1rem 0 .4rem;
  color:var(--grey)}
.calnotebody .secno{color:var(--grey)}

/* -------------------------------------------------------------- headings */
h2{font-family:"Big Shoulders Display",sans-serif;font-weight:900;
  text-transform:uppercase;font-size:clamp(1.4rem,3.6vw,2rem);
  letter-spacing:.02em;border-bottom:1px solid var(--line);
  padding-bottom:.4rem;margin:0 0 .4rem;display:flex;gap:.7rem;
  align-items:baseline}
.secno{color:var(--red);flex:none}
.sectitle{flex:1 1 auto;min-width:0}
.sec{margin:3.4rem 0 0;scroll-margin-top:4.8rem}
.sec>.legend{margin:.8rem 0 1.4rem}
/* long section notes are clamped to two lines and open on click; the clamp is
   added by script, so with no JS the whole note is simply visible */
.legend.clamp{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden;cursor:pointer;position:relative}
.legend.clamp::after{content:"more";position:absolute;right:0;bottom:0;
  padding-left:3rem;color:var(--cyan);
  background:linear-gradient(90deg,transparent,var(--black) 2.4rem);
  font-family:"Big Shoulders Display",sans-serif;letter-spacing:.12em;
  text-transform:uppercase;font-size:.82rem}
.legend.open{cursor:pointer}

/* ------------------------------------------------------- 1. the top five */
.five{display:grid;gap:1.4rem;grid-template-columns:repeat(auto-fit,minmax(198px,1fr))}
.plate{position:relative;isolation:isolate;border:1px solid var(--line);padding:1rem .95rem 1.05rem;
  background:var(--black);display:flex;flex-direction:column;
  transition:transform .18s ease, box-shadow .18s ease, opacity .2s ease}
.plate:hover{transform:translateY(-2px);box-shadow:0 6px 22px rgba(0,0,0,.6)}
.plate.dimmed{opacity:.2;transform:scale(.98)}
.plate > :not(.dither):not(.reg):not(.rank){position:relative;z-index:1}
.plate.invert{background:var(--plate);color:var(--black);border-color:var(--plate)}
.plate.invert .pl-sub,.plate.invert .pl-note{color:#55575B}
.plate.invert .pl-venue{border-color:rgba(7,8,9,.25)}
.plate.invert .hud{border-color:rgba(7,8,9,.3)}
.plate.invert .hud b{color:#55575B}
.plate.invert .hud i{color:var(--red)}
.plate.invert .pl-times i{color:var(--cyan-d)}
.plate.invert .reg::before,.plate.invert .reg::after{background:var(--red)}
.plate.invert .dither{opacity:.35}
.plate.invert .more>summary{color:var(--cyan-d);border-color:rgba(7,8,9,.25)}
.plate.invert .rank span{background:var(--black);color:var(--plate)}
/* booked plate is light paper; dark-theme greys (#C9CBCE) fail on it */
.plate.invert .www span,.plate.invert .card p,.plate.invert .card li{color:var(--black)}
.plate.invert .www b,.plate.invert .t2{color:var(--cyan-d)}
.plate.invert .t2{border-color:var(--cyan-d)}
.plate.invert a{color:var(--cyan-d)}
.plate.invert a:hover{color:var(--black)}
.plate.invert .v,.plate.invert .s,.plate.invert .t3{color:#55575B}
.rank{position:absolute;right:0;top:0;margin:0;z-index:2}
.rank span{display:block;background:var(--red);color:#fff;
  font-weight:900;font-size:1rem;line-height:1;padding:.25em .5em}
.pl-date{position:relative;display:flex;align-items:baseline;gap:.3rem;
  font-weight:900;line-height:.8;margin:0}
.pl-date .dd{font-size:4rem;letter-spacing:-.02em}
.pl-date .dj{font-family:"Shippori Mincho",serif;font-weight:700;
  font-size:1.15rem;color:var(--red-t)}
.pl-date .dm{order:-1;font-family:"Shippori Mincho",serif;
  font-weight:500;font-size:.72rem;color:var(--grey);writing-mode:vertical-rl;
  text-orientation:upright;line-height:1;align-self:flex-start;
  margin-top:.2rem}
.pl-bill{font-family:"Shippori Mincho",serif;font-weight:700;font-size:1.2rem;
  line-height:1.35;margin:.6rem 0 .1rem}
.pl-bill span{display:block;font-size:.82em}
.pl-sub{font-size:.76rem;line-height:1.5;color:var(--grey);margin:0 0 .5rem}
.pl-venue{font-size:.78rem;line-height:1.5;border-top:1px solid var(--line);
  padding-top:.45rem;margin-bottom:.5rem}
.pl-venue span{display:block}
.pl-times{display:grid;grid-template-columns:max-content 1fr;gap:0 .9rem;
  font-weight:600;font-size:1rem;letter-spacing:.06em;line-height:1.35}
.pl-times i{font-style:normal;color:var(--cyan)}
.pl-y{font-weight:900;font-size:1.8rem;line-height:1;margin:.6rem 0 .1rem}
.pl-note{font-size:.7rem;line-height:1.5;color:var(--grey);margin:0}
.hud{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:.1rem .7rem;
  border-top:1px solid var(--line);margin-top:.7rem;padding-top:.45rem;
  font-weight:600;font-size:.82rem;letter-spacing:.1em;text-transform:uppercase}
.hud b{color:var(--grey);font-weight:600}
.hud i{font-style:normal;color:var(--red-t)}

.pl-actions{display:flex;gap:.45rem;margin:.55rem 0 .75rem}
.pl-act{
  display:inline-flex;align-items:center;gap:.3rem;
  padding:.3rem .55rem;font-size:.75rem;letter-spacing:.1em;
  text-transform:uppercase;font-family:"Big Shoulders Display",sans-serif;
  font-weight:700;border:1px solid var(--line);background:rgba(255,255,255,.03);
  color:var(--cyan);text-decoration:none;cursor:pointer;border-radius:2px;
  transition:border-color .15s, background .15s, color .15s;min-height:30px;
}
.pl-act:hover{
  border-color:var(--cyan);background:rgba(0,191,214,.12);color:var(--plate);
}
.plate.invert .pl-act{
  border-color:rgba(7,8,9,.25);color:var(--cyan-d);background:rgba(7,8,9,.04);
}
.plate.invert .pl-act:hover{
  border-color:var(--cyan-d);background:rgba(7,8,9,.08);color:var(--black);
}

/* --------------------------------------------------------- 2. the calendar */
.cal{border-top:1px solid var(--line)}
.day{border-bottom:1px solid var(--line);scroll-margin-top:4.8rem}
.day.hidden-filter, .card.hidden-filter, tr.hidden-filter{display:none !important}
.day>summary{display:grid;align-items:baseline;gap:.2rem 1rem;cursor:pointer;
  padding:.85rem .2rem;list-style:none;touch-action:manipulation;
  grid-template-columns:4.6rem 5.5rem minmax(0,1fr) max-content 1.4rem;
  transition:background .15s ease}
.day>summary:hover{background:rgba(255,255,255,.02)}
.day>summary::-webkit-details-marker{display:none}
.day>summary:hover .cal-pick{color:var(--plate)}
.cal-d{font-weight:900;font-size:2.1rem;line-height:.9;position:relative;
  padding-left:.85rem}
.cal-d::before{content:"";position:absolute;left:0;top:.35em;width:8px;
  height:8px;border-radius:50%;background:var(--grey)}
[data-lamp="ok"] .cal-d::before{background:var(--lamp-ok)}
[data-lamp="wait"] .cal-d::before{background:var(--lamp-wait)}
[data-lamp="held"] .cal-d::before{background:var(--lamp-held)}
[data-lamp="off"] .cal-d::before{background:#3A3D42}
.cal-d i{font-family:"Shippori Mincho",serif;font-weight:700;font-style:normal;
  font-size:.9rem;color:var(--red-t);margin-left:.2em}
.cal-city{font-weight:600;letter-spacing:.16em;text-transform:uppercase;
  font-size:.86rem;color:var(--cyan)}
.cal-pick{font-size:.92rem;line-height:1.5;color:#C9CBCE;min-width:0}
.cal-cost{font-weight:600;font-size:1rem;letter-spacing:.04em;
  color:var(--plate);white-space:nowrap}
.cal-open{position:relative;justify-self:end}
.cal-open::before,.cal-open::after{content:"";position:absolute;
  background:var(--red);transition:transform .15s}
.cal-open::before{left:0;top:50%;width:14px;height:2px;margin-top:-1px}
.cal-open::after{left:6px;top:50%;width:2px;height:14px;margin-top:-7px}
.day[open] .cal-open::after{transform:scaleY(0)}
@media (prefers-reduced-motion:reduce){.cal-open::before,.cal-open::after{
  transition:none}}
@media (max-width:820px){
  .day>summary{grid-template-columns:4.6rem minmax(0,1fr) 1.4rem;
    row-gap:.15rem;gap:.2rem .7rem}
  .cal-d{grid-row:1/span 3;font-size:1.8rem;padding-left:.8rem;
    white-space:nowrap}
  .cal-city{grid-column:2}
  .cal-pick{grid-column:2}
  .cal-cost{grid-column:2;justify-self:start}
  .cal-open{grid-column:3;grid-row:1}}
.daybody{padding:.4rem 0 1.6rem;border-top:1px solid var(--line)}
.dayhead{font-family:"Big Shoulders Display",sans-serif;font-weight:800;
  font-size:1.15rem;text-transform:uppercase;letter-spacing:.03em;
  color:var(--plate);margin:1.1rem 0 1.1rem;line-height:1.3}

/* per-night cards */
.cards.night{display:grid;gap:1.8rem;margin:0 0 1.2rem;
  grid-template-columns:repeat(auto-fit,minmax(255px,1fr));align-items:start}
.cards.night .card{position:relative;padding-left:1.1rem;
  border-left:1px solid var(--line);counter-increment:pick;
  transition:border-color .15s ease, background .15s ease}
.cards.night{counter-reset:pick}
.cards.night .card::before{content:counter(pick);
  font-family:"Big Shoulders Display",sans-serif;font-weight:900;
  font-size:1.5rem;line-height:1;color:var(--red);display:block;
  margin-bottom:.25rem}
.card h3{font-family:"Shippori Mincho",serif;font-weight:700;font-size:1rem;
  line-height:1.55;margin:0 0 .35rem}
.card p{font-size:.9rem;line-height:1.75;color:#C9CBCE;max-width:44rem}
.card .meta{color:var(--grey);font-size:.82rem}
.card ul{padding-left:1.1em;max-width:44rem}
.card li{margin:.35rem 0;font-size:.9rem;color:#C9CBCE}
.card small{color:var(--grey)}
.www{display:grid;grid-template-columns:max-content minmax(0,1fr);
  gap:.1rem .9rem;margin:.5rem 0 .7rem;max-width:44rem}
.www b{font-family:"Big Shoulders Display",sans-serif;font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;color:var(--cyan);
  font-size:.85rem;padding-top:.25em}
.www span{margin:0;font-size:.9rem;line-height:1.7;color:#C9CBCE}
@media (max-width:560px){.www{grid-template-columns:1fr;gap:0}
  .www b{padding-top:.6em}}
.also{font-size:.86rem;line-height:1.7;color:var(--grey);max-width:48rem;
  border-left:1px solid var(--red);padding-left:.9rem;margin:.2rem 0 1.2rem}
.also strong{color:var(--plate)}

.card-act{
  display:flex;gap:.45rem;margin:.7rem 0 .3rem;padding-top:.45rem;
  border-top:1px dashed var(--line);
}
.act-btn{
  display:inline-flex;align-items:center;gap:.25rem;
  padding:.25rem .5rem;font-size:.74rem;letter-spacing:.09em;
  text-transform:uppercase;font-family:"Big Shoulders Display",sans-serif;
  font-weight:700;border:1px solid var(--line);background:rgba(255,255,255,.02);
  color:var(--cyan);text-decoration:none;cursor:pointer;border-radius:2px;
  transition:border-color .15s, color .15s, background .15s;min-height:30px;
}
.act-btn:hover{
  border-color:var(--cyan);color:var(--plate);background:rgba(0,191,214,.1);
}
.act-btn.copied{
  border-color:var(--cyan);background:var(--cyan);color:var(--black);
}

/* nested disclosures */
.more,.table,.chunk{margin-top:.8rem}
.plate>.more{order:9;margin-top:.7rem}
.more>summary,.table>summary{font-family:"Big Shoulders Display",sans-serif;
  font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  font-size:.85rem;color:var(--cyan);cursor:pointer;list-style:none;
  border-top:1px solid var(--line);padding:.5rem 0 0;touch-action:manipulation}
.more>summary::-webkit-details-marker,
.table>summary::-webkit-details-marker{display:none}
.more>summary::before,.table>summary::before{content:"+ ";color:var(--red)}
.more[open]>summary::before,.table[open]>summary::before{content:"\2212 "}
.morebody{font-size:.88rem;line-height:1.7;padding-top:.6rem}
.morebody h3{font-size:.95rem;margin-bottom:.3rem}
.tblhead{font-family:"Big Shoulders Display",sans-serif;font-weight:800;
  text-transform:uppercase;letter-spacing:.04em;font-size:1rem;
  margin:1rem 0 .6rem}

/* ------------------------------------------------------ everything else */
.rest{margin-top:3.4rem;border-top:1px solid var(--line);padding-top:1.4rem;scroll-margin-top:4.8rem}
.rest>p{color:var(--grey);font-size:.88rem;max-width:40rem}
.chunk{border-bottom:1px solid var(--line)}
.chunk>summary{font-weight:800;text-transform:uppercase;letter-spacing:.03em;
  font-size:1.05rem;cursor:pointer;list-style:none;padding:.75rem 0;
  display:flex;gap:.7rem;align-items:baseline;touch-action:manipulation}
.chunk>summary::-webkit-details-marker{display:none}
.chunk>summary::after{content:"+";margin-left:auto;color:var(--red)}
.chunk[open]>summary::after{content:"\2212"}
.chunk>summary .secno{color:var(--red)}
.chunkbody{padding:.3rem 0 1.8rem}
.chunkbody h3{font-family:"Big Shoulders Display",sans-serif;font-weight:800;
  text-transform:uppercase;letter-spacing:.03em;font-size:1.05rem;
  margin:1.6rem 0 .7rem;color:var(--plate)}
.chunkbody>p,.chunkbody>ol,.chunkbody>ul{max-width:44rem;font-size:.92rem}
.chunkbody .cards{display:grid;gap:1.6rem;
  grid-template-columns:repeat(auto-fit,minmax(280px,1fr));align-items:start}
.chunkbody .card{border-left:1px solid var(--line);padding-left:1.1rem}
.chunkbody .cards.night{counter-reset:pick}

/* ---------------------------------------------------------------- tags */
.v,.s{font-size:.82em}
.v::before{content:"\6E08";display:inline-block;border:1px solid var(--red-t);
  color:var(--red-t);padding:0 .15em;margin-right:.3em;line-height:1.2;
  transform:rotate(-6deg);white-space:nowrap;font-family:"Shippori Mincho",serif}
.s::before{content:"\672A\78BA\8A8D";margin-right:.35em;color:var(--grey);
  border-bottom:1px dotted var(--grey);white-space:nowrap}
.v,.s{color:var(--grey)}
.t1,.t2,.t3,.smp{font-family:"Big Shoulders Display",sans-serif;font-weight:600;
  font-size:.85em;letter-spacing:.1em;text-transform:uppercase;
  padding:0 .35em;white-space:nowrap}
.t1{background:var(--red);color:#fff}
.t2{border:1px solid var(--cyan);color:var(--cyan)}
.t3{border:1px solid var(--grey);color:var(--grey)}
.smp{border:1px dashed var(--red-t);color:var(--red-t)}

/* -------------------------------------------------------------- tables */
.tw{overflow-x:auto;margin:.8rem 0 1.4rem;border:1px solid var(--line);
  position:relative;overscroll-behavior:contain}
.tw::-webkit-scrollbar{height:6px}
.tw::-webkit-scrollbar-track{background:var(--black)}
.tw::-webkit-scrollbar-thumb{background:var(--line);border-radius:3px}
.tw::-webkit-scrollbar-thumb:hover{background:var(--cyan-d)}
.scroll-hint{
  display:none;font-family:"Big Shoulders Display",sans-serif;
  font-size:.74rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--grey);margin-bottom:.3rem;text-align:right;
}
@media (max-width:760px){
  .scroll-hint{display:block}
}
table{border-collapse:collapse;width:100%;min-width:44rem;font-size:.82rem;
  line-height:1.6;text-align:left}
th,td{padding:.45rem .65rem;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--red);color:#fff;font-weight:600;letter-spacing:.12em;
  text-transform:uppercase;font-size:.85rem}
td{color:#C9CBCE}
td b,td strong{color:var(--plate)}
tr:last-child td{border-bottom:0}
tr:nth-child(even) td{background:rgba(255,255,255,.015)}
td.day{white-space:nowrap;font-family:"Big Shoulders Display",sans-serif;
  font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--plate)}

/* ------------------------------------------------------- back-to-top & toast */
.btt{
  position:fixed;right:20px;bottom:24px;z-index:90;
  background:var(--black);color:var(--cyan);
  border:1px solid var(--cyan);border-radius:2px;
  padding:.5rem .75rem;display:inline-flex;align-items:center;gap:.35rem;
  font-family:"Big Shoulders Display",sans-serif;font-weight:900;
  font-size:.85rem;letter-spacing:.14em;text-transform:uppercase;
  cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.6);
  opacity:0;pointer-events:none;transform:translateY(8px);
  transition:opacity .2s, transform .2s, background .15s, color .15s;
  min-height:38px;
}
.btt.visible{
  opacity:1;pointer-events:auto;transform:translateY(0);
}
.btt:hover{
  background:var(--cyan);color:var(--black);
}

.toast{
  position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(20px);
  z-index:110;background:#0d0f12;color:var(--plate);
  border:1px solid var(--cyan);border-radius:2px;
  padding:.55rem 1.1rem;font-family:"Big Shoulders Display",sans-serif;
  font-weight:700;font-size:.9rem;letter-spacing:.1em;text-transform:uppercase;
  box-shadow:0 8px 24px rgba(0,0,0,.8), 0 0 12px rgba(0,191,214,.25);
  opacity:0;pointer-events:none;transition:opacity .2s, transform .2s;
  max-width:90vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.toast.show{
  opacity:1;transform:translateX(-50%) translateY(0);
}
"""

JS = r"""
(function(){
  // 1. URL Hash Deep Linking & Day Opening
  function openHash(){
    var id=location.hash.slice(1); if(!id) return;
    var el=document.getElementById(id); if(!el) return;
    if(el.tagName==='DETAILS') el.open=true;
    var p=el.parentElement;
    while(p){ if(p.tagName==='DETAILS') p.open=true; p=p.parentElement; }
    setTimeout(function(){
      el.scrollIntoView({behavior:'smooth',block:'start'});
    }, 50);
  }
  window.addEventListener('hashchange',openHash);
  openHash();

  // 2. Day summary click updates URL hash without reload
  document.querySelectorAll('.day > summary').forEach(function(s){
    s.addEventListener('click',function(){
      var dayEl=s.parentElement;
      var isOpen=dayEl.open;
      if(!isOpen && dayEl.id){
        history.replaceState(null,'','#'+dayEl.id);
      }
    });
  });

  // 3. Expand All / Collapse All Calendar Days
  var expBtn=document.getElementById('cal-expand-all');
  var colBtn=document.getElementById('cal-collapse-all');
  var days=Array.from(document.querySelectorAll('.day'));

  if(expBtn && colBtn){
    expBtn.addEventListener('click',function(){
      days.forEach(function(d){
        d.removeAttribute('name');
        d.open=true;
      });
    });
    colBtn.addEventListener('click',function(){
      days.forEach(function(d){
        d.open=false;
        d.setAttribute('name','day');
      });
    });
  }

  // 4. Toast notification system
  var toastEl=document.getElementById('toast');
  var toastTimer=null;
  function showToast(text){
    if(!toastEl) return;
    toastEl.textContent='✓ '+text;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer=setTimeout(function(){
      toastEl.classList.remove('show');
    }, 2400);
  }

  // 5. Copy Venue Buttons
  document.addEventListener('click',function(e){
    var btn=e.target.closest('.copy-btn');
    if(!btn) return;
    var text=btn.getAttribute('data-copy')||'';
    if(!text) return;
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){
        showToast('Copied "'+text+'" to clipboard');
        var orig=btn.innerHTML;
        btn.innerHTML='✓ Copied';
        btn.classList.add('copied');
        setTimeout(function(){
          btn.innerHTML=orig;
          btn.classList.remove('copied');
        }, 1800);
      }).catch(function(){
        fallbackCopy(text, btn);
      });
    } else {
      fallbackCopy(text, btn);
    }
  });

  function fallbackCopy(text, btn){
    var ta=document.createElement('textarea');
    ta.value=text;
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast('Copied "'+text+'"');
      var orig=btn.innerHTML;
      btn.innerHTML='✓ Copied';
      btn.classList.add('copied');
      setTimeout(function(){
        btn.innerHTML=orig;
        btn.classList.remove('copied');
      }, 1800);
    } catch(err){}
    document.body.removeChild(ta);
  }

  // 6. Live Search and Category Filter
  var searchInput=document.getElementById('event-search');
  var clearBtn=document.getElementById('search-clear');
  var filterMsg=document.getElementById('filter-msg');
  var chips=Array.from(document.querySelectorAll('.chip'));
  var plates=Array.from(document.querySelectorAll('.plate'));
  var tableRows=Array.from(document.querySelectorAll('.tw table tr:not(:first-child)'));

  var currentFilter='all';
  var currentQuery='';

  function applyFilter(){
    var q=currentQuery.trim().toLowerCase();
    var f=currentFilter;
    var isFiltering=(q.length>0 || f!=='all');
    var matchesCount=0;

    if(clearBtn) clearBtn.hidden=(q.length===0);

    // Filter plates
    plates.forEach(function(pl){
      var txt=pl.textContent.toLowerCase();
      var matchQ=(!q || txt.indexOf(q)!==-1);
      var matchF=true;
      if(f==='tokyo') matchF=(txt.indexOf('tokyo')!==-1 || txt.indexOf('shibuya')!==-1 || txt.indexOf('shinjuku')!==-1);
      else if(f==='kansai') matchF=(txt.indexOf('osaka')!==-1 || txt.indexOf('kyoto')!==-1 || txt.indexOf('hikone')!==-1);
      else if(f==='jazz') matchF=(txt.indexOf('jazz')!==-1 || txt.indexOf('pit inn')!==-1 || txt.indexOf('body & soul')!==-1);
      else if(f==='trad') matchF=(txt.indexOf('noh')!==-1 || txt.indexOf('能')!==-1 || txt.indexOf('min’yō')!==-1 || txt.indexOf('民謡')!==-1);
      else if(f==='booked') matchF=(txt.indexOf('held')!==-1 || txt.indexOf('booked')!==-1);

      var match=(matchQ && matchF);
      if(isFiltering){
        pl.classList.toggle('dimmed', !match);
        if(match) matchesCount++;
      } else {
        pl.classList.remove('dimmed');
      }
    });

    // Filter days & auto-expand matching days
    days.forEach(function(dayEl){
      var dayText=dayEl.textContent.toLowerCase();
      var dayMatchQ=(!q || dayText.indexOf(q)!==-1);
      var dayMatchF=true;
      var city=(dayEl.querySelector('.cal-city')||{}).textContent||'';
      city=city.toLowerCase();

      if(f==='tokyo') dayMatchF=(city==='tokyo');
      else if(f==='kansai') dayMatchF=(city==='osaka' || city==='kyoto' || city==='hikone');
      else if(f==='jazz') dayMatchF=(dayText.indexOf('jazz')!==-1 || dayText.indexOf('pit inn')!==-1 || dayText.indexOf('body & soul')!==-1);
      else if(f==='trad') dayMatchF=(dayText.indexOf('noh')!==-1 || dayText.indexOf('能')!==-1 || dayText.indexOf('bunraku')!==-1 || dayText.indexOf('shrine')!==-1);
      else if(f==='booked') dayMatchF=(dayEl.getAttribute('data-lamp')==='held');

      var hasMatch=(dayMatchQ && dayMatchF);
      dayEl.classList.toggle('hidden-filter', isFiltering && !hasMatch);

      if(isFiltering && hasMatch){
        dayEl.open=true;
        matchesCount++;
      }
    });

    // Filter table rows
    tableRows.forEach(function(row){
      var rowText=row.textContent.toLowerCase();
      var matchQ=(!q || rowText.indexOf(q)!==-1);
      var matchF=true;
      if(f==='tokyo') matchF=(rowText.indexOf('tokyo')!==-1 || rowText.indexOf('shibuya')!==-1 || rowText.indexOf('shinjuku')!==-1);
      else if(f==='kansai') matchF=(rowText.indexOf('osaka')!==-1 || rowText.indexOf('kyoto')!==-1 || rowText.indexOf('kobe')!==-1);
      else if(f==='jazz') matchF=(rowText.indexOf('jazz')!==-1 || rowText.indexOf('pit inn')!==-1);
      else if(f==='trad') matchF=(rowText.indexOf('noh')!==-1 || rowText.indexOf('能')!==-1 || rowText.indexOf('bunraku')!==-1);
      else if(f==='booked') matchF=(rowText.indexOf('booked')!==-1 || rowText.indexOf('held')!==-1);

      row.classList.toggle('hidden-filter', isFiltering && !(matchQ && matchF));
    });

    // Update message
    if(filterMsg){
      if(!isFiltering){
        filterMsg.innerHTML='Showing all events across Tokyo &amp; Kansai';
      } else {
        var criteria=[];
        if(f!=='all') criteria.push(f.toUpperCase());
        if(q) criteria.push('"'+q+'"');
        filterMsg.innerHTML='Found <strong>'+matchesCount+'</strong> matching day(s) &amp; picks for '+criteria.join(' + ');
      }
    }
  }

  if(searchInput){
    searchInput.addEventListener('input',function(){
      currentQuery=searchInput.value;
      applyFilter();
    });
    if(clearBtn){
      clearBtn.addEventListener('click',function(){
        searchInput.value='';
        currentQuery='';
        applyFilter();
        searchInput.focus();
      });
    }
  }

  chips.forEach(function(chip){
    chip.addEventListener('click',function(){
      chips.forEach(function(c){ c.classList.remove('active'); });
      chip.classList.add('active');
      currentFilter=chip.getAttribute('data-filter')||'all';
      applyFilter();
    });
  });

  // Keyboard shortcut: / focuses search, Esc clears
  document.addEventListener('keydown',function(e){
    if(e.key==='/' && document.activeElement!==searchInput && !['INPUT','TEXTAREA'].includes((document.activeElement||{}).tagName)){
      e.preventDefault();
      if(searchInput){
        searchInput.focus();
        searchInput.scrollIntoView({behavior:'smooth',block:'center'});
      }
    } else if(e.key==='Escape' && document.activeElement===searchInput){
      if(searchInput.value){
        searchInput.value='';
        currentQuery='';
        applyFilter();
      } else {
        searchInput.blur();
      }
    }
  });

  // HUD search button
  var hudFindBtn=document.getElementById('hud-find-btn');
  if(hudFindBtn && searchInput){
    hudFindBtn.addEventListener('click',function(){
      searchInput.focus();
      searchInput.scrollIntoView({behavior:'smooth',block:'center'});
    });
  }

  // 7. Scroll Progress & Back to Top Button
  var progressEl=document.getElementById('scroll-progress');
  var bttBtn=document.getElementById('back-to-top');

  window.addEventListener('scroll',function(){
    var sTop=window.pageYOffset||document.documentElement.scrollTop;
    var sHeight=document.documentElement.scrollHeight-document.documentElement.clientHeight;
    var pct=sHeight>0?(sTop/sHeight)*100:0;
    if(progressEl) progressEl.style.width=pct+'%';
    if(bttBtn){
      bttBtn.classList.toggle('visible', sTop>350);
    }
  }, {passive:true});

  if(bttBtn){
    bttBtn.addEventListener('click',function(){
      window.scrollTo({top:0,behavior:'smooth'});
    });
  }

  // 8. Clamp the long section notes to two lines, click to open.
  document.querySelectorAll('.sec > .legend').forEach(function(el){
    if(el.textContent.trim().length < 190) return;
    el.classList.add('clamp');
    el.setAttribute('role','button');
    el.setAttribute('tabindex','0');
    el.setAttribute('aria-expanded','false');
    function toggle(){
      var on=el.classList.toggle('clamp');
      el.classList.toggle('open',!on);
      el.setAttribute('aria-expanded', on?'false':'true');
    }
    el.addEventListener('click',toggle);
    el.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle();}
    });
  });
})();
"""

out = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{META['title']}</title>
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#070809">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800;900&family=Shippori+Mincho:wght@500;700&display=swap">
<style>{CSS}</style></head>
<body>
<a class="skip" href="#five" aria-label="Skip to the top five"></a>

<nav class="hud-bar" id="hud-bar" aria-label="Travel navigation">
  <div class="hud-inner">
    <a href="/japan/" class="hud-back" aria-label="Back to Japan Itinerary">
      <span aria-hidden="true">&larr;</span>
      <span>Itinerary</span>
    </a>
    <div class="hud-title-wrap">
      <span class="hud-badge">JAPAN-ONLY</span>
      <span class="hud-sub">19–25 Sept 2026</span>
    </div>
    <div class="hud-nav">
      <a href="#five" class="hud-nav-link" data-sec="five">Top 5</a>
      <a href="#calendar" class="hud-nav-link" data-sec="calendar">Calendar</a>
      <a href="#rest" class="hud-nav-link" data-sec="rest">Reference</a>
      <button type="button" class="hud-find-btn" id="hud-find-btn" aria-label="Find events in book">
        <span aria-hidden="true">🔍</span> Find
      </button>
    </div>
  </div>
  <div class="scroll-progress" id="scroll-progress" aria-hidden="true"></div>
</nav>

<header class="hero"><div class="inner">
{STANDFIRST}
<p class="jp1">\u65e5\u672c\u9650\u5b9a</p>
<details class="intro"><summary>The rules, and the two facts that shape the week</summary>
<div class="introbody">{INTRO_REST}</div></details>
</div></header>

<main class="wrap">

<div class="filter-bar" id="filter-bar">
  <div class="filter-row">
    <div class="search-box">
      <span class="search-icon" aria-hidden="true">🔍</span>
      <input type="search" id="event-search" class="search-input" placeholder="Filter artists, venues, dates, genres (press / to focus)…" aria-label="Filter events and venues" autocomplete="off" spellcheck="false">
      <button type="button" id="search-clear" class="search-clear" aria-label="Clear search" hidden>&times;</button>
    </div>
    <div class="chips" role="toolbar" aria-label="Filter events by category">
      <button type="button" class="chip active" data-filter="all">All</button>
      <button type="button" class="chip" data-filter="tokyo">Tokyo</button>
      <button type="button" class="chip" data-filter="kansai">Kansai</button>
      <button type="button" class="chip" data-filter="jazz">Jazz</button>
      <button type="button" class="chip" data-filter="trad">Noh / Rites</button>
      <button type="button" class="chip" data-filter="booked">Held</button>
    </div>
  </div>
  <div class="filter-msg" id="filter-msg" aria-live="polite">Showing all events across Tokyo &amp; Kansai</div>
</div>

<section class="sec" id="five">
{SEC['0']['h2']}
{FIVE_LEGEND}
<div class="five">
{PLATES}
</div>
</section>

<section class="sec" id="calendar">
{SEC['0b']['h2']}
{LEAD_0B}
<details class="calnote"><summary>What a day opens to</summary>
<div class="calnotebody">{SEC['2']['h2']}{LEAD_2}</div></details>

<div class="cal-bar">
  <div class="cal-legend" aria-label="Status indicator key">
    <span class="legend-item"><span class="legend-dot held" aria-hidden="true"></span> Held (Booked)</span>
    <span class="legend-item"><span class="legend-dot wait" aria-hidden="true"></span> Lottery / Wait</span>
    <span class="legend-item"><span class="legend-dot ok" aria-hidden="true"></span> Walk-up OK</span>
    <span class="legend-item"><span class="legend-dot off" aria-hidden="true"></span> Locked / Game</span>
  </div>
  <div class="cal-controls">
    <button type="button" class="cal-ctrl-btn" id="cal-expand-all" aria-label="Expand all calendar days">+ Expand All</button>
    <button type="button" class="cal-ctrl-btn" id="cal-collapse-all" aria-label="Collapse all calendar days">&minus; Collapse All</button>
  </div>
</div>

<div class="cal">
{''.join(CELLS)}
</div>
</section>

<section class="rest" id="rest">
<p>The rest of the book: the full ranked shortlists, the categories, the
booking friction, and what could not be verified.</p>
{''.join(REST)}
</section>

</main>

<button type="button" class="btt" id="back-to-top" aria-label="Scroll back to top">
  <span aria-hidden="true">&uarr;</span> TOP
</button>
<div class="toast" id="toast" role="status" aria-live="polite" aria-atomic="true"></div>

<script>{JS}</script>
</body></html>
"""

DST.parent.mkdir(parents=True, exist_ok=True)
# LF, like every other text file in the repo (.gitattributes eol=lf); the
# default on Windows would check the page out as CRLF against a LF blob.
DST.write_text(out, encoding="utf-8", newline="\n")
print("wrote", DST, len(out), "bytes")
print("five plates:", out.count('class="plate'), "| days:", out.count('class="day"'),
      "| rest chunks:", len(REST))
