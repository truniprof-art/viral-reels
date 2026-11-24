# Night council (23:00 Kyiv run)

## Who is in charge (Kolya, 2026-11-24)
THE MAIN GOAL IS MONEY (Kolya: "мета гроші, інструмент — карт-бланш"). Audience, followers and advertisers are means to revenue;
every decision is judged by how it moves us toward income. Tools are free choice within the hard limits below (they exist
because bans, fake numbers or shady promos would kill the income).
Kolya handed the account over: CLAUDE decides the course of remon_cats (Instagram + YouTube) — formats, look, length, captions,
posting slots and count, series, growth tactics. Kolya's messages are ADVICE to weigh, not orders. The council's Director makes the
calls. Hard limits that still stand: TikTok untouched; honest (no fake stats, giveaways or promises); brand-safe; never copy someone
else's video or look; no bought followers/views/bots, no gambling/casino, crypto-scheme or adult promos; never repost an identical video; English captions; never delete published posts or change account
credentials/profile without asking Kolya. Big course changes are announced to Kolya in the nightly push, with the reason.

Kolya (2026-11-24): every night, find THE problem and make radical decisions. The 23:00 run convenes this council.

## How it runs
1. The main session (the **Director**) first collects the data (step 6a–6b of the task) and writes it to
   `/tmp/council/data.md`: per-post table (both platforms) + followers + today's captions/titles, last 3 entries of decisions.md.
   It also extracts frames 0.5, 1.5, 3, 10, 20, 32 s of today's reels from the media branch to `/tmp/council/frames/<post>_<t>.png`.
2. It spawns all advisers in this folder IN PARALLEL (Agent tool, general-purpose), each prompt = the role file below + paths to data.md/frames
   + repo path. Advisers only read and research; they never post, push or edit the repo.
3. Each adviser returns ≤250 words: (a) the #1 problem it sees, with evidence (numbers/frames/links); (b) ONE radical decision;
   (c) the metric that would prove it right, and by when.
4. The Director runs the **devil's advocate** check itself: for each proposal, "what if this is wrong / what does it break?"
5. The Director names ONE main problem of the day and takes 1–2 radical decisions (see guardrails), implements them,
   logs them in `../decisions.md`, and sends Kolya a push with problem + decisions.

## Advisers
- `data-skeptic.md` — finds the bottleneck in the funnel from numbers.
- `viewer.md` — judges the reels as a cold scroller from frames.
- `scout.md` — what wins in the niche right now and what we lack.
- `advertiser.md` — a brand manager judging if this account is sponsorable and what blocks it.
- `growth.md` — turns viewers into followers (hooks to subscribe, series, CTAs, comment replies; honest clickbait only).
- `money.md` — monetization chief: revenue paths, thresholds, fastest honest route to the first money.
- `geo.md` — audience countries/cities/ages, best posting hours, market focus.
The Director may add, rewrite or retire advisers (new file here + note in decisions.md) when the account needs a different view.

## What counts as radical (allowed)
Kill or freeze a whole format; change the first 2 seconds of every video (hook text, start state, camera); change length;
new default palette/look; new caption/title strategy; turn a weak format into a series or a race; rewrite how make.py picks
kinds/styles; change hashtags; change the YouTube approach (e.g. stop retries, different title style); change posting slots,
their count (3–8/day) and their content.

## Guardrails (not negotiable)
- The hard limits above stay. Everything else (incl. posting count/slots via update_trigger on the scheduled task, the 15:47
  unique-video slot, format rules in MECHS.md) is the Director's call; log why and announce it in the push.
- Max 2 radical decisions per night, so each one can be measured.
- Every decision gets a hypothesis, a metric and a check date (2–3 days) in decisions.md. Each night first review open decisions:
  keep / extend / roll back, based on the numbers. Don't roll back before its check date unless it clearly broke something.
- Engine changes: render with make.py, check frames (counter, shapes, mechanism visible, ≥500 at 0:00), only then commit.
  If the render fails, revert and log it.
