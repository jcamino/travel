from pathlib import Path
live = Path("public/japan/music/index.html").read_text(encoding="utf-8")
n = Path("public/japan/music-4.6/index.html").read_text(encoding="utf-8")
print("live book id", 'id="book"' in live)
print("4.6 book id", 'id="book"' in n)
print("4.6 plates", n.count('class="plate'))
print("live ranked", "Ranked shortlist" in live)
print("4.6 ranked", "Ranked shortlist" in n)
