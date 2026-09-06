#!/usr/bin/env python3
"""Content-preservation gate for redesigns of /japan/music.

Usage: python tests/japan-music/content_check.py public/japan/music-moon/index.html

Checks that the redesigned page still carries every text fragment and every
outbound link of the source page (public/japan/music/index.html). The design
may add navigation labels, reorder sections, and re-render tags as stamps or
glyphs, but it may not drop or paraphrase research content.

Exit 0 when clean, 1 with a list of missing fragments / links otherwise.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "public" / "japan" / "music" / "index.html"


def strip(page: str) -> str:
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<[^>]+>", " ", page)
    page = html.unescape(page)
    page = page.replace(" ", " ")
    return re.sub(r"\s+", " ", page).strip()


def fragments(text: str, minlen: int = 24):
    """Split into sentence-ish fragments long enough to be unambiguous."""
    parts = re.split(r"(?<=[.。!?！？])\s+|\s·\s|\s—\s|\s\|\s", text)
    out = []
    for p in parts:
        p = p.strip(" ·—|")
        if len(p) >= minlen:
            out.append(p)
    return out


def links(page: str):
    return set(re.findall(r'href="(https?://[^"]+)"', page))


def main(target: str) -> int:
    src = SOURCE.read_text(encoding="utf-8")
    dst = Path(target).read_text(encoding="utf-8")
    src_text, dst_text = strip(src), strip(dst)

    # Tags that a redesign is allowed to re-render as glyphs/stamps: removed
    # from both sides before comparing.
    allowed_drop = ["VERIFIED", "SECONDARY", "Tier 1", "Tier 2", "Tier 3"]
    for tag in allowed_drop:
        src_text = src_text.replace(tag, " ")
        dst_text = dst_text.replace(tag, " ")
    src_text = re.sub(r"\s+", " ", src_text)
    dst_flat = re.sub(r"\s", "", dst_text)

    missing = []
    for frag in fragments(src_text):
        # compare on a whitespace-insensitive basis
        if re.sub(r"\s", "", frag) not in dst_flat:
            missing.append(frag)

    lost_links = sorted(links(src) - links(dst))

    src_words, dst_words = len(src_text.split()), len(dst_text.split())
    print(f"source words {src_words}, target words {dst_words}")
    print(f"fragments checked {len(fragments(src_text))}, missing {len(missing)}")
    print(f"links in source {len(links(src))}, lost {len(lost_links)}")
    for m in missing[:60]:
        print("  MISSING:", m[:160])
    for l in lost_links[:60]:
        print("  LOST LINK:", l)
    if len(missing) > 60 or len(lost_links) > 60:
        print("  ... (truncated)")
    return 0 if not missing and not lost_links else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
