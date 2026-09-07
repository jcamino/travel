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
import re
import sys
import pathlib

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
LEAD_5, TABLES = day_blocks('5', r'<div class="tw">')
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
    return f'''<article class="plate{inv}">
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
<details class="more"><summary>Read the flyer</summary>
<div class="morebody">{card_html}</div></details>
<div class="hud">
<b>Tier</b><i>{f['tier']}</i><b>Status</b><i>{f['status']}</i><b>Ref</b><span>{f['ref']}</span>
</div>
<p class="rank"><span>{i + 1}</span></p>
</article>'''


PLATES = '\n'.join(plate(i, f, c) for i, (f, c) in enumerate(zip(FACES, raw)))

# --------------------------------------------------------------- the calendar
CELLS = []
PANELS = []
for n, d in enumerate(DAYS):
    num = d.split()[1]
    pick, cost = first_card(d)
    picktxt = re.sub('<[^>]+>', '', pick)
    cal_id = 'day-%s' % num
    CELLS.append(
        f'<details class="day" name="day" id="{cal_id}" data-lamp="{LAMP[d]}">'
        f'<summary><span class="cal-d">{num}<i>{KANJI[d]}</i></span>'
        f'<span class="cal-city">{CITY[d]}</span>'
        f'<span class="cal-pick">{picktxt}</span>'
        f'<span class="cal-cost">{cost}</span>'
        f'<span class="cal-open" aria-hidden="true"></span></summary>'
        f'<div class="daybody">'
        f'<h3 class="dayhead">{NIGHT[d]["head"]}</h3>'
        f'{NIGHT[d]["inner"]}'
        f'<details class="table"><summary>Everything else on the {ordinal(num)}</summary>'
        f'<h4 class="tblhead">{TABLES[d]["head"]}</h4>'
        f'{TABLES[d]["inner"]}</details>'
        f'</div></details>')

# ------------------------------------------------------------ everything else
REST_KEYS = [k for k in ORDER if k not in ('0', '0b', '5')]
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
a{color:var(--cyan)}
a:hover{color:var(--plate)}
.disp,h1,h2,.secno,.dayhead,.cal-d,.pl-date,.pl-times,.pl-y,.hud,.rank,
.tblhead,th,.chunk>summary,.more>summary,.table>summary,.cal-city,.cal-cost{
  font-family:"Big Shoulders Display","Shippori Mincho",sans-serif}
:where(a,summary,[tabindex]):focus-visible{outline:2px solid var(--cyan);
  outline-offset:3px}
.skip{position:fixed;left:8px;top:-4rem;z-index:60;background:var(--red);
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
.sec{margin:3.4rem 0 0}
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
  background:var(--black);display:flex;flex-direction:column}
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

/* --------------------------------------------------------- 2. the calendar */
.cal{border-top:1px solid var(--line)}
.day{border-bottom:1px solid var(--line)}
.day>summary{display:grid;align-items:baseline;gap:.2rem 1rem;cursor:pointer;
  padding:.85rem .2rem;list-style:none;
  grid-template-columns:4.6rem 5.5rem minmax(0,1fr) max-content 1.4rem}
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
.tw{overflow-x:auto;margin:.8rem 0 1.4rem;border:1px solid var(--line)}
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
"""

JS = r"""
(function(){
  // Open a day (and scroll to it) when linked as /japan/music/#day-25.
  function openHash(){
    var id=location.hash.slice(1); if(!id) return;
    var el=document.getElementById(id); if(!el) return;
    if(el.tagName==='DETAILS') el.open=true;
    var p=el.parentElement;
    while(p){ if(p.tagName==='DETAILS') p.open=true; p=p.parentElement; }
  }
  window.addEventListener('hashchange',openHash);
  openHash();

  // Clamp the long section notes to two lines, click to open.
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=Shippori+Mincho:wght@500;700&display=swap">
<style>{CSS}</style></head>
<body>
<a class="skip" href="#five" aria-label="Skip to the top five"></a>
<header class="hero"><div class="inner">
{STANDFIRST}
<p class="jp1">\u65e5\u672c\u9650\u5b9a</p>
<details class="intro"><summary>The rules, and the two facts that shape the week</summary>
<div class="introbody">{INTRO_REST}</div></details>
</div></header>
<main class="wrap">

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
<div class="calnotebody">{SEC['5']['h2']}{LEAD_5}</div></details>
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
