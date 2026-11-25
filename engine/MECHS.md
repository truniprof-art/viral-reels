# How to add a new mechanism

Series format: a 33 s vertical (1080x1920) flat-matte 2D video. A countdown runs 0:30 → 0:00, with an object counter. Objects multiply when the video's mechanism acts on them (crush, slice, x2 gate…): one is removed and two new ones spawn. At 0:00 the tank explodes.

## Rules from the owner (do not break)
- MIXED SCHEDULE (Kolya approved 2026-11-25, from data): 09:47 + 12:47 = a BRAND-NEW mechanism (exploration, not in mechs.json); 19:47 + 21:47 + 23:47 = a NEW STRUCTURAL VARIATION of a mechanism that hit (wheel, press, gates, blender so far): a build never posted before (new tank shape, number/layout of parts, direction, levels), not a re-skin; 15:47 = format-breaking EXPERIMENT unlike our usual content. `make.py auto` only as fallback.
- VARIETY FIRST (owner, 2026-11-23): never post near-identical videos. Every video differs in mechanism and/or look:
  object shape (circle, triangle, square, ring, hex nut, star, pill), background, tank shape, palette.
  make.py picks a style (`STYLE` env, see style.py) that avoids the shapes of the last 4 posts and the backgrounds of the last 2.
  A hit format is a signal to make *new variations* of it, not to repost it.
- NO REPEATED MECHANISM BUILD (owner, 2026-11-24): a mechanism is never posted again in the same build. Every regular post is a
  *variation*: make.py picks a structural variant (VARIANTS in make.py: number of funnels/arms/paddles/gates, direction, size, press config)
  not used in this kind's recent posts (log: ../variants.log, written by make.py — commit it). If a kind hits, add NEW variants of it
  (test with `search`, need ≤3 at 5 s, ≤12 at 10 s, ≥500 final) instead of reposting. Kinds with a single variant (crusher) need new variants.
- ONE FULLY UNIQUE VIDEO PER DAY (owner, 2026-11-24: ABSOLUTELY new content, a psychology-driven experiment; see strategy.md 'Daily EXPERIMENT slot' and log it in ../experiments.md): the 15:47 (Kyiv) run builds something never posted before — new mechanism,
  new reason to multiply, new tank shape or level layout — not just a re-skin.
- Reasons to multiply may vary (crush, slice by a blade, pass through a x2 gate, split on a spike/prism, etc.), but each must be
  clear and visible, and there is ONE rule per video. Plain random touching never multiplies an object.
- One consistent rule per video. Rotation never reverses direction.
- Start slow by DEFAULT (1–3 balls at 5 s, ≤12 at 10 s). Since 2026-11-26 (Kolya: "you are in charge") this is the council's default, not an owner rule: a decision in decisions.md may change it (first test: 15:47 head start on 11-26). Growth then explodes, and the tank is full at 0:00 (≥500 balls).
- 2D only, flat matte style (no gloss), no slow-mo.
- Balls never escape the tank.
- The mechanism must not be so fast that balls can't get into it.
- Continuous, self-feeding mechanisms (rollers, belts) score best. Periodic strikers (guillotine, hammers, scissors, gears) were disliked.

## Engine
`base.py` holds the shared engine.

Subclass `Mech` with these hooks:
- `build(space)`
- `step(t, dt)`
- `crush(t, pos) -> bool mask`
- `spawn_dir`, or optionally `spawn_x` / `spawn_xy`
- `squash`, `state(t)`, `draw(ctx, t, st, a)`
- `sounds()`, optionally `hum()`
- `explode(space)`, `tank_walls`

Use `belts.py` as a template. The file must end with `main(YourClass, "name")`, which gives the commands `search seeds… | rec seed | snap times… | all`.

To make the start slow, use pressure accumulation (see `PTH` in belts.py) and delayed activation of extra crush zones.

## Steps to add one
1. Write `engine/<name>.py`.
2. Find parameters that give a good curve: `WORK=/tmp/x python3 -B <name>.py search 1 2 3 4 5 6`.
3. Check frames: `rec <seed>`, then `snap 3 12 22 29`, and look at the PNGs in `$WORK`.
4. Add an entry to `mechs.json`: `{"file", "name", "min_final", "env"}`.
5. Add it to `../rotation.json` with weight 1.
6. Run `python3 -B make.py <name> ../out/t.mp4` once, check it, then commit.

