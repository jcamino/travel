# -*- coding: utf-8 -*-
"""The markdown dialect behind the Japan-only music book.

`japan-only-music-book.md` next to this file is the source of truth for
/japan/music: the research prose, plus the editorial data (the five flyer
faces, the calendar row for each day) that used to sit hardcoded in
`akira-build.py`. This module is the only thing that knows the dialect;
`akira-build.py` asks it for the front matter and the body HTML and then
does the design. The research notebook the book was written from — raw
fetches, the pass scripts, the redesign plans — stays outside this repo in
`Code/japan/music/japan-only/`.

The dialect is line-oriented and lossless: one markdown line is one HTML
line, in order, so a diff of the source reads as a diff of the page.

  # / ## / ###          h1 / h2 / h3
  {kicker} ...          <div class="kicker">
  {note} ...            <div class="note">
  {lede} / {legend}     <p class="lede"> / <p class="legend">
  {meta} / {also}       <p class="meta"> / <p class="also">
  {small} ...           <p><small>...</small></p>
  anything else         <p>...</p>
  {cards} {cards night} <div class="cards"> / <div class="cards night">
  {card} Title          <div class="card"><h3>Title</h3>
  {card flag} Title     <div class="card flagcard"><h3>Title</h3>
  {www} What: a | When: b | Where: c | Cost: d
  {ul} / {ol}, "- x"    lists
  {table}, "| a | b |"  a <div class="tw"><table>; the first row is the header
  {/card} {/cards} ...  close the block

Inline, in any text: **strong**, *em*, `code`, [text](url), and the badges
{v:VERIFIED}, {s:SECONDARY}, {t1:Tier 1}, {t2:...}, {t3:...}, {smp:SAMPLER}.
A literal & is written as &; the renderer escapes it. None of the characters
* ` [ ] { } | occur in the book's own text, which is what lets the mapping be
reversible with no escaping at all.
"""
import json
import re

BADGES = ('v', 's', 't1', 't2', 't3', 'smp')
WWW_KEYS = ('What', 'When', 'Where', 'Cost')

# ----------------------------------------------------------------- inline


def _unent(t):
    return t.replace('&amp;', '&')


def _ent(t):
    return t.replace('&', '&amp;')


_TAG = re.compile(r'<(/?)(a|strong|em|code|span)\b([^>]*)>')
_HREF = '<a href="%%s">'


def inline_to_md(html):
    """One HTML inline run -> markdown."""
    out, pos, stack = [], 0, []
    for m in _TAG.finditer(html):
        out.append(_unent(html[pos:m.start()]))
        pos = m.end()
        closing, tag, attrs = m.group(1), m.group(2), m.group(3)
        if closing:
            open_tag, mark = stack.pop()
            assert open_tag == tag, (open_tag, tag, html[:80])
            out.append(mark)
            continue
        if tag == 'strong':
            out.append('**')
            stack.append((tag, '**'))
        elif tag == 'em':
            out.append('*')
            stack.append((tag, '*'))
        elif tag == 'code':
            out.append('`')
            stack.append((tag, '`'))
        elif tag == 'a':
            href = re.search(r'href="([^"]*)"', attrs).group(1)
            out.append('[')
            stack.append((tag, '](%s)' % _unent(href)))
        elif tag == 'span':
            cls = re.search(r'class="([^"]*)"', attrs)
            assert cls and cls.group(1) in BADGES, attrs
            out.append('{%s:' % cls.group(1))
            stack.append((tag, '}'))
    assert not stack, stack
    out.append(_unent(html[pos:]))
    return ''.join(out)


_MD = re.compile(r'\*\*|\*|`|\[|\]\(([^)]*)\)|\{(' + '|'.join(BADGES)
                 + r'):|\}')


def inline_to_html(md):
    """One markdown inline run -> HTML. Exact inverse of inline_to_md."""
    out, pos, stack = [], 0, []
    for m in _MD.finditer(md):
        out.append(_ent(md[pos:m.start()]))
        pos = m.end()
        tok = m.group(0)
        if tok in ('**', '*', '`'):
            name = {'**': 'strong', '*': 'em', '`': 'code'}[tok]
            if stack and stack[-1] == name:
                stack.pop()
                out.append('</%s>' % name)
            else:
                stack.append(name)
                out.append('<%s>' % name)
        elif tok == '[':
            stack.append('a')
            out.append(_HREF)
        elif tok == '}':
            assert stack and stack[-1] == 'span', stack
            stack.pop()
            out.append('</span>')
        elif m.group(1) is not None:            # ](url) closes the link
            assert stack and stack[-1] == 'a', stack
            stack.pop()
            for i in range(len(out) - 1, -1, -1):
                if out[i] == _HREF:
                    out[i] = '<a href="%s">' % _ent(m.group(1))
                    break
            out.append('</a>')
        else:                                   # {badge:
            stack.append('span')
            out.append('<span class="%s">' % m.group(2))
    assert not stack, stack
    out.append(_ent(md[pos:]))
    return ''.join(out)


