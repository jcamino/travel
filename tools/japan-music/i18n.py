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


def inject(path: pathlib.Path) -> None:
    page = path.read_text(encoding="utf-8")
    if "jm-lang" in page:
        raise SystemExit("i18n.py: already injected; rebuild with akira-build.py first")
    # </script> inside a script literal would close the block early
    payload = json.dumps(MAP, ensure_ascii=False).replace("</", "<\\/")
    block = ("<style>" + CSS + "</style>\n<script>"
             + JS.replace("__MAP__", payload) + "</script>\n")
    assert page.count("</body>") == 1, "unexpected page shape"
    path.write_text(page.replace("</body>", block + "</body>"), encoding="utf-8",
                    newline="\n")
    jp = len(re.findall(r"[぀-ヿ㐀-鿿ｦ-ﾟ]+", page))
    print(f"wrote {path} (+{len(block)} bytes) | {len(MAP)} terms | "
          f"{jp} Japanese runs on the page")


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (
        HERE.parents[1] / "public" / "japan" / "music" / "index.html")
    inject(target)
