# HANDOFF — the copy pass owed on `japan-only-music-book.md`

**One job:** run a declaude / copy pass over the ~41 lines of
`tools/japan-music/japan-only-music-book.md` that were written *after* the last
copy pass, then rebuild. Nothing else in the book is owed a pass.

## Why only 41 lines

The book has had four copy passes, all of them on the *full research dump*:

| Commit | Pass |
|---|---|
| `426c1f0` | declaude copy edits (Gemini Pro + Flash, reviewed) |
| `e882bae` | Gemini 3.8 Flash detector pass (reviewed) |
| `0f09a84` | strip planning narration for a reader outside the planning |
| `ed0f98a` | copy pass over both sources ← **the last one** |

Three commits landed *after* `ed0f98a` and are in the live source today:

| Commit | What it did |
|---|---|
| `f9be760` | Takanaka corrected to Tier 3 (he sold out Brooklyn Paramount, 4–5 Apr 2026) |
| `ece6ef6` | renumbered the sections (−391 lines) |
| `44341d6` | the traveler cut: dropped the research dump, **wrote `1 · Book before you fly` from scratch**, rewrote both ledes and several legends |

So the reorganisation *is* done and the declaude *is* done — but they happened in
that order, and the prose the reorganisation introduced never went back through a
pass. That is the whole gap.

## Get the exact lines

    git diff ed0f98a HEAD -- tools/japan-music/japan-only-music-book.md \
      | grep '^+[^+]' | sed 's/^+//' | grep -v '^\s*$'

41 lines, which break down as:

- **14 `- ` list items** — the whole of `1 · Book before you fly` (deadlines,
  phone numbers, which ticket systems refuse a foreign card). Highest value and
  the most likely to have drifted, since it was written in one go.
- **7 `{card}` titles**, **4 `{www}`** What/When/Where lines, **1 `{meta}`**
- **4 `{legend}`** section standfirsts and **2 `{lede}`** — the top of the page
- **4 `## ` / 1 `### `** headings from the renumber
- **2 bold-lead paragraphs** on Takanaka (`**What it is.**`,
  `**Why it is first anyway.**`) from `f9be760`
- **1 table row**, **1 JSON front-matter key** (`"tier": "Tier 3"` — data, skip it)

On a skim these read clean: concrete, sourced, no puffery. They have simply never
been checked, so do not assume.

## Constraints that bite

- **The dialect is reversible and the gate enforces it.** One markdown line
  renders to one HTML line. Do not introduce `` * ` [ ] { } | `` into prose —
  there is no escaping mechanism, and none is needed, which is what makes the
  round trip exact. See "The dialect" in `README.md`.
- **`content_check.py` compares source words to page words.** It will fail on a
  dropped link or a lost checked fragment, so edit wording, never structure.
- **Do not touch the JSON front matter.** It carries the trip shape and the
  flyer faces, and `akira-build.py` asserts on it.

## Run it

    python tools/japan-music/mdbook.py                                   # round trip must be exact
    python tools/japan-music/akira-build.py public/japan/music/index.html
    python tests/japan-music/content_check.py public/japan/music/index.html

All three must be green before committing. Current baseline to beat:

    japan-only-music-book.md: 374 lines, round trip exact
    fragments checked 576, missing 0
    links in source 49, lost 0
    musicrefs 10, missing 0

The `declaude` skill is the intended tool for the pass itself.
