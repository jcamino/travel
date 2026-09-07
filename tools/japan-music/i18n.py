#!/usr/bin/env python3
"""English toggle for /japan/music.

Usage: python tools/japan-music/i18n.py public/japan/music/index.html

Injects a language toggle into a page already built by `akira-build.py`.
Every Japanese run on the page gets an English rendering from
`translations.json`; the toggle swaps between them and remembers the choice.

Why this is a separate step, and why the swap happens in the browser
-------------------------------------------------------------------
The served HTML keeps its Japanese text exactly as `akira-build.py` emitted
it. Wrapping the runs here, in the file, would break `content_check.py`:
that gate strips tags to a space and compares the result to the source, so
`御香宮神能『蝋燭能』` wrapped as two spans would read back as
`御香宮神能 『 蝋燭能` and no longer match the source line. Doing the wrap at
runtime sidesteps that completely -- the gate sees the page unchanged.

It also means the Japanese is never destroyed. That matters more than it
looks: you cannot ask for 幕見 at the Kabuki-za window by saying "single-act
gallery seat", and 予約〆切 is what you will actually see on a venue page.
English is the default because the reader cannot read Japanese; one tap puts
the original back for the moment you are standing at a counter.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
MAP = json.loads((HERE / "translations.json").read_text(encoding="utf-8"))
GLOSS = json.loads((HERE / "glossary.json").read_text(encoding="utf-8"))

# The page writes these with macrons; the glossary keys are typed without, so
# every surface form the prose actually uses has to point at the same entry.
ALIASES = {
    "kyogen": ["kyōgen"], "gidayu": ["gidayū"], "min'yo": ["min'yō"],
    "tayu": ["tayū"], "Tsugaru": ["Tsugaru shamisen"], "wadaiko": [],
    "jinjo": [], "live house": ["livehouse"], "78s": ["78-rpm", "78rpm"],
    "drink charge": ["drink charges"], "shrine": ["shrines"],
    "temple": ["temples"], "mikoshi": [], "kissa": ["kissaten"],
}
LOOKUP = {}
for _k, _v in GLOSS.items():
    for _form in [_k] + ALIASES.get(_k, []):
        LOOKUP[_form] = _k
# longest surface form first, so "meikyoku kissa" wins over "kissa" and
# "Tsugaru shamisen" over "shamisen"
LOOKUP = dict(sorted(LOOKUP.items(), key=lambda kv: (-len(kv[0]), kv[0])))

CSS = """
.langbar{display:flex;gap:0;align-items:center;margin:0 0 0 auto;
  border:1px solid var(--line);border-radius:2px;overflow:hidden;flex:0 0 auto}
.langbar button{appearance:none;background:transparent;border:0;cursor:pointer;
  font-family:"Big Shoulders Display",sans-serif;font-weight:800;font-size:.74rem;
  letter-spacing:.06em;text-transform:uppercase;color:var(--grey);
  padding:.28rem .55rem;line-height:1.5}
.langbar button[aria-pressed="true"]{background:var(--cyan);color:var(--black)}
.langbar button:focus-visible{outline:2px solid var(--red);outline-offset:-2px}
i.ja,i.en{font-style:normal}
body.lang-en i.ja{display:none}
body.lang-ja i.en{display:none}
/* A gloss is a definition ("matinee", "grand annual festival") and is marked
   as one; a romanised name ("Sat", "Mine Kosuke") is just the word, so it gets
   no marker. Python decides which by the case of the first letter. */
i.en.gloss{border-bottom:1px dotted rgba(138,140,144,.5)}
@media (max-width:520px){.langbar button{padding:.24rem .45rem;font-size:.7rem}}

/* A term you can ask about. Underlined rather than coloured, so a page that
   is already carrying red and cyan does not gain a third signal. */
button.gl{appearance:none;background:none;border:0;padding:0;margin:0;color:inherit;
  font:inherit;cursor:help;text-decoration:underline dotted var(--cyan);
  text-underline-offset:3px}
button.gl:hover,button.gl:focus-visible{color:var(--cyan);outline:none}
button.gl::after{content:"?";font-size:.62em;vertical-align:.45em;color:var(--cyan);
  margin-left:.1em;font-weight:700}

.glsheet{position:fixed;left:0;right:0;bottom:0;z-index:60;transform:translateY(101%);
  transition:transform .2s ease;background:#0d0f11;border-top:2px solid var(--cyan);
  padding:1rem 1.1rem 1.3rem;max-height:60vh;overflow:auto;
  box-shadow:0 -18px 40px rgba(0,0,0,.6)}
.glsheet[data-open="1"]{transform:translateY(0)}
.glsheet h4{margin:0 0 .5rem;font-family:"Big Shoulders Display",sans-serif;
  font-weight:900;text-transform:uppercase;letter-spacing:.04em;font-size:1.15rem;
  color:var(--cyan)}
.glsheet p{margin:0;max-width:42rem;line-height:1.55}
.glsheet button.glx{position:absolute;top:.5rem;right:.7rem;background:none;border:0;
  color:var(--grey);font-size:1.5rem;line-height:1;cursor:pointer}