## Style layer
`style.py` reads `STYLE` (JSON `{"shape","bg"}`) and is used by every renderer: `ST_.put(ctx, col, glow, x, y, i, BR)` draws an object,
`ST_.BG` is the background, `ST_.LABEL` the counter word, `ST_.ink(a)` the text colour. New renderers must use it too.
Physics stays circular. Force a style with `SHAPE=tri BG=sand python3 -B make.py ...`. posts.csv has a `style` column (`shape:bg`).
A mech without the rectangular tank sets `tank_walls = False`, builds its own walls and may define `fix_xy(x, y)` to keep spawns inside.

## Mechanisms so far
- press (presssim2/pressrender3) — hydraulic press, crush.
- crusher (rollsim/rollrender) — roller pairs, crush.
- belts — V belts, crush.
- blender — round jar, 4-blade spinning knife SLICES objects (new cause).
- gates — bucket elevators lift objects, they fall through glowing x2 gates (new cause, 3 gates switch on at 0/12/20 s).
- wheel — big paddle wheel in a round trough scoops shapes up its rising side through a red x2 laser line (split on laser).
- bumpers — RACE: tank split by a wall into two team colours (orange vs blue); a rotor flings shapes at a round pinball bumper on each side; touching the bumper = x2 (new cause). Orange recharges faster early, blue faster late, so the lead flips in the last ~5 s; side counters + LEADS/WINS, 'PICK A SIDE' title. Per-side cap 380.
- gates_zig (gates_zig.py, variation of gates, 2026-11-25) — same bucket elevators, but three HALF-WIDTH x2 gates staggered left/right/left with a slanted ramp under the first two: shapes zigzag gate→ramp→gate (marble-run waterfall), up to 3 doublings per trip. Env CH0=1.2, GACT=0,11,17.
- wheel_twin (wheel_twin.py, variation of wheel, 2026-11-25) — TWO smaller paddle wheels (R 190, 5 paddles) side by side in a W-shaped double trough with a ridge in the middle, mirror rotation (left wheel lifts its left side, right wheel its right side; neither ever reverses). Each has its own red x2 laser on its outer rising side; the right laser switches on at 9 s (ACT2) for the slow start. Shapes are thrown back over the ridge into either wheel. Env W1=4.4.
- press funnel (VARIANT=funnel, 2026-11-25, variation of press) — the tank is a steep FUNNEL (SLOPE_Y 1050, top PBY0 980) with a narrower slab (PX 440..640) and smaller shapes (PBR 13): walls slide everything straight back onto the anvil; spawns sit just inside the slanted walls and anything outside the funnel is re-dropped (presssim2 FUNNEL / wall_x). Final ~260–300 (press norm ≥250), fills the funnel to the brim. Env via make.py PRESS_ENV.
- hourglass — the tank IS a giant hourglass turning slowly one way; every shape squeezing through the glowing NECK becomes THREE (first x3 rule; base.py `NSPLIT` on the mech). Small shapes (BR 9) like sand; it pours back through the neck every half-turn, so growth comes in waves. Own walls, BX0..FLOOR widened.

## On-screen text & ending (council 2026-11-24)
- OPENING BET (council 2026-11-25, D3): `style.opener` (called from `style.endcard` every frame) shows 0–2.6 s a banner '1 BALL. ONE RULE. / HOW MANY AT 0:00?' (start count = env N0, default 1; bumpers N0=2). End card adds 'from N0 in 30 seconds'. New renderers get it automatically by calling `ST_.endcard` every frame.
- MID FOLLOW CUE (D6, 2026-11-26): `style.midcue` 12.0–14.2 s yellow bar 'FOLLOW @CRUSH.MULTIPLY', automatic via `ST_.endcard`.
- SLOT CROSSOVER 11-26..11-28 (decisions.md D4): 12:47 = hit variation, 21:47 = brand-new mechanism.
- All on-screen text is ENGLISH (labels BALLS/RINGS/… in style.LABELS).
- No black fade: the last 1.5 s is `style.endcard()` — EPISODE N, FINAL COUNT (real, from `style.LAST`, set by the renderer's counter), "Did you guess it?", "NEW SIMULATION EVERY FEW HOURS · FOLLOW @CRUSH.MULTIPLY". New renderers must set `ST_.LAST[0]` where they draw the counter and call `ST_.endcard(ctx, t, T_END, text)` at the end of each frame.
- Episode N = env EP, else posts.csv rows + 1 (so it matches the caption "Episode N").
