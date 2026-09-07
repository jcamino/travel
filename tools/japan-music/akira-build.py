# -*- coding: utf-8 -*-
"""Build /japan/music as the Akira print-cyberpunk landing page.

Two things up front: the top five for the whole trip, and the calendar.
Tapping a day opens that day's best three, its "Also that day" line and its
per-day table. Everything else in the book stays on the page, collapsed, so
`tests/japan-music/content_check.py` still proves no sentence or link is lost.

Text is never altered: only tags and attributes are added, and sections are
re-ordered into the disclosure structure.

The source is `japan-only-music-book.md` next to this file, read through
`mdbook`: its front matter carries the trip shape and the five flyer faces,
its body carries the research. Nothing editorial lives in this file; what is
below is the design.

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
# Sections are addressed by role, not by number. They have been renumbered
# three times and every hardcoded "SEC['5']" silently stopped matching --
# which is how the per-day tables quietly failed to fold into the day plates
# for several commits. The two lead sections are positional; the other two
# special ones are found by name and carry no chapter number in the source.
FIVE_KEY, CAL_KEY = ORDER[0], ORDER[1]
TABLES_KEY = 'Per-day tables'
ACT_KEY = 'Act this week'
THREE_KEY = 'If you only do three things'
assert FIVE_KEY in SEC and CAL_KEY in SEC, ORDER[:3]
assert TABLES_KEY in SEC, f"no {TABLES_KEY!r} section; day plates lose their tables"

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

LEAD_0B, NIGHT = day_blocks(CAL_KEY, r'<div class="cards night">')
if TABLES_KEY in SEC:
    LEAD_5, TABLES = day_blocks(TABLES_KEY, r'<div class="tw">')
else:
    LEAD_5, TABLES = '', {}
# Trip shape, from the front matter: the order of the week, which city you
# sleep in, the kanji for the weekday, and the lamp (held = already booked;
# the lamp key stays "held" because CSS and the filter select on it, but the
# word shown to the reader is "booked",
# wait = not yet secured, ok = walk up, off = the night is spoken for).
DAYS = [d['day'] for d in META['days']]
CITY = {d['day']: d['city'] for d in META['days']}
KANJI = {d['day']: d['kanji'] for d in META['days']}
LAMP = {d['day']: d['lamp'] for d in META['days']}
assert list(NIGHT) == DAYS, list(NIGHT)
if TABLES:
    assert list(TABLES) == DAYS, list(TABLES)

LAMP_WORD = {
    'ok': 'walk-up', 'wait': 'wait', 'held': 'booked', 'off': 'spoken for'}


def paint_h2(h2html):
    m = re.match(r'<h2>(.*?)</h2>\s*$', h2html, re.S)
    if not m:
        return h2html
    parts = m.group(1).split('·', 1)
    if len(parts) != 2:
        return h2html
    return ('<h2><span class="secno">%s</span><span class="sectitle">%s</span></h2>'
            % (parts[0].strip() + ' ·', parts[1].strip()))


STANDFIRST = re.sub(
    r'<h1>(.*?)</h1>',
    lambda m: ('<h1><span class="ink">%s</span>'
               '<span class="ink2" aria-hidden="true">%s</span></h1>'
               % (m.group(1), m.group(1))),
    STANDFIRST, count=1)


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
             r'(.*?)\s*</div>\s*$', SEC[FIVE_KEY]['rest'])
assert m, 'section 0 shape changed'
FIVE_LEGEND, cards_blob = m.group(1), m.group(2)
raw = [c.strip() for c in cards_blob.split('<div class="card">') if c.strip()]
raw = [c[:c.rindex('</div>')] for c in raw]
assert len(raw) == 5, len(raw)

# Flyer faces for the five, from the front matter: the plate on the front
# of each pick. The faces and the cards are two hand-maintained lists in
# different orders, so they are matched on bill + day, never by position:
# zipping them put the wrong flyer inside four of the five plates (the
# Body & Soul plate opened onto Yamashita) until 7 Sept 2026.
FACES = [dict(f, times=[tuple(t) for t in f['times']])
         for f in META['five']]

HEADS = [re.search(r'<h3>(.*?)</h3>', c, re.S) for c in raw]
assert all(HEADS), 'a section 0 card has no heading to match on'
HEADS = [h.group(1) for h in HEADS]


def face_for(head):
    """The front-matter face belonging to this card, by its bill and day."""
    d = DAYRE.match(re.sub('<[^>]+>', '', head).strip())
    day = d.group(2) if d else ''
    hits = [f for f in FACES if f['bill'] in head and f['day'] == day]
    assert len(hits) == 1, (head[:70], day, [f['bill'] for f in hits])
    return hits[0]


# Card order is the ranking the prose argues (Takanaka is rank 0, booked;
# the candle noh is first), so the plates follow the cards, not the JSON.
PAIRS = [(face_for(h), c) for h, c in zip(HEADS, raw)]
assert len({f['ref'] for f, _ in PAIRS}) == len(FACES), 'a face matched twice'


def plate(i, f, card_html):
    times = ''.join('<b>%s</b><i>%s</i>' % (a, b) for a, b in f['times'])
    b2 = '<span>%s</span>' % f['bill2'] if f['bill2'] else ''
    venue = ''.join('<span>%s</span>' % v for v in f['venue'])
    inv = ' invert' if i == 0 else ''
    jump = html.escape(str(f['day']), quote=True)
    where = f['venue'][0] if f['venue'] else ''
    map_href = 'https://www.google.com/maps/search/?api=1&query=%s' % urllib.parse.quote(where)
    where_e = html.escape(where, quote=True)
    return f'''<article class="plate{inv}" data-day="{jump}">
<span class="reg tl"></span><span class="reg tr"></span>
<span class="reg bl"></span><span class="reg br"></span>
<span class="dither" aria-hidden="true"></span>
<p class="pl-date"><a class="pl-jump" href="#day-{jump}"><span class="dm">{f['month']}</span><span class="dd">{f['day']}</span><span class="dj">{f['dow']}</span></a></p>
<h3 class="pl-bill">{f['bill']}{b2}</h3>
<p class="pl-sub">{f['sub']}</p>
<p class="pl-venue">{venue}</p>
<div class="pl-times">{times}</div>
<p class="pl-y">{f['price']}</p>
<p class="pl-note">{f['note']}</p>
<p class="pl-acts"><a class="act" href="{map_href}">Map</a><button type="button" class="act copy" data-copy="{where_e}">Copy venue</button></p>
<details class="more"><summary>Read the flyer</summary>
<div class="morebody">{card_html}</div></details>
<div class="hud">
<b>Tier</b><i>{f['tier']}</i><b>Status</b><i>{f['status']}</i><b>Ref</b><span>{f['ref']}</span>
</div>
<p class="rank"><span>{i}</span></p>
</article>'''


PLATES = '\n'.join(plate(i, f, c) for i, (f, c) in enumerate(PAIRS))

# --------------------------------------------------------------- the calendar
CELLS = []
FILM = []
for n, d in enumerate(DAYS):
    num = d.split()[1]
    pick, cost = first_card(d)
    picktxt = html.unescape(re.sub('<[^>]+>', '', pick))
    cal_id = 'day-%s' % num
    lamp = LAMP[d]
    FILM.append(
        f'<a class="wk" href="#{cal_id}" data-lamp="{lamp}">'
        f'<span class="wk-d">{num}<i>{KANJI[d]}</i></span>'
        f'<span class="wk-city">{CITY[d]}</span>'
        f'<span class="wk-pick">{html.escape(picktxt)}</span>'
        f'<span class="wk-lamp">{LAMP_WORD.get(lamp, lamp)}</span>'
        f'</a>')
    prev = DAYS[n - 1] if n else None
    nxt = DAYS[n + 1] if n + 1 < len(DAYS) else None

    def _dn(dd, cls):
        nn = dd.split()[1]
        return ('<a class="%s" href="#day-%s">%s<i>%s</i></a>'
                % (cls, nn, nn, KANJI[dd]))

    daynav = (
        '<nav class="daynav" aria-label="Adjacent nights">'
        + (_dn(prev, 'dn-prev') if prev else '<span class="dn-prev"></span>')
        + '<span class="dn-now">%s<i>%s</i> %s</span>' % (num, KANJI[d], CITY[d])
        + (_dn(nxt, 'dn-next') if nxt else '<span class="dn-next"></span>')
        + '</nav>')
    extra = ''
    if d in TABLES:
        extra = (
            f'<details class="table"><summary>Everything else on the {ordinal(num)}</summary>'
            f'<h4 class="tblhead">{TABLES[d]["head"]}</h4>'
            f'{TABLES[d]["inner"]}</details>')
    CELLS.append(
        f'<details class="day" name="day" id="{cal_id}" data-lamp="{lamp}">'
        f'<summary><span class="cal-d">{num}<i>{KANJI[d]}</i></span>'
        f'<span class="cal-city">{CITY[d]}</span>'
        f'<span class="cal-pick">{html.escape(picktxt)}</span>'
        f'<span class="cal-cost">{cost}</span>'
        f'<span class="cal-open" aria-hidden="true"></span></summary>'
        f'<div class="daybody">'
        f'{daynav}'
        f'<h3 class="dayhead">{NIGHT[d]["head"]}</h3>'
        f'{NIGHT[d]["inner"]}'
        f'{extra}'
        f'</div></details>')

FILM_HTML = ''.join(FILM)

TRIP_MD = ROOT / "tools" / "japan" / "trip.md"
_seen, MUSICREFS = [], []
if TRIP_MD.is_file():
    for _r in re.findall(r'^\{musicref\} (.+)$',
                         TRIP_MD.read_text(encoding='utf-8'), re.M):
        if _r not in _seen:
            _seen.append(_r)
            MUSICREFS.append('<li>%s</li>' % html.escape(_r))
REFS_HTML = ('<ul class="vh musicrefs">%s</ul>' % ''.join(MUSICREFS)
             if MUSICREFS else '')

CALNOTE = ''
if TABLES_KEY in SEC:
    CALNOTE = (
        '<details class="calnote"><summary>What a day opens to</summary>'
        '<div class="calnotebody">%s%s</div></details>'
        % (SEC[TABLES_KEY]['h2'], LEAD_5))

H2_FIVE = paint_h2(SEC[FIVE_KEY]['h2'])
H2_CAL = paint_h2(SEC[CAL_KEY]['h2'])

# ------------------------------------------------------------ everything else
# Section 1 is the only thing on the page that expires. It does not go in
# the collapsed tail with the reference material; it goes above the fold.
THREE_HTML = ''
if THREE_KEY in SEC:
    THREE_HTML = ('<section class="sec three" id="three">%s%s</section>'
                  % (paint_h2(SEC[THREE_KEY]['h2']), SEC[THREE_KEY]['rest']))
ACT_HTML = ''
if ACT_KEY in SEC:
    ACT_HTML = ('<section class="sec acts" id="act">%s%s</section>'
                % (paint_h2(SEC[ACT_KEY]['h2']), SEC[ACT_KEY]['rest']))
REST_KEYS = [k for k in ORDER
             if k not in (FIVE_KEY, CAL_KEY, TABLES_KEY, ACT_KEY, THREE_KEY)]
REST = []
for k in REST_KEYS:
    t = SEC[k]['title']
    REST.append(
        '<details class="chunk" id="chunk-%s"><summary>%s</summary>'
        '<div class="chunkbody">%s</div></details>'
        % (html.escape(k, quote=True), t, SEC[k]['rest']))

# Kaneda's bike, side profile, facing right; the flip is done in CSS.
# viewBox 64x34, ground at y=33, so both wheels rest on the progress line.
MOTO_SVG = r"""<div class="moto" id="moto" aria-hidden="true">
<svg class="moto-body" viewBox="0 0 64 34" width="36" height="19" fill="none" focusable="false">
<defs><linearGradient id="mthrust" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="#00BFD6" stop-opacity="0"/>
<stop offset=".55" stop-color="#00BFD6" stop-opacity=".3"/>
<stop offset="1" stop-color="#DFFBFF" stop-opacity=".85"/></linearGradient></defs>
<ellipse cx="33" cy="32.5" rx="25" ry="2" fill="#000" opacity=".55"/>
<path class="moto-thrust" d="M-16 20.4 6 19.2 6 23.2-16 21.8Z" fill="url(#mthrust)"/>
<g>
<circle cx="15" cy="27" r="6" fill="#0A0B0D" stroke="#2E3238"/>
<g class="spoke"><path d="M15 21.8v10.4M9.8 27h10.4" stroke="var(--cyan)" stroke-width="1.4" opacity=".5"/></g>
<circle cx="15" cy="27" r="2.3" fill="#16181C" stroke="var(--cyan)" opacity=".9"/>
</g>
<g>
<circle cx="50" cy="27.5" r="5.5" fill="#0A0B0D" stroke="#2E3238"/>
<g class="spoke"><path d="M50 22.7v9.6M45.2 27.5h9.6" stroke="var(--cyan)" stroke-width="1.3" opacity=".5"/></g>
<circle cx="50" cy="27.5" r="2.1" fill="#16181C" stroke="var(--cyan)" opacity=".9"/>
</g>
<path d="M20 23.4 45 22.8 44.7 25 20 25.4Z" fill="#4A0818"/>
<path d="M5.4 22.4C4.6 17.2 6.2 13 10.4 11.3 13.8 10 18 9.9 20.8 11.2c2.7 1.3 3.9 3.5 4.3 6l9.1.8c4.8-1.9 9.9-2.3 14.7-1.2 6 1.4 10.8 2.9 12.9 4.1 1 .6.4 1.6-1.5 1.7l-15.3.4c-6.8 1.3-17.4 1.6-26 1.4-6.5-.15-11.4 0-13.6-2Z" fill="var(--red)"/>
<path d="M43.5 16c5.4-.5 11.9 1.3 18.3 4.7.9.6.5 1.8-1.5 1.9l-13.1.4c-.4-2.8-1.7-5.2-3.7-7Z" fill="#AF1338"/>
<path d="M10.4 11.3c3.4-1.3 7.6-1.4 10.4-.1" stroke="var(--red-t)" stroke-width="1" opacity=".7" fill="none"/>
<rect x="7" y="15.2" width="6.4" height="2.9" rx="1.45" fill="var(--plate)" opacity=".92"/>
<path d="M10.2 15.2h1.75a1.45 1.45 0 0 1 0 2.9H10.2Z" fill="var(--cyan)"/>
<path d="M35.8 16.1 39.4 17.1" stroke="#16181C" stroke-width="2.3" stroke-linecap="round"/>
<g stroke="var(--plate)" stroke-linecap="round">
<path d="M16.2 13.2 19.6 9.8 25 6.6" stroke-width="4.1"/>
<path d="M16.8 12.8 22.2 19" stroke-width="2.7"/>
<path d="M25 7.2 37.4 16" stroke-width="2.1"/>
</g>
<circle cx="28.4" cy="4.3" r="2.85" fill="var(--plate)"/>
<path d="M27.2 3.7 30.4 3.2" stroke="var(--cyan)" stroke-width="1.5" stroke-linecap="round"/>
<circle cx="60.6" cy="21.3" r="3" fill="var(--cyan)" opacity=".22"/>
<circle cx="60.6" cy="21.3" r="1.35" fill="#DFFBFF"/>
</svg>
</div>"""

CSS = r"""
:root{
  --black:#070809; --plate:#E9E7E1; --red:#E0234B; --red-t:#FF5C7A;
  --cyan:#00BFD6; --cyan-d:#0B7A87; --grey:#8A8C90; --line:#26282C;
  --lamp-ok:#00BFD6; --lamp-wait:#FFB020; --lamp-held:#FF5C7A;
  --rail:4.6rem;
}
*,*::before,*::after{box-sizing:border-box}
html{color-scheme:dark;-webkit-text-size-adjust:100%;scroll-behavior:smooth;
  scroll-padding-top:calc(var(--rail) + env(safe-area-inset-top,0px))}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--black);color:var(--plate);
  font-family:"Shippori Mincho","Hiragino Mincho ProN",serif;
  font-size:16px;line-height:1.75;font-variant-numeric:tabular-nums;
  touch-action:manipulation}
