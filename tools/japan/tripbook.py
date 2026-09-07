# -*- coding: utf-8 -*-
"""The markdown dialect behind /japan, and the TRIP literal it renders to.

`trip.md` is the source of truth for the trip: front matter for what
describes the whole week, then one section per day and one block per item.
`build.py` asks this module for the data and writes it into `page.html` as
the TRIP object the page renders from.

The dialect is line-oriented and lossless:

  ## 2026-09-19 | Sat | 19 | Tokyo | Arrive Tokyo
  {base} Hotel Son Shibuya
  {daynote} ...                      repeatable, optional

  ### 15:00 | Both in Tokyo by about 15:00
  {status} decided
  {end} 16:44                        optional
  {approx} {music} {travel}          flags, present or absent
  {ticket} pending                   optional
  {detail} ...                       always present, may be empty
  {place} ... {map} ... {url} ...    always present, may be empty
  {musicref} ...                     optional
  {extramap} label | query           optional
  {conf} ... {via} ... {car} ...     optional, may be empty
  - a note                           repeatable

The JS is emitted in one fixed shape, a key group per line and every non-empty
note on its own line, so editing one note is a one-line diff. None of the
characters * ` [ ] { } | occurs in the trip's own text, so the markers need no
escaping; a " is written plainly here and escaped on the way into JS.
"""
import json
import re

FENCE = '---'
HEAD = ['time', 'endTime', 'approx', 'title', 'status', 'ticket', 'music',
        'travel']
TAIL = ['conf', 'via', 'car']
FLAGS = ['approx', 'music', 'travel']
DAY_HEAD = ['date', 'weekday', 'label', 'city', 'theme']
# marker -> key, for the one-value lines
VALUE = [('status', 'status'), ('end', 'endTime'), ('ticket', 'ticket'),
         ('detail', 'detail'), ('musicref', 'musicRef'), ('conf', 'conf'),
         ('via', 'via'), ('car', 'car')]
TO_KEY = dict(VALUE)


# --------------------------------------------------------------- to the page

def _s(v):
    return '"%s"' % v.replace('\\', '\\\\').replace('"', '\\"')


def _v(v):
    if v is True:
        return 'true'
    if isinstance(v, dict):
        return '{ %s }' % ', '.join('%s: %s' % (k, _s(x)) for k, x in v.items())
    return _s(v)


def _group(item, keys, indent, open_brace=False):
    bits = ['%s: %s' % (k, _v(item[k])) for k in keys if k in item]
    if not bits:
        return []
    return ['%s%s%s,' % (' ' * indent, '{ ' if open_brace else '',
                         ', '.join(bits))]


def item_js(item, last):
    out = _group(item, HEAD, 8, open_brace=True)
    out += _group(item, ['detail'], 10)
    out += _group(item, ['place', 'mapQuery', 'url'], 10)
    out += _group(item, ['musicRef'], 10)
    out += _group(item, ['extraMap'], 10)
    if item['notes']:
        out.append(' ' * 10 + 'notes: [')
        for n in item['notes'][:-1]:
            out.append(' ' * 12 + _s(n) + ',')
        out.append(' ' * 12 + _s(item['notes'][-1]))
        out.append(' ' * 10 + ']' + (',' if any(k in item for k in TAIL)
                                     else ''))
    else:
        out.append(' ' * 10 + 'notes: []'
                   + (',' if any(k in item for k in TAIL) else ''))
    tail = _group(item, TAIL, 10)
    if tail:
        out.append(tail[0][:-1])
    out[-1] += ' }' if last else ' },'
    return out


def trip_js(trip):
    """The TRIP object literal, in the one shape this module writes."""
    L = ['const TRIP = {']
    for k in ('title', 'dates', 'who'):
        L.append('  %s: %s,' % (k, _s(trip[k])))
    L.append('  about: [')
    for a in trip['about'][:-1]:
        L.append('    %s,' % _s(a))
    L.append('    %s' % _s(trip['about'][-1]))
    L.append('  ],')
    L.append('  legend: {')
    pairs = list(trip['legend'].items())
    for k, v in pairs[:-1]:
        L.append('    %s: %s,' % (k, _s(v)))
    L.append('    %s: %s' % (pairs[-1][0], _s(pairs[-1][1])))
    L.append('  },')
    L.append('  holidays: [%s],' % ', '.join(_s(h) for h in trip['holidays']))
    L.append('  musicPage: %s,' % _s(trip['musicPage']))
    L.append('  days: [')
    for n, d in enumerate(trip['days']):
        L.append('    {')
        L.append('      %s,' % ', '.join(
            '%s: %s' % (k, _s(d[k]))
            for k in ('date', 'label', 'weekday', 'city', 'theme')))
        L.append('      base: %s,' % _s(d['base']))
        if 'dayNotes' in d:
            L.append('      dayNotes: [%s],'
                     % ', '.join(_s(x) for x in d['dayNotes']))
        L.append('      items: [')
        for i, item in enumerate(d['items']):
            L += item_js(item, i == len(d['items']) - 1)
        L.append('      ]')
        L.append('    }' + ('' if n == len(trip['days']) - 1 else ','))
    L.append('  ],')
    L.append('  openItems: %s' % json.dumps(trip['openItems'],
                                            ensure_ascii=False))
    L.append('};')
    return '\n'.join(L)


