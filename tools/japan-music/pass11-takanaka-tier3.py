# -*- coding: utf-8 -*-
"""Re-apply the Takanaka correction to the markdown source of truth.

The claim "never toured the United States" is false: takanaka.com/live lists
SUPER TAKANAKA WORLD LIVE 2026 (Brixton 31 Mar / 1 Apr, Brooklyn Paramount 4-5
Apr, Chicago, San Francisco, Hollywood Palladium, Sydney -- all sold out) and
The Wiltern, Los Angeles, 9-10 Mar 2025. He is Tier 3 on the page's own test and
leads section 0 only because the tickets are held. Also softens the other
never-abroad lines that were written without a source.

One-shot; run once, then delete or keep as a record. Every anchor must match once.
"""
import re, pathlib

P = pathlib.Path(__file__).with_name("japan-only-music-book.md")
s = P.read_text(encoding="utf-8")

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, "anchor x%d (want %d): %s" % (c, n, old[:100])
    s = s.replace(old, new)

# --- section 0 legend
rep('Ranked across the whole week, not one per day: first by how far each is from anything Brooklyn can offer, then by whether you can get in. Jazz and everything else compete',
    'Ranked across the whole week, not one per day: first by how far each is from anything Brooklyn can offer, then by whether you can get in. The first entry leads because the tickets are held; on the test alone Takanaka is Tier 3, having sold out Brooklyn Paramount in April. Jazz and everything else compete')

# --- section 0 card
rep('booked: the guitarist who has never played the United States, in a civic hall fifty minutes from Kyoto',
    'booked: the guitarist who sold out Brooklyn Paramount in April, five months later in a civic hall fifty minutes from Kyoto')
rep('{meta} {t2:Tier 2} · booked · {v:VERIFIED} [takanaka.com/live](https://takanaka.com/live/) (doors, start, price)',
    '{meta} {t3:Tier 3} (Brooklyn Paramount, 4–5 April 2026, sold out) · booked · {v:VERIFIED} [takanaka.com/live](https://takanaka.com/live/) (doors, start, price, and the world-tour dates)')
rep('**What it is.** Takanaka has made records since 1972 and has never toured the United States; the closest a New Yorker gets is the reissues.',
    '**What it is.** Takanaka has made records since 1972, and since the streaming revival he tours the world: SUPER TAKANAKA WORLD LIVE 2026 sold out two nights at London\'s O2 Academy Brixton, **two nights at Brooklyn Paramount on 4 and 5 April**, the Aragon Ballroom in Chicago, The Masonic in San Francisco, two nights at the Hollywood Palladium and two in Sydney, after two nights at the Wiltern in Los Angeles in March 2025. A Brooklyn resident could have walked to him this spring.')
rep('**Why it is first.** The ranking test is distance from Brooklyn, then whether you can get in. Takanaka is Tier 2 rather than Tier 1, but you hold the tickets, which no other entry on this page can say, and Tatsuro Yamashita below is the same kind of artist with no ticket. The cost is the harvest-moon rites, so this sat in section 3 until 6 Sept as "a Tier-2 legend on the wrong night".',
    '**Why it is first anyway.** The ranking test is distance from Brooklyn, then whether you can get in, and Takanaka fails the first half: he played Brooklyn five months ago, so he is Tier 3 here, exportable, in the same class as Boris and the Miles band. It leads the page because you hold the tickets, which no other entry can say, and because it takes the evening; on the test alone it would sit in section 3. The cost is the harvest-moon rites.')

# --- 0b Friday card, jazz sweep, must-surface card, Friday table
rep('{www} What: The fixed commitment: Takanaka\'s hall tour, グランドホール. {t2:Tier 2}',
    '{www} What: The fixed commitment: Takanaka\'s autumn hall tour, グランドホール. {t3:Tier 3}: he sold out Brooklyn Paramount on 4–5 April 2026')
rep('— Tier 2, never plays the US; booked on 6 Sept, overall #1 in section 0;',
    '— Tier 3 (SUPER TAKANAKA WORLD LIVE 2026 sold out Brooklyn Paramount on 4–5 April, after the Wiltern in March 2025); booked on 6 Sept, first in section 0 because it is booked;')
rep('He never tours the US. This conflicts with the moon rites;',
    'He sold out Brooklyn Paramount on 4–5 April 2026 on a world tour (London, Chicago, San Francisco, Los Angeles, Sydney), so on the test he is Tier 3; it leads section 0 because it is booked. This conflicts with the moon rites;')
rep('(Tier 2, never in the US) | Hikone (JR 50 min)', '(Tier 3: Brooklyn Paramount, April 2026) | Hikone (JR 50 min)')

# --- other never-abroad claims written without a source
rep('(tenor, b. 1944, on Tokyo stages since the 1960s, no US dates in decades)', '(tenor, b. 1944, on Tokyo stages since the 1960s)')
rep('Kosuke Mine has played tenor in Tokyo since the 1960s and has not played the US in decades.',
    'Kosuke Mine has played tenor in Tokyo since the 1960s and works the Tokyo rooms week in, week out.')
rep('who does not tour America;', 'who rarely plays outside Japan;')
rep('and he does not tour America.', 'and he rarely plays outside Japan.')
rep('he has not played New York in years)', 'based between Kansai and Berlin)')
rep('Kansai improviser who does not come to New York. Ligeti does play in New York.',
    'Kansai improviser, based between Osaka and Berlin. Ligeti is the New York-based half.')
rep('{t2:Tier 2} (they toured the US two decades ago; not since)', '{t2:Tier 2} (their US touring was around 2000)')

P.write_text(s, encoding="utf-8")
left = re.findall(r"never (?:toured|played|plays|tours|in) the (?:US|United States)|no US dates|not played the US|does not tour America|does not come to New York", s)
print("written:", P, "| never-in-the-US phrasings left:", left)