p{margin:0 0 .8em}
h1,h2,h3,h4{margin:0}
a{color:var(--cyan)}
a:hover{color:var(--plate)}
.disp,h1,h2,.secno,.dayhead,.cal-d,.pl-date,.pl-times,.pl-y,.hud,.rank,
.tblhead,th,.chunk>summary,.more>summary,.table>summary,.cal-city,.cal-cost,
.rail,.wk,.daynav,.act,.filter-bar{
  font-family:"Big Shoulders Display","Shippori Mincho",sans-serif}
:where(a,summary,button,[tabindex]):focus-visible{outline:2px solid var(--cyan);
  outline-offset:3px}
summary,button,.wk,.act{cursor:pointer}
.skip{position:fixed;left:8px;top:-4rem;z-index:80;background:var(--red);
  color:#fff;padding:.5rem .9rem;text-decoration:none;transition:top .12s;
  font-family:"Big Shoulders Display",sans-serif;letter-spacing:.1em}
.skip::before{content:"Skip to this week's deadlines"}
.skip:focus{top:8px}
.wrap{max-width:74rem;margin:0 auto;
  padding:0 20px calc(5rem + env(safe-area-inset-bottom,0px))}
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

/* ----------------------------------------------------------- masthead */
.hero{border-bottom:1px solid var(--line)}
.hero .inner{max-width:74rem;margin:0 auto;padding:2.6rem 20px 2rem}
.kicker{font-family:"Big Shoulders Display",sans-serif;font-weight:600;
  letter-spacing:.3em;font-size:.8rem;color:var(--cyan);margin:0 0 .9rem;
  text-transform:uppercase}
