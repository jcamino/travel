# -*- coding: utf-8 -*-
"""Build /japan from trip.md.

`page.html` is the page: markup, styles, and the code that renders a day.
`trip.md` is the trip. This puts the second inside the first, in place of
the MARKER line, and writes public/japan/index.html.

Usage: python tools/japan/build.py [output.html]
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tripbook  # noqa: E402

ROOT = HERE.parents[1]
MARKER = '/* TRIP GOES HERE, FROM trip.md */'
DST = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (
    ROOT / 'public' / 'japan' / 'index.html')

trip = tripbook.load(HERE / 'trip.md')
page = (HERE / 'page.html').read_text(encoding='utf-8')
assert page.count(MARKER) == 1, 'page.html has no single TRIP marker'
out = page.replace(MARKER, tripbook.trip_js(trip))

DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_text(out, encoding='utf-8', newline='\n')
print('wrote %s, %d bytes, %d days, %d items'
      % (DST, len(out), len(trip['days']),
         sum(len(d['items']) for d in trip['days'])))
