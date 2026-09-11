# Book: Shinjuku Pit Inn 昼の部, Sun 20 Sept 2026

> **STATUS: CONFIRMED. 予約完了メール received 2026-09-11, 2 seats, Sun 20
> Sept daytime show.** It says the tickets are already held under the booking
> name: give the name at reception, buy them before doors, enter in ticket
> order. It carries **no 整理番号** and no reservation number.
>
> It also gives **doors 13:30, music 14:00**, which contradicts the venue's own
> page for this date (**Open 14:00 / Start 14:30**, re-checked 2026-09-11).
> 13:30/14:00 are Pit Inn's ordinary 昼の部 times, used by every other matinee
> that month, so the mail reads like a template. Be at the desk from 13:00 and
> the question does not arise. See "Check afterwards".

Reserve **2 seats** at the Sunday matinee, 東京民謡倶楽部, inside Marty
Holoubek's 3 Days / 6 Concerts residency. Read on the venue's own page
2026-09-07; every fact below came off that page, not the music book.

- Show page: https://pit-inn.com/artist_live_info/260920hirumarty/
- 新宿ピットイン, 〒160-0022 東京都新宿区新宿2-12-4 アコード新宿B1
- tel 03-3354-2024, the 1965 basement
- Open 14:00 / Start 14:30, about two hours
- 前売 **¥5,500 tax incl.** (¥5,000 + tax), one drink included
- 当日 ¥6,050 tax incl. Two advance tickets = **¥11,000**
- On sale, no sold-out marker as of 2026-09-07

## No money moves online

The form is a *reservation*, not a purchase. Nothing is charged, no card is
entered, and there is no payment page to stop before. You pay at the Pit Inn
counter on the day. The usual card discipline does not apply here because
there is nothing to protect.

## The route

Three official routes; the venue lists no email address.

1. **Web form** (use this). On the show page, click **▶チケット予約フォーム**.
   It POSTs `artist_name` / `live_date` / `live_time` to
   `https://pit-inn.com/reservation`, which renders the real form with those
   three fields pre-filled and read-only. Confirm they read:
   - `artist_name` = `Marty Holoubek 3 Days 6 Concerts 2026`
   - `live_date` = `2026年9月20日（Sun）`
   - `live_time` = `Open14:00/Start14:30`
2. **Phone** 03-3354-2024, Japanese only.
3. **Counter** at the venue, any day before the show.

## The form

Contact Form 7. Required unless marked optional.

| Field | Name | Value |
|---|---|---|
| 代表者のお名前 | `your-name` | Javier Camino |
| フリガナ | `your-furigana` | ハビエル カミーノ |
| メールアドレス | `your-email` | javier032@gmail.com |
| ご予約数 | `number-623` | `2` |
| ご意見・ご希望 | `textbox` | optional; leave blank |
| 表示された英数字 | `captcha-644` | read off the image |

**The CAPTCHA is an image**, paired with a hidden
`_wpcf7_captcha_challenge_captcha-644` token. It cannot be solved headlessly, so
this is a browser job: drive a CDP Chrome on `:9333`, or just do it by hand. Do
not burn time trying to script past it. (`:9334` is a watcher, leave it alone.)

フリガナ is mandatory and expects katakana. A romaji name will likely be
rejected by the validator; use ハビエル カミーノ.

## Terms, as the venue states them

- **Reservation deadline, and changes to headcount: 23:00 the day before**,
  so **Sat 19 Sept, 23:00 JST**. After that, door only at ¥6,050.
- Confirmation comes in **two stages**. The instant auto-reply from
  `no-reply@pit-inn.com` states plainly that it is *not* the confirmation
  (予約完了メールではございません). Staff review the form and send a separate
  **予約完了メール** within a few days. Only that second mail is the booking.
  If it does not arrive, write to `shinjuku@pit-inn.com`; the auto-reply
  address rejects replies.
- **整理番号 (entry-order number) is assigned when you reserve, not when you
  arrive.** Reserving earlier gets you in earlier. This is the only reason to
  do it today rather than next week.
- Entry is in 整理番号 order; reserved guests board before walk-ups.
- No cancellation fee is stated, and none can apply because nothing is paid.
- No operator-cancellation refund policy is published on the page.

## On the day, the part that is easy to get wrong

A reservation is not a ticket. You must **buy the reserved ticket at the Pit Inn
reception desk before doors**. The venue asks matinee reservation-holders to
come from **13:00**, buy the ticket, then return for the **14:00** opening, so
the desk is not swamped at 14:00.

So: at the venue about 13:00, ticket in hand, back at 14:00, in at your 整理番号.
Give the booking name at reception — the confirmation says the two tickets are
already set aside under it. If the mail's 13:30 doors turn out to be the real
ones, arriving at 13:00 still lands you inside the window.

Expect cash. The music book says cash at the door; the venue page does not say
either way, so carry enough, ¥11,000 for two.

## Check afterwards

- [x] Auto-reply received at javier032@gmail.com 2026-09-07 23:19 UTC, subject
      「新宿PITINN　ご予約受付メール」, naming 2026年9月20日（Sun）,
      Open14:00/Start14:30, 2名様. Not the confirmation.
- [x] **予約完了メール received 2026-09-11** (the real confirmation): 2 people,
      daytime show of 20 September, tickets already kept under the booking name,
      buy them at reception before opening, entry in ticket-number order. Its
      times, doors 13:30 / start 14:00, are the house defaults and not what the
      show page says.
- [ ] 整理番号 noted — the confirmation carries none, so ask at the desk
- [ ] ¥5,500 advance price honoured at the counter, not ¥6,050. The show page
      calls all three routes 前売 sales, so reserving now should lock the
      advance price, but it is ¥1,100 across two tickets if that reading is
      wrong. Check at the desk, do not argue on the day.
- [ ] Nothing was charged to any card

## Not this show

Pit Inn runs 昼の部 14:30 and 夜の部 19:30 daily, and Holoubek plays six of
them across Sun 20 to Tue 22. Only the **Sun 20 matinee** is 東京民謡倶楽部,
the min'yō band: three Tsugaru shamisen, singer, shakuhachi and wadaiko over
the jazz rhythm section with 石若駿 on drums. Every other slot in the residency
is a different trio. Book the 20th at 14:30 or you have booked the wrong thing.