h1{position:relative;isolation:isolate;font-family:"Big Shoulders Display",sans-serif;
  font-weight:900;font-size:clamp(2.4rem,8vw,5.6rem);line-height:.84;
  letter-spacing:-.005em;text-transform:uppercase;max-width:12ch;
  text-wrap:balance}
h1 .ink{position:relative;z-index:1}
/* two plates, out of register on purpose: both inks stay legible */
h1 .ink2{position:absolute;left:0;top:0;right:0;color:var(--red);
  transform:translate(2px,-2px);z-index:0;pointer-events:none}
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
.sec{margin:3.4rem 0 0;scroll-margin-top:calc(var(--rail) + .6rem)}
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
.five{display:grid;gap:1.4rem;grid-template-columns:minmax(0,1.28fr) repeat(4,minmax(0,1fr))}
@media (max-width:1100px){
  .five{grid-template-columns:repeat(auto-fit,minmax(198px,1fr))}}
@media (max-width:560px){
  .five{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;
    gap:1rem;padding-bottom:.6rem;margin-inline:-20px;padding-inline:20px;
    -webkit-overflow-scrolling:touch}
  .plate{flex:0 0 min(84vw,22rem);scroll-snap-align:start}}
.plate{position:relative;isolation:isolate;border:1px solid var(--line);padding:1rem .95rem 1.05rem;
  background:var(--black);display:flex;flex-direction:column}