# ------------------------------------------------------------ to the markdown

def trip_to_md(trip):
    out = []
    for d in trip['days']:
        out.append('## %s' % ' | '.join(d[k] for k in DAY_HEAD))
        out.append('{base} %s' % d['base'])
        for n in d.get('dayNotes', []):
            out.append('{daynote} %s' % n)
        for item in d['items']:
            out.append('')
            out.append('### %s | %s' % (item['time'], item['title']))
            flags = ' '.join('{%s}' % f for f in FLAGS if f in item)
            if flags:
                out.append(flags)
            for marker, key in VALUE:
                if key in item:
                    out.append(('{%s} %s' % (marker, item[key])).rstrip())
            out.append(('{place} %s' % item['place']).rstrip())
            out.append(('{map} %s' % item['mapQuery']).rstrip())
            out.append(('{url} %s' % item['url']).rstrip())
            if 'extraMap' in item:
                out.append('{extramap} %s | %s' % (item['extraMap']['label'],
                                                   item['extraMap']['query']))
            for n in item['notes']:
                out.append('- %s' % n)
        out.append('')
    return '\n'.join(out).rstrip() + '\n'


def md_to_trip(meta, md):
    trip = dict(meta)
    trip['days'] = days = []
    day = item = None
    for raw in md.split('\n'):
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith('## '):
            parts = [p.strip() for p in line[3:].split(' | ')]
            assert len(parts) == len(DAY_HEAD), parts
            day = dict(zip(DAY_HEAD, parts))
            day = {k: day[k] for k in
                   ('date', 'label', 'weekday', 'city', 'theme')}
            day['items'] = []
            days.append(day)
            item = None
        elif line.startswith('### '):
            time, _, title = line[4:].partition(' | ')
            item = {'time': time.strip(), 'title': title.strip(),
                    'notes': []}
            day['items'].append(item)
        elif line.startswith('- '):
            item['notes'].append(line[2:])
        elif re.fullmatch(r'\{(?:approx|music|travel)\}'
                          r'(?: \{(?:approx|music|travel)\})*', line):
            for f in re.findall(r'\{(\w+)\}', line):
                item[f] = True
        else:
            m = re.match(r'\{(\w+)\}(?: (.*))?$', line)
            assert m, line[:60]
            marker, value = m.group(1), m.group(2) or ''
            if marker == 'base':
                day['base'] = value
            elif marker == 'daynote':
                day.setdefault('dayNotes', []).append(value)
            elif marker == 'extramap':
                label, _, query = value.partition(' | ')
                item['extraMap'] = {'label': label, 'query': query}
            elif marker == 'place':
                item['place'] = value
            elif marker == 'map':
                item['mapQuery'] = value
            elif marker == 'url':
                item['url'] = value
            else:
                assert marker in TO_KEY, line[:60]
                item[TO_KEY[marker]] = value
    # put every item's keys back into the page's own order
    order = HEAD + ['detail', 'place', 'mapQuery', 'url', 'musicRef',
                    'extraMap', 'notes'] + TAIL
    for d in days:
        d['items'] = [{k: it[k] for k in order if k in it} for it in d['items']]
    return trip


# --------------------------------------------------------------- the source

def split_source(text):
    assert text.startswith(FENCE + '\n'), 'no front matter'
    head, sep, body = text[len(FENCE) + 1:].partition('\n' + FENCE + '\n')
    assert sep, 'front matter is not closed'
    return json.loads(head), body


def join_source(trip):
    meta = {k: v for k, v in trip.items() if k != 'days'}
    return '%s\n%s\n%s\n%s' % (FENCE,
                               json.dumps(meta, ensure_ascii=False, indent=2),
                               FENCE, trip_to_md(trip))


def load(path):
    meta, body = split_source(path.read_text(encoding='utf-8'))
    return md_to_trip(meta, body)