@media(prefers-reduced-motion:reduce){.glsheet{transition:none}}

/* The bracketed gloss is the answer for most readers, so it is always there
   and never needs a tap. Dimmed so the sentence still reads as a sentence. */
.glx-in{color:var(--grey);font-size:.92em}
@media (max-width:520px){.glx-in{font-size:.88em}}
"""

JS = r"""
(function(){
  var MAP = __MAP__;
  var keys = Object.keys(MAP);           // already longest-first from Python
  if (!keys.length) return;
  var RE = new RegExp(keys.map(function(k){
    return k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }).join('|'), 'g');

  var CJK = /[぀-ヿ㐀-鿿ｦ-ﾟ々〆ヶ]/;
  // The weekday keys are single characters, so a bare `日` would also fire
  // inside 日本限定 and leave "Sun本限定" on the page. A one-character key only
  // counts when it is standing on its own, as it does in the day strip.
  function standsAlone(text, m){
    if (m[0].length > 1) return true;
    var before = m.index ? text[m.index - 1] : '';
    var after = text[m.index + m[0].length] || '';
    return !CJK.test(before) && !CJK.test(after);
  }

  var SKIP = {SCRIPT:1, STYLE:1, TEXTAREA:1, NOSCRIPT:1};
  function wrap(root){
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function(n){
        if (!n.nodeValue || !/[぀-ヿ㐀-鿿ｦ-ﾟ]/.test(n.nodeValue))
          return NodeFilter.FILTER_REJECT;
        var p = n.parentNode;
        while (p && p !== root){
          if (SKIP[p.nodeName] || (p.classList && p.classList.contains('i18n')))
            return NodeFilter.FILTER_REJECT;
          p = p.parentNode;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var todo = [], n;
    while ((n = walker.nextNode())) todo.push(n);
    todo.forEach(function(node){
      var text = node.nodeValue, out = null, last = 0, m;
      RE.lastIndex = 0;
      while ((m = RE.exec(text))){
        if (!standsAlone(text, m)) continue;
        out = out || document.createDocumentFragment();
        if (m.index > last) out.appendChild(document.createTextNode(text.slice(last, m.index)));
        var span = document.createElement('span');
        span.className = 'i18n';
        var ja = document.createElement('i'); ja.className = 'ja'; ja.textContent = m[0];
        var en = document.createElement('i');
        var v = MAP[m[0]];
        en.className = 'en' + (v[0] === v[0].toLowerCase() && v[0] !== v[0].toUpperCase()
                               ? ' gloss' : '');
        en.textContent = v;
        en.setAttribute('lang','en'); ja.setAttribute('lang','ja');
        span.appendChild(ja); span.appendChild(en);
        span.title = m[0] + ' — ' + MAP[m[0]];
        out.appendChild(span);
        last = m.index + m[0].length;
      }
      if (!out) return;
      if (last < text.length) out.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(out, node);
    });
  }

  // ---------------------------------------------------------- glossary
  var GL = __GLOSS__, GLKEYS = __GLKEYS__;
  var GRE = new RegExp('(^|[^A-Za-z’\'ōū])('
    + GLKEYS.map(function(k){ return k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).join('|')
    + ')(?![A-Za-z’ōū])', 'gi');

  // One mark per term per block. Marking all 19 "noh"s would be unreadable;
  // marking the first in each card puts the explanation where you are reading.
  var BLOCKS = '.plate, details.day, details.chunk, .acts, header.hero, .sec';
  function marklex(){
    var blocks = [].slice.call(document.querySelectorAll(BLOCKS));
    if (!blocks.length) blocks = [document.body];
    blocks.forEach(function(block){
      var seen = {};
      var walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
        acceptNode: function(n){
          if (!n.nodeValue || !/[A-Za-z]/.test(n.nodeValue)) return NodeFilter.FILTER_REJECT;
          var p = n.parentNode;
          while (p && p !== block){
            if (SKIP[p.nodeName] || p.nodeName === 'BUTTON'
                || (p.classList && (p.classList.contains('i18n')
                                 || p.classList.contains('ja')
                                 || p.classList.contains('en')
                                 || p.classList.contains('glx-in')
                                 || p.classList.contains('glsheet')
                                 || p.classList.contains('gllist'))))
              return NodeFilter.FILTER_REJECT;
            p = p.parentNode;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      });
      var todo = [], n;
      while ((n = walker.nextNode())) todo.push(n);
      todo.forEach(function(node){
        var text = node.nodeValue, out = null, last = 0, m;
        GRE.lastIndex = 0;
        while ((m = GRE.exec(text))){
          var key = GL[m[2].toLowerCase()];
          if (!key || seen[key]) continue;
          seen[key] = 1;
          out = out || document.createDocumentFragment();
          var upto = m.index + m[1].length;
          if (upto > last) out.appendChild(document.createTextNode(text.slice(last, upto)));
          var entry = __DEFS__[key];
          var b = document.createElement('button');
          b.type = 'button'; b.className = 'gl'; b.dataset.gl = key;
          b.textContent = m[2];
          // native tooltip on desktop; the sheet is the touch equivalent
          b.title = entry.long;
          b.setAttribute('aria-label', m[2] + ' — ' + entry.short);
          out.appendChild(b);
          if (entry.inline){
            var g = document.createElement('span');
            g.className = 'glx-in';
            g.textContent = ' (' + entry.short + ')';
            out.appendChild(g);
          }
          last = upto + m[2].length;
        }
        if (!out) return;
        if (last < text.length) out.appendChild(document.createTextNode(text.slice(last)));
        node.parentNode.replaceChild(out, node);
      });
    });
  }

  var sheet;
  function openGloss(key){
    if (!sheet) return;
    sheet.querySelector('h4').textContent = key;
    sheet.querySelector('p').textContent = (__DEFS__[key] || {}).long || '';
    sheet.dataset.open = '1';
    sheet.setAttribute('aria-hidden', 'false');
    sheet.querySelector('.glx').focus();
  }
  function closeGloss(){
    if (!sheet) return;
    sheet.dataset.open = '0';
    sheet.setAttribute('aria-hidden', 'true');
  }
  function buildSheet(){
    sheet = document.createElement('aside');
    sheet.className = 'glsheet'; sheet.dataset.open = '0';
    sheet.setAttribute('role', 'dialog');
    sheet.setAttribute('aria-label', 'Glossary');
    sheet.setAttribute('aria-hidden', 'true');
    sheet.innerHTML = '<button type="button" class="glx" aria-label="Close">&times;</button>'
                    + '<h4></h4><p></p>';
    document.body.appendChild(sheet);
    sheet.querySelector('.glx').addEventListener('click', closeGloss);
    document.addEventListener('click', function(e){
      var b = e.target.closest && e.target.closest('button.gl');
      if (b) { openGloss(b.dataset.gl); return; }
      if (sheet.dataset.open === '1' && !e.target.closest('.glsheet')) closeGloss();
    });
    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape') closeGloss();
    });
  }
  function setLang(lang){
    document.body.classList.toggle('lang-en', lang === 'en');
    document.body.classList.toggle('lang-ja', lang !== 'en');
    document.documentElement.lang = lang === 'en' ? 'en' : 'ja';
    var bar = document.querySelector('.langbar');
    if (bar) [].forEach.call(bar.querySelectorAll('button'), function(b){
      b.setAttribute('aria-pressed', String(b.dataset.lang === lang));
    });
    try { localStorage.setItem('jm-lang', lang); } catch (e) {}
    var live = document.getElementById('live');
    if (live) live.textContent = lang === 'en'
      ? 'Japanese names shown in English' : 'Original Japanese shown';
  }

  function init(){
    wrap(document.body);
    marklex();
    buildSheet();
    var sec = document.querySelector('.rail .rail-sec');
    if (sec){
      var bar = document.createElement('div');
      bar.className = 'langbar';
      bar.setAttribute('role','group');
      bar.setAttribute('aria-label','Language for Japanese names');
      bar.innerHTML = '<button type="button" data-lang="en">EN</button>'
                    + '<button type="button" data-lang="ja">日本語</button>';
      bar.addEventListener('click', function(e){
        var b = e.target.closest('button');
        if (b) setLang(b.dataset.lang);
      });
      sec.appendChild(bar);
    }
    var saved = null;
    try { saved = localStorage.getItem('jm-lang'); } catch (e) {}
    setLang(saved || 'en');
  }

  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', init);
  else init();
})();
"""


def _j(obj) -> str:
    """JSON for embedding in a <script>; `</` would close the block early."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def inject(path: pathlib.Path) -> None:
    page = path.read_text(encoding="utf-8")
    if "jm-lang" in page:
        raise SystemExit("i18n.py: already injected; rebuild with akira-build.py first")
    js = (JS.replace("__MAP__", _j(MAP))
            .replace("__GLOSS__", _j({k.lower(): v for k, v in LOOKUP.items()}))
            .replace("__GLKEYS__", _j(list(LOOKUP)))
            .replace("__DEFS__", _j(GLOSS)))
    for token in ("__MAP__", "__GLOSS__", "__GLKEYS__", "__DEFS__"):
        assert token not in js, f"{token} was never substituted"
    block = "<style>" + CSS + "</style>\n<script>" + js + "</script>\n"
    assert page.count("</body>") == 1, "unexpected page shape"
    path.write_text(page.replace("</body>", block + "</body>"), encoding="utf-8",
                    newline="\n")
    jp = len(re.findall(r"[぀-ヿ㐀-鿿ｦ-ﾟ]+", page))
    print(f"wrote {path} (+{len(block)} bytes) | {len(MAP)} terms | "
          f"{len(GLOSS)} glossary entries | {jp} Japanese runs on the page")


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (
        HERE.parents[1] / "public" / "japan" / "music" / "index.html")
    inject(target)