# ------------------------------------------------------------------ blocks
#
# One markdown line is one HTML line, with two structural exceptions:
#   * {/card} closes onto the end of the line before it, the way the book has
#     always been written (`...</p></div>`);
#   * a line marked ^ is glued onto the line before it instead of starting a
#     new one. Only the flag cards use it, to keep What/When/Where/Cost and
#     the paragraph under it on one line.

GLUE = '^'


def _cells_to_md(row_html):
    out = []
    for m in re.finditer(r'<t([dh])(?: class="([^"]*)")?>(.*?)</t\1>',
                         row_html, re.S):
        cls, inner = m.group(2), m.group(3)
        assert inner == inner.strip(), repr(inner)
        assert cls in (None, 'day'), cls
        text = inline_to_md(inner)
        assert not text.startswith('.day '), text
        out.append(('.day ' if cls == 'day' else '') + text)
    return '| ' + ' | '.join(out) + ' |'


def _md_to_row(line, header):
    body = line.strip()
    assert body.startswith('|') and body.endswith('|'), line
    out = []
    for cell in (c.strip() for c in body[1:-1].split('|')):
        if cell.startswith('.day '):
            out.append('<td class="day">%s</td>' % inline_to_html(cell[5:]))
        else:
            tag = 'th' if header else 'td'
            out.append('<%s>%s</%s>' % (tag, inline_to_html(cell), tag))
    return '<tr>%s</tr>' % ''.join(out)


def _www_to_md(inner):
    """Split <b>What</b><span>..</span>.. into its four values.

    The values carry tier badges of their own, so the closing </span> has to
    be found by balancing rather than by a non-greedy match.
    """
    pairs, pos = [], 0
    while pos < len(inner):
        m = re.compile(r'<b>(.*?)</b><span>').match(inner, pos)
        assert m, inner[pos:pos + 60]
        depth, scan = 1, m.end()
        while depth:
            nxt = re.compile(r'</?span\b[^>]*>').search(inner, scan)
            depth += -1 if nxt.group(0).startswith('</') else 1
            scan = nxt.end()
        pairs.append((m.group(1), inner[m.end():scan - len('</span>')]))
        pos = scan
    assert tuple(k for k, _ in pairs) == WWW_KEYS, [k for k, _ in pairs]
    return ' | '.join('%s: %s' % (k, inline_to_md(v)) for k, v in pairs)


def _md_to_www(text):
    parts = text.split(' | ')
    assert len(parts) == len(WWW_KEYS), parts
    out = []
    for key, part in zip(WWW_KEYS, parts):
        assert part.startswith(key + ': '), (key, part[:40])
        out.append('<b>%s</b><span>%s</span>'
                   % (key, inline_to_html(part[len(key) + 2:])))
    return '<p class="www">%s</p>' % ''.join(out)


# Tried in order against the cursor. </div> is handled separately, because
# whether it closes a card or a card list depends on what is open.
_BLOCKS = [
    (re.compile(r'<h([123])>(.*?)</h\1>'),
     lambda m: '#' * int(m.group(1)) + ' ' + inline_to_md(m.group(2))),
    (re.compile(r'<div class="(kicker|note)">(.*?)</div>'),
     lambda m: '{%s} %s' % (m.group(1), inline_to_md(m.group(2)))),
    (re.compile(r'<div class="card( flagcard)?"><h3>(.*?)</h3>'),
     lambda m: '{card%s} %s' % (' flag' if m.group(1) else '',
                                inline_to_md(m.group(2)))),
    (re.compile(r'<div class="cards( night)?">'),
     lambda m: '{cards%s}' % (' night' if m.group(1) else '')),
    (re.compile(r'<div class="tw"><table>'), lambda m: '{table}'),
    (re.compile(r'</table></div>'), lambda m: '{/table}'),
    (re.compile(r'<(ul|ol)>'), lambda m: '{%s}' % m.group(1)),
    (re.compile(r'</(ul|ol)>'), lambda m: '{/%s}' % m.group(1)),
    (re.compile(r'<li>(.*?)</li>'), lambda m: '- ' + inline_to_md(m.group(1))),
    (re.compile(r'<tr>.*?</tr>'), lambda m: _cells_to_md(m.group(0))),
    (re.compile(r'<p class="www">(.*?)</p>'),
     lambda m: '{www} ' + _www_to_md(m.group(1))),
    (re.compile(r'<p class="(lede|legend|meta|also)">(.*?)</p>'),
     lambda m: '{%s} %s' % (m.group(1), inline_to_md(m.group(2)))),
    (re.compile(r'<p><small>(.*?)</small></p>'),
     lambda m: '{small} ' + inline_to_md(m.group(1))),
    (re.compile(r'<p>(.*?)</p>'), lambda m: inline_to_md(m.group(1))),
]