.plate:hover .reg::before,.plate:hover .reg::after{background:var(--red-t)}
.plate:hover.invert .reg::before,.plate:hover.invert .reg::after{background:var(--cyan-d)}
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
.pl-jump{color:inherit;text-decoration:none;display:flex;align-items:baseline;gap:.3rem}
.pl-jump:hover{color:inherit}
.pl-acts{display:flex;gap:.45rem;margin:.55rem 0 .15rem}
.act{display:inline-flex;align-items:center;min-height:2.5rem;padding:0 .7rem;
  font-weight:600;font-size:.82rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--cyan);border:1px solid var(--line);background:transparent;text-decoration:none}
.act:hover{border-color:var(--cyan);color:var(--plate)}
.plate.invert .act{color:var(--cyan-d);border-color:rgba(7,8,9,.25)}
.plate.invert .act:hover{color:var(--black);border-color:var(--cyan-d)}
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

/* --------------------------------------------------------- 2. the calendar */
.cal{border-top:1px solid var(--line)}
.day{border-bottom:1px solid var(--line)}
.day{scroll-margin-top:calc(var(--rail) + .4rem)}
.day>summary{display:grid;align-items:baseline;gap:.2rem 1rem;cursor:pointer;
  padding:.85rem .2rem;list-style:none;min-height:3.4rem;
  grid-template-columns:4.6rem 5.5rem minmax(0,1fr) max-content 1.4rem}
.day>summary:active{background:#101214}
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
  border-left:1px solid var(--line);counter-increment:pick}
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

/* nested disclosures */
.more,.table,.chunk{margin-top:.8rem}
.plate>.more{order:9;margin-top:.7rem}
.more>summary,.table>summary{font-family:"Big Shoulders Display",sans-serif;
  font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  font-size:.85rem;color:var(--cyan);cursor:pointer;list-style:none;
  border-top:1px solid var(--line);padding:.5rem 0 0}
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
.three{margin:1.6rem 0 0;border:1px solid var(--cyan);border-left:3px solid var(--cyan);
  border-radius:2px;padding:1.1rem 1.2rem;background:rgba(0,191,214,.05)}
.three>h2{margin-top:0}
.three>.legend{margin:.6rem 0 1rem}
.three ol{margin:0;padding-left:0;list-style:none;counter-reset:three}
.three li{counter-increment:three;margin:.75rem 0;line-height:1.5;
  padding-left:2.1rem;position:relative}
.three li::before{content:counter(three);position:absolute;left:0;top:-.1rem;
  font-family:"Big Shoulders Display",sans-serif;font-weight:900;font-size:1.5rem;
  color:var(--cyan);line-height:1}
@media(max-width:640px){.three{padding:.9rem .95rem;margin-top:1.1rem}}
.acts{margin:1.1rem 0 0;border:1px solid var(--red);border-left:3px solid var(--red);
  border-radius:2px;padding:1.1rem 1.2rem;background:rgba(224,35,75,.055)}
.acts>h2{margin-top:0}
.acts>.legend{margin:.6rem 0 1rem}
.acts ol{margin:0;padding-left:1.1rem}
.acts li{margin:.6rem 0;line-height:1.5}
@media(max-width:640px){.acts{padding:.9rem .95rem;margin-top:1.1rem}}
.rest{margin-top:3.4rem;border-top:1px solid var(--line);padding-top:1.4rem}
.rest>p{color:var(--grey);font-size:.88rem;max-width:40rem}
.chunk{border-bottom:1px solid var(--line)}
.chunk>summary{font-weight:800;text-transform:uppercase;letter-spacing:.03em;
  font-size:1.05rem;cursor:pointer;list-style:none;padding:.75rem 0;
  display:flex;gap:.7rem;align-items:baseline}
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
  max-width:100%;min-width:0;overscroll-behavior-x:contain}
table{border-collapse:collapse;width:100%;min-width:44rem;font-size:.82rem;
  line-height:1.6;text-align:left}
th,td{padding:.45rem .65rem;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--red);color:#fff;font-weight:600;letter-spacing:.12em;
  text-transform:uppercase;font-size:.85rem}
td{color:#C9CBCE}
td b,td strong{color:var(--plate)}
tr:last-child td{border-bottom:0}
td.day{white-space:nowrap;font-family:"Big Shoulders Display",sans-serif;
  font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--plate)}

/* ----------------------------------------------------------- sticky week */
.rail{position:sticky;top:0;z-index:50;background:var(--black);
  border-bottom:1px solid var(--line);
  padding:calc(.35rem + env(safe-area-inset-top,0px)) 0 .6rem}
.rail-inner{max-width:74rem;margin:0 auto;padding:0 20px;min-width:0}
.rail-sec{display:flex;flex-wrap:wrap;align-items:center;gap:.15rem .2rem;
  margin:0 0 .35rem}
.rail-sec a{color:var(--grey);text-decoration:none;font-weight:600;
  letter-spacing:.12em;text-transform:uppercase;font-size:.78rem;
  padding:.35rem .55rem;min-height:2.5rem;display:inline-flex;align-items:center}
.rail-sec a:hover,.rail-sec a[aria-current="true"]{color:var(--cyan)}
.film{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);min-width:0;width:100%;
  overflow-x:auto}
.wk{display:flex;flex-direction:column;gap:.15rem;padding:.45rem .5rem .5rem;
  background:var(--black);color:var(--plate);text-decoration:none;min-height:4.4rem;
  min-width:0;position:relative}