def html_to_md(body):
    """The book's body HTML -> markdown. Inverse of md_to_html."""
    md, opened = [], []
    for line in body.split('\n'):
        if not line:
            md.append('')
            continue
        pos, first = 0, True
        while pos < len(line):
            rest = line[pos:]
            if rest.startswith('</div>'):
                md.append('{/card}' if opened.pop() == 'card' else '{/cards}')
                pos += len('</div>')
                first = False
                continue
            for pattern, build in _BLOCKS:
                m = pattern.match(rest)
                if m:
                    break
            assert m, rest[:120]
            token = build(m)
            if token.startswith('{card}') or token.startswith('{card flag}'):
                opened.append('card')
            elif token.startswith('{cards'):
                opened.append('cards')
            md.append(token if first else GLUE + token)
            pos += m.end()
            first = False
    assert not opened, opened
    return '\n'.join(md)


def md_to_html(md):
    """Markdown -> the book's body HTML. Inverse of html_to_md."""
    out, table = [], 0          # table: 0 none, 1 expecting header, 2 rows
    for raw in md.split('\n'):
        if not raw:
            out.append('')
            continue
        glue = raw.startswith(GLUE)
        line = raw[1:] if glue else raw

        if table:
            if line == '{/table}':
                table, html = 0, '</table></div>'
            else:
                html = _md_to_row(line, header=table == 1)
                glue = table == 1       # the header rides the <table> line
                table = 2
        elif line == '{table}':
            out.append('<div class="tw"><table>')
            table = 1
            continue
        elif line == '{/card}':
            out[-1] += '</div>'
            continue
        elif line == '{/cards}':
            html = '</div>'
        elif line in ('{ul}', '{ol}'):
            html = '<%s>' % line[1:-1]
        elif line in ('{/ul}', '{/ol}'):
            html = '</%s>' % line[2:-1]
        elif line in ('{cards}', '{cards night}'):
            html = '<div class="cards%s">' % (
                ' night' if line.endswith('night}') else '')
        elif line.startswith('### '):
            html = '<h3>%s</h3>' % inline_to_html(line[4:])
        elif line.startswith('## '):
            html = '<h2>%s</h2>' % inline_to_html(line[3:])
        elif line.startswith('# '):
            html = '<h1>%s</h1>' % inline_to_html(line[2:])
        elif line.startswith('- '):
            html = '<li>%s</li>' % inline_to_html(line[2:])
        elif line.startswith('{card} ') or line.startswith('{card flag} '):
            flag = line.startswith('{card flag} ')
            html = '<div class="card%s"><h3>%s</h3>' % (
                ' flagcard' if flag else '',
                inline_to_html(line.split('} ', 1)[1]))
        elif line.startswith('{www} '):
            html = _md_to_www(line[6:])
        elif line.startswith('{small} '):
            html = '<p><small>%s</small></p>' % inline_to_html(line[8:])
        elif re.match(r'\{(kicker|note)\} ', line):
            key = line[1:line.index('}')]
            html = '<div class="%s">%s</div>' % (
                key, inline_to_html(line[len(key) + 3:]))
        elif re.match(r'\{(lede|legend|meta|also)\} ', line):
            key = line[1:line.index('}')]
            html = '<p class="%s">%s</p>' % (
                key, inline_to_html(line[len(key) + 3:]))
        else:
            html = '<p>%s</p>' % inline_to_html(line)

        if glue:
            out[-1] += html
        else:
            out.append(html)
    assert not table, 'unclosed {table}'
    return '\n'.join(out)


# ------------------------------------------------------------- the source

FENCE = '---'


def split_source(text):
    """The .md text -> (front matter dict, markdown body)."""
    assert text.startswith(FENCE + '\n'), 'no front matter'
    head, sep, body = text[len(FENCE) + 1:].partition('\n' + FENCE + '\n')
    assert sep, 'front matter is not closed'
    return json.loads(head), body


def join_source(meta, md_body):
    """(front matter dict, markdown body) -> the .md text."""
    return '%s\n%s\n%s\n%s' % (
        FENCE, json.dumps(meta, ensure_ascii=False, indent=2), FENCE, md_body)


def check(path):
    """Render the source and read it back; the markdown must come out the same.

    Anything the dialect cannot express round-trips to something else, so this
    catches a hand edit that breaks the mapping before the page is built.
    Usage: python tools/japan-music/mdbook.py [source.md]
    """
    meta, body_md = split_source(path.read_text(encoding='utf-8'))
    again = html_to_md(md_to_html(body_md))
    if again == body_md:
        print('%s: %d lines, round trip exact' % (path.name,
                                                  body_md.count('\n') + 1))
        return 0
    for n, (a, b) in enumerate(zip(body_md.split('\n'), again.split('\n')), 1):
        if a != b:
            print('%s:%d does not round trip' % (path.name, n))
            print('  source:  %s' % a[:160])
            print('  rebuilt: %s' % b[:160])
            return 1
    print('%s: line count changed, %d -> %d'
          % (path.name, body_md.count('\n') + 1, again.count('\n') + 1))
    return 1


if __name__ == '__main__':
    import pathlib
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    default = (pathlib.Path(__file__).resolve().parent
               / 'japan-only-music-book.md')
    sys.exit(check(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else default))