.wk:hover{background:#101214;color:var(--plate)}
.wk[aria-current="true"]{background:#101214;box-shadow:inset 0 2px 0 var(--cyan)}
.wk-d{font-weight:900;font-size:1.35rem;line-height:.9;padding-left:.85rem;
  position:relative}
.wk-d::before{content:"";position:absolute;left:0;top:.35em;width:8px;height:8px;
  border-radius:50%;background:var(--grey)}
.wk[data-lamp="ok"] .wk-d::before{background:var(--lamp-ok)}
.wk[data-lamp="wait"] .wk-d::before{background:var(--lamp-wait)}
.wk[data-lamp="held"] .wk-d::before{background:var(--lamp-held)}
.wk[data-lamp="off"] .wk-d::before{background:#3A3D42}
.wk-d i{font-family:"Shippori Mincho",serif;font-weight:700;font-style:normal;
  font-size:.72rem;color:var(--red-t);margin-left:.15em}
.wk-city{font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  font-size:.68rem;color:var(--cyan)}
.wk-pick{font-family:"Shippori Mincho",serif;font-size:.7rem;line-height:1.35;
  color:#C9CBCE;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden}
.wk-lamp{font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  font-size:.62rem;color:var(--grey)}
@media (max-width:820px){
  :root{--rail:5.6rem}
  .film{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;
    -webkit-overflow-scrolling:touch;background:transparent;border:0;gap:.35rem;
    overscroll-behavior-x:contain}
  .wk{flex:0 0 4.6rem;scroll-snap-align:start;border:1px solid var(--line);
    min-height:4.2rem;padding:.4rem .45rem}
  .wk-pick,.wk-city{display:none}
  .wk-d{font-size:1.2rem;padding-left:.75rem}}
.live{position:fixed;left:0;bottom:0;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
.daynav{display:flex;align-items:center;justify-content:space-between;gap:.8rem;
  margin:0 0 1rem;padding:.2rem 0 .7rem;border-bottom:1px solid var(--line)}
.daynav a,.dn-now{font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  font-size:.85rem;text-decoration:none;min-height:2.5rem;display:inline-flex;
  align-items:center;gap:.25rem}
.daynav a{color:var(--cyan)}
.daynav a:hover{color:var(--plate)}
.dn-now{color:var(--plate)}
.daynav i{font-family:"Shippori Mincho",serif;font-style:normal;color:var(--red-t)}
.dn-prev:empty,.dn-next:empty{visibility:hidden;min-width:3rem}
.day[open] .daybody{animation:open .22s ease}
@keyframes open{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){
  .day[open] .daybody{animation:none}
  .act,.wk,.rail-sec a{transition:none}}
.rest{scroll-margin-top:calc(var(--rail) + .6rem)}

/* ------------------------------------------- scroll progress (from 3-8) */
/* No position rule for .rail here: it is already position:sticky, which is a
   positioned value, so it contains the absolutely positioned progress line.
   Re-declaring position:relative below the original rule would kill sticky. */
/* The gradient is sized to the viewport, not to the bar, so the trail is
   *revealed* cyan-first and warms to red as the page runs out. Sized to the
   bar it would rescale, and the tip would be red at every scroll position --
   which is exactly where the red bike sits. */
.scroll-progress{position:absolute;left:0;bottom:-1px;height:2px;width:0%;
  background:linear-gradient(90deg,var(--cyan),var(--red));
  background-size:100vw 100%;
  pointer-events:none;z-index:1}

/* --------------------------------------------------- Kaneda, on the trail */
/* Decorative. Rides the leading edge of the progress line and turns around
   when the scroll direction flips. Same containing block as .scroll-progress
   (.rail is position:sticky) -- do not add position:relative to .rail. */
/* 36x19 against a 19.4px gap: the floor is the *ink* of the film strip's
   bottom line of lamp text ("WALK-UP", "SPOKEN FOR"), not its line box, which
   hides 3.7px of leading. The rail's padding-bottom above is .6rem rather
   than .4rem to buy the last 3px of that. bottom:0 seats the wheels in the
   2px line rather than perching him above it. */
.moto{position:absolute;left:0;bottom:0;width:36px;height:19px;
  pointer-events:none;z-index:2;will-change:transform}
.moto-body{display:block;width:100%;height:100%;overflow:visible;
  transform:scaleX(var(--dir,1));transform-origin:23.4% 90%;
  transition:transform .22s cubic-bezier(.34,1.4,.64,1)}
/* Nose up on the fast burst. scaleX(-1) mirrors the rotation with it, so the
   nose still lifts when he is pointed the other way. */
.moto.fast .moto-body{transform:scaleX(var(--dir,1)) rotate(-5deg)}
.moto-thrust{opacity:0;transition:opacity .18s ease}
.moto.moving .moto-thrust{opacity:1}
.moto .spoke{transform-box:fill-box;transform-origin:center;
  animation:motospin .9s linear infinite;animation-play-state:paused}
.moto.moving .spoke{animation-play-state:running}
.moto.fast .spoke{animation-duration:.28s}
@keyframes motospin{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){
  .moto-body{transition:none}
  .moto.fast .moto-body{transform:scaleX(var(--dir,1))}
  .moto .spoke{animation:none}
  .moto-thrust{display:none}}

/* ------------------------------------------------ filter bar (from 3-8) */
.filter-bar{margin:2.2rem 0 1.8rem;padding:1.1rem 1.2rem;
  background:rgba(18,19,23,.75);border:1px solid var(--line);
  border-left:3px solid var(--cyan);position:relative}
.filter-row{display:flex;flex-wrap:wrap;align-items:center;gap:.8rem}
.search-box{position:relative;flex:1 1 260px;display:flex;align-items:center}
.search-icon{position:absolute;left:.75rem;color:var(--grey);pointer-events:none}
.search-input{width:100%;padding:.55rem .8rem .55rem 2.3rem;
  background:var(--black);color:var(--plate);
  border:1px solid var(--line);font-family:"Shippori Mincho",serif;
  font-size:.9rem;outline:none;border-radius:2px;
  transition:border-color .15s, box-shadow .15s}
.search-input:focus{border-color:var(--cyan);box-shadow:0 0 0 2px rgba(0,191,214,.2)}
.search-input::-webkit-search-cancel-button{display:none}
.search-clear{position:absolute;right:.6rem;background:none;border:none;
  color:var(--grey);font-size:1.2rem;cursor:pointer;padding:.2rem .4rem;line-height:1}
.search-clear:hover{color:var(--plate)}
.chips{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center}
.chip{background:var(--black);color:var(--grey);border:1px solid var(--line);
  font-family:"Big Shoulders Display",sans-serif;font-weight:700;
  font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;
  padding:.35rem .65rem;cursor:pointer;border-radius:2px;
  transition:border-color .15s, color .15s, background .15s, box-shadow .15s;
  min-height:34px}
.chip:hover{color:var(--plate);border-color:var(--grey)}
.chip.active{background:var(--cyan);color:var(--black);border-color:var(--cyan);
  box-shadow:0 0 10px rgba(0,191,214,.3)}
.filter-msg{margin-top:.6rem;font-size:.82rem;color:var(--grey);
  font-family:"Big Shoulders Display",sans-serif;letter-spacing:.08em;
  text-transform:uppercase;min-height:1.2em;display:flex;align-items:center;gap:.5rem}
.filter-msg strong{color:var(--cyan)}
.plate.dimmed{opacity:.2;transform:scale(.98)}
details.day.hidden-filter,tr.hidden-filter{display:none !important}
@media (prefers-reduced-motion:reduce){
  .plate.dimmed{transform:none}}
"""

JS = r"""
(function(){
  var live=document.getElementById('live');
  function say(t){ if(live) live.textContent=t; }

  function markFilm(id){
    document.querySelectorAll('.wk').forEach(function(a){
      var on=a.getAttribute('href')==='#'+id;
      if(on) a.setAttribute('aria-current','true');
      else a.removeAttribute('aria-current');
    });
  }
  function markSec(){
    var cur='five';
    ['five','calendar','rest'].forEach(function(id){
      var n=document.getElementById(id);
      if(n && n.getBoundingClientRect().top < 120) cur=id;
    });
    document.querySelectorAll('.rail-sec a[href^="#"]').forEach(function(a){
      var on=a.getAttribute('href')==='#'+cur;
      if(on) a.setAttribute('aria-current','true');
      else a.removeAttribute('aria-current');
    });
  }
  function openHash(){
    var id=location.hash.slice(1); if(!id) return;
    var el=document.getElementById(id); if(!el) return;
    if(el.tagName==='DETAILS') el.open=true;
    var p=el.parentElement;
    while(p){ if(p.tagName==='DETAILS') p.open=true; p=p.parentElement; }
    markFilm(id);
  }
  window.addEventListener('hashchange',openHash);
  window.addEventListener('scroll',markSec,{passive:true});
  openHash();
  markSec();

  document.querySelectorAll('details.day').forEach(function(el){
    el.addEventListener('toggle',function(){
      if(!el.open) return;
      if(location.hash!=='#'+el.id){
        history.replaceState(null,'','#'+el.id);
      }
      markFilm(el.id);
    });
  });

  document.querySelectorAll('.copy').forEach(function(btn){
    btn.addEventListener('click',function(){
      var t=btn.getAttribute('data-copy')||'';
      if(!t) return;
      function ok(){ say('Copied '+t); btn.textContent='Copied';
        setTimeout(function(){ btn.textContent='Copy venue'; },1200); }
      if(navigator.clipboard&&navigator.clipboard.writeText){
        navigator.clipboard.writeText(t).then(ok,function(){});
      }
    });
  });

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

  // ------------------------------------------ scroll progress (from 3-8)
  // ...and the bike that draws it. One rAF-throttled writer for both, so the
  // trail and its rider can never disagree about where the tip is.
  var progressEl=document.getElementById('scroll-progress');
  if(progressEl){
    var moto=document.getElementById('moto');
    var rail=progressEl.parentNode;
    function scrollY(){
      var max=document.documentElement.scrollHeight-document.documentElement.clientHeight;
      var y=window.pageYOffset||document.documentElement.scrollTop;
      // Elastic overscroll reports positions past both ends and then settles
      // back. Unclamped, that settle reads as a reversal, and he used to spin
      // round at the foot of the page before the reader had scrolled up at all.
      return y<0?0:(y>max?max:y);
    }
    var lastY=scrollY();
    var facing=1, revAccum=0, queued=false, idleT=null, railW=0, motoW=0, rearOff=0;

    function measure(){
      railW=rail.clientWidth;
      motoW=moto?moto.offsetWidth:0;
      // 15/64 is the rear wheel's centre in the SVG's own viewBox, and it is
      // also .moto-body's transform-origin, so the flip pivots on this point
      // and the trail stays welded to it.
      rearOff=motoW*15/64;
    }

    function paint(){
      queued=false;
      var sHeight=document.documentElement.scrollHeight-document.documentElement.clientHeight;
      var pct=sHeight>0?(scrollY()/sHeight)*100:0;
      pct=Math.min(100,Math.max(0,pct));
      if(moto&&railW>motoW){
        // One number drives both. He runs flush left at the top of the page to
        // flush right at the bottom; the trail stops at his rear wheel rather
        // than running under him and out the front. Written in the same frame,
        // off the same x, with no transition on either -- that is the whole of
        // keeping them in sync.
        var x=(pct/100)*(railW-motoW);
        moto.style.transform='translate3d('+x.toFixed(1)+'px,0,0)';
        progressEl.style.width=(x+rearOff).toFixed(1)+'px';
      }else{
        progressEl.style.width=pct+'%';
      }
    }

    function coast(){
      if(!moto) return;
      moto.classList.remove('moving','fast');
      // Parked at the top there is no "up" left to face. He pivots on his rear
      // wheel, so mirrored at x=0 his nose hangs off the left edge of the rail;
      // point him back into the page instead. Only once he has come to rest, so
      // this never fires mid-scroll.
      if(facing<0&&scrollY()<=1){
        facing=1; revAccum=0;
        moto.style.setProperty('--dir',1);
      }
    }

    window.addEventListener('scroll',function(){
      var y=scrollY();
      var dy=y-lastY;
      // 1.5px of hysteresis: a trackpad's jitter must not spin him round.
      if(Math.abs(dy)>1.5){
        if((dy>0?1:-1)===facing){
          revAccum=0;
        }else{
          // Turning round is a commitment, not one stray frame: 8px of travel
          // against the way he is pointed, and any step back the other way
          // spends the credit. Momentum tails and settles never reach it.
          revAccum+=Math.abs(dy);
          if(revAccum>8){
            facing=-facing; revAccum=0;
            if(moto) moto.style.setProperty('--dir',facing);
          }
        }
        if(moto){
          moto.classList.add('moving');
          moto.classList.toggle('fast',Math.abs(dy)>34);
        }
        lastY=y;
        clearTimeout(idleT);
        idleT=setTimeout(coast,420);
      }
      if(!queued){queued=true;requestAnimationFrame(paint);}
    }, {passive:true});

    window.addEventListener('resize',function(){
      measure();
      if(!queued){queued=true;requestAnimationFrame(paint);}
    }, {passive:true});

    measure();
    paint();
  }

  // --------------------------------------------- live filter (from 3-8)
  var searchInput=document.getElementById('event-search');
  var clearBtn=document.getElementById('search-clear');
  var filterMsg=document.getElementById('filter-msg');
  var chips=Array.from(document.querySelectorAll('.chip'));
  var plates=Array.from(document.querySelectorAll('.plate'));
  // '.day' also marks the slot column of every per-day table (<td class="day">);
  // only the calendar's <details class="day"> are filterable nights.
  var fDays=Array.from(document.querySelectorAll('details.day'));
  var tableRows=Array.from(document.querySelectorAll('.tw table tr:not(:first-child)'));
  var currentFilter='all';
  var currentQuery='';

  function has(t,x){ return t.indexOf(x)!==-1; }

  function applyFilter(){
    var q=currentQuery.trim().toLowerCase();
    var f=currentFilter;
    var isFiltering=(q.length>0 || f!=='all');
    var matchesCount=0;

    if(clearBtn) clearBtn.hidden=(q.length===0);

    plates.forEach(function(pl){
      var txt=pl.textContent.toLowerCase();
      var matchQ=(!q || has(txt,q));
      var matchF=true;
      if(f==='tokyo') matchF=has(txt,'tokyo')||has(txt,'shibuya')||has(txt,'shinjuku');
      else if(f==='kansai') matchF=has(txt,'osaka')||has(txt,'kyoto')||has(txt,'hikone');
      else if(f==='jazz') matchF=has(txt,'jazz')||has(txt,'pit inn')||has(txt,'body & soul');
      else if(f==='trad') matchF=has(txt,'noh')||has(txt,'能')||has(txt,'min’yō')||has(txt,'民謡');
      else if(f==='booked') matchF=has(txt,'held')||has(txt,'booked');
      var match=(matchQ && matchF);
      if(isFiltering){
        pl.classList.toggle('dimmed', !match);
        if(match) matchesCount++;
      } else {
        pl.classList.remove('dimmed');
      }
    });

    fDays.forEach(function(dayEl){
      var dayText=dayEl.textContent.toLowerCase();
      var dayMatchQ=(!q || has(dayText,q));
      var dayMatchF=true;
      var city=((dayEl.querySelector('.cal-city')||{}).textContent||'').toLowerCase();
      if(f==='tokyo') dayMatchF=(city==='tokyo');
      else if(f==='kansai') dayMatchF=(city==='osaka'||city==='kyoto'||city==='hikone');
      else if(f==='jazz') dayMatchF=has(dayText,'jazz')||has(dayText,'pit inn')||has(dayText,'body & soul');
      else if(f==='trad') dayMatchF=has(dayText,'noh')||has(dayText,'能')||has(dayText,'bunraku')||has(dayText,'shrine');
      else if(f==='booked') dayMatchF=(dayEl.getAttribute('data-lamp')==='held');
      var hasMatch=(dayMatchQ && dayMatchF);
      dayEl.classList.toggle('hidden-filter', isFiltering && !hasMatch);
      if(isFiltering && hasMatch){ dayEl.open=true; matchesCount++; }
    });

    tableRows.forEach(function(row){
      var rowText=row.textContent.toLowerCase();
      var matchQ=(!q || has(rowText,q));
      var matchF=true;
      if(f==='tokyo') matchF=has(rowText,'tokyo')||has(rowText,'shibuya')||has(rowText,'shinjuku');
      else if(f==='kansai') matchF=has(rowText,'osaka')||has(rowText,'kyoto')||has(rowText,'kobe');
      else if(f==='jazz') matchF=has(rowText,'jazz')||has(rowText,'pit inn');
      else if(f==='trad') matchF=has(rowText,'noh')||has(rowText,'能')||has(rowText,'bunraku');
      else if(f==='booked') matchF=has(rowText,'booked')||has(rowText,'held');
      row.classList.toggle('hidden-filter', isFiltering && !(matchQ && matchF));
    });

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
    say(isFiltering ? matchesCount+' matches' : 'Filter cleared');
  }

  if(searchInput){
    searchInput.addEventListener('input',function(){
      currentQuery=searchInput.value; applyFilter();
    });
    if(clearBtn){
      clearBtn.addEventListener('click',function(){
        searchInput.value=''; currentQuery=''; applyFilter(); searchInput.focus();
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

  document.addEventListener('keydown',function(e){
    if(e.key==='/' && document.activeElement!==searchInput &&
       ['INPUT','TEXTAREA'].indexOf((document.activeElement||{}).tagName)===-1){
      e.preventDefault();
      if(searchInput){ searchInput.focus(); searchInput.scrollIntoView({behavior:'smooth',block:'center'}); }
    } else if(e.key==='Escape' && document.activeElement===searchInput){
      if(searchInput.value){ searchInput.value=''; currentQuery=''; applyFilter(); }
      else { searchInput.blur(); }
    }
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=Shippori+Mincho:wght@500;700&display=swap">
<style>{CSS}</style></head>
<body>
<a class="skip" href="#act" aria-label="Skip to this week's deadlines"></a>
<div class="live" id="live" aria-live="polite"></div>
<nav class="rail" aria-label="The week">
<div class="rail-inner">
<div class="rail-sec">
<a href="/japan/">Itinerary</a>
<a href="#act">Act now</a>
<a href="#five">The picks</a>
<a href="#calendar">The week</a>
<a href="#rest">The rest</a>
</div>
<div class="film" role="navigation" aria-label="Seven nights">
{FILM_HTML}
</div>
</div>
<div class="scroll-progress" id="scroll-progress" aria-hidden="true"></div>
{MOTO_SVG}
</nav>
<header class="hero"><div class="inner">
{STANDFIRST}
<p class="jp1">\u65e5\u672c\u9650\u5b9a</p>
<details class="intro"><summary>Page context</summary>
<div class="introbody">{INTRO_REST}</div></details>
</div></header>
<main class="wrap">
{THREE_HTML}
{ACT_HTML}

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
      <button type="button" class="chip" data-filter="booked">Booked</button>
    </div>
  </div>
  <div class="filter-msg" id="filter-msg" aria-live="polite">Showing all events across Tokyo &amp; Kansai</div>
</div>

<section class="sec" id="five">
{H2_FIVE}
{FIVE_LEGEND}
<div class="five">
{PLATES}
</div>
</section>

<section class="sec" id="calendar">
{H2_CAL}
{LEAD_0B}
{CALNOTE}
<div class="cal">
{''.join(CELLS)}
</div>
</section>

<section class="rest" id="rest">
<p>The rest of the book: the full ranked shortlists, the categories, the
booking friction, and what could not be verified.</p>
{''.join(REST)}
</section>

{REFS_HTML}
</main>
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

# The English toggle is injected here rather than woven into the template so
# the page above stays exactly as content_check.py expects to find it: the
# injection only appends a <style> and a <script>, and the swap happens in the
# browser, so no Japanese text in the document is moved or wrapped on disk.
import i18n  # noqa: E402
i18n.inject(DST)
