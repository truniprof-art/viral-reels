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
- wheel_dual (wheel_dual.py, variation of wheel, 2026-11-26) — ONE paddle wheel with TWO x2 lasers: red across the rising (left) side as before plus a CYAN laser across the DESCENDING (right) side at LY2 1150 (switches on at ACT2=12 s, recharge ×K2=2), so a shape can double twice per lap. Spawns under the cyan laser go below it. Env ACT2=12 K2=2 CH1=0.03; fills ~29 s.
- gates_spin (gates_spin.py, variation of gates, 2026-11-26) — same bucket elevators, but the fixed gates are replaced by ONE spinning x2 LASER ROTOR (half length RL 300, hub at y 1040) turning one way, speeding up 0.55→1.25 rad/s; one bar live from 0 s, the perpendicular bar lights at ACT2=12 s -> spinning x2 CROSS. Anything the glowing bar sweeps through or falls through splits. Env CH1=0.02 ACT2=12; fills ~28–29 s.
- geyser (geyser.py, NEW mechanism 2026-11-26 09:47) — V-funnel floor rolls everything into a NOZZLE; an air geyser column (cyan, widens JW0 30→JW1 80 px, launch speed 1600→1700) blasts shapes straight up through a floating glowing ×2 HOOP (half width HW 140 at HY 820, hung on wires). Every shape that flies through the hoop becomes two; early shots spray wide (SP0 0.25 rad) and often miss, later the jet tightens (SP1 0.12) → fountain of shapes. Continuous, self-feeding. ~3 at 5 s, ~600 final, fills ~29.5 s.
- blender_twin (blender_twin.py, 2026-11-26 12:47 hit variation, D4 slot) — ONE round jar, TWO counter-rotating 3-arm blades low left/right (both sweep up through the middle) + a centre divider that slides shapes into the blade pockets; right blade starts at ACT2=8 s. env PTH 1.6 / PTH1 0.6 / W0 0.7 / MAXN 650; curve ~1/6/29/100/268/505/650.
- wheel_rush (wheel_rush.py, 15:47 EXPERIMENT 2026-11-26, HEAD START test) — paddle wheel with 7 paddles, smaller shapes (BR 12), opens with N0=48 shapes already pouring into the trough (no empty start), red x2 laser on the rising side; counter honestly starts at 48; MAXN 1000, cap reached ~29.8 s. env N0 48 / CH0 0.4 / CH1 0.04 / W0 1.0 / WE 0.8. mechs.json supports per-mech max5/max10 for head-start kinds. Rotation weight 0 until the head-start verdict (11-28).
- portal (portal.py, NEW mechanism 2026-11-27 09:47, Ep 28, D9 arm B) — V funnel floor rolls shapes into a green IN portal at the bottom; every shape swallowed comes out of the violet OUT portal at the top (y 650) as TWO and falls back through a staggered plinko pegboard (rows 800–1280). IN portal recharge CH0 1.1 → CH1 0.012 s (slow start), takes more per charge later. Curve ~2/8–10/27–32/100–120/290–340/520–570/760 cap ~29 s. Late: the OUT portal crowds at the top. Small known artifact: a thin line from a crush flash can stroke between portals (harmless).

## On-screen text & ending (council 2026-11-24)
- OPENING BET (council 2026-11-25, D3): `style.opener` (called from `style.endcard` every frame) shows 0–2.6 s a banner '1 BALL. ONE RULE. / HOW MANY AT 0:00?' (start count = env N0, default 1; bumpers N0=2). End card adds 'from N0 in 30 seconds'. New renderers get it automatically by calling `ST_.endcard` every frame.
- MID FOLLOW CUE (D6, 2026-11-26): `style.midcue` 12.0–14.2 s yellow bar 'FOLLOW @CRUSH.MULTIPLY', automatic via `ST_.endcard`.
- SLOT CROSSOVER 11-26..11-28 (decisions.md D4): 12:47 = hit variation, 21:47 = brand-new mechanism.
- All on-screen text is ENGLISH (labels BALLS/RINGS/… in style.LABELS).
- No black fade: the last 1.5 s is `style.endcard()` — EPISODE N, FINAL COUNT (real, from `style.LAST`, set by the renderer's counter), "Did you guess it?", "NEW SIMULATION EVERY FEW HOURS · FOLLOW @CRUSH.MULTIPLY". New renderers must set `ST_.LAST[0]` where they draw the counter and call `ST_.endcard(ctx, t, T_END, text)` at the end of each frame.
- Episode N = env EP, else posts.csv rows + 1 (so it matches the caption "Episode N").
- **press_twin** (2026-11-26 19:47, Ep 23, hit variation of press): `press_twin_sim.py` + `press_twin_render.py`, own branch in make.py (not in mechs.json, like press). Two slabs (spans 240–460 and 620–840) over a W floor: steep side chutes, anvil A, centre ridge (RIDGE_Y 1470), anvil B. Press B wakes at ACT2=9 s and slams half a beat after A (alternating pistons). UP_GAP 190 (120 wedges shapes between head and slope), LV=0.55 launch scale (1.0 throws spawns away → final ~150), cfg 2.2,1.7,0.7 → 3 @5 s, ~7 @10 s, hits MAXN 900 ~28 s. Known look: side chutes stack up to the lid from ~20 s (balls queue for the slabs).
- **wheel pad3** (2026-11-26 23:47, Ep 25, hit variation of wheel; VARIANTS wheel "pad3" = NP 3, LY 1120): only THREE long paddles and the red x2 laser 40 px lower on the rising side, so each long arm sweeps a big load through the laser per lap; ~2 @5 s, ~9 @10 s, 720 cap ~29.9 s.
- **wheel pad5** (2026-11-27 12:47, Ep 29, hit variation of wheel, D9 arm A; VARIANTS wheel "pad5" = NP 5): five paddles — one step from the pad4 breakout; hex nuts on slate; 2 @5 s, 2 @10 s, 49 @20 s, 403 @~27 s, 720 cap at the end.
- D9 BANNER A/B (2026-11-26 night): `NOBANNER=1` env switches off `style.opener` (D3 bet banner); everything else unchanged. Arm map per slot in decisions.md D9 (11-27..11-28); log arm in posts.csv style as `shape:bg|A` / `|B`.
- D8 WORLD BALL LEAGUE: concepts/country_race.py + concepts/league.json (points 10-8-6-5-4-3-2-1 from real standings; `standings(frames[-1], fin, 99)[0]` gives the full order). Next race must: open already moving, add wildcards from comments, end on top-5 standings + next race time, and append the result to league.json.
- **gates wide** (2026-11-27 01:47, Ep 26, hit variation of gates, D9 arm B = NOBANNER; VARIANTS gates "wide" = COLW 130): same 3-gate base build as the 24.6k g3 breakout, but elevator shafts 130 px instead of 96 → buckets lift bigger loads, narrower gate span; curve 3/4/11/25/100/557/760, fills ~27 s. slate bg. Note: make.py fails at os.replace if the output dir doesn't exist — create it first.
- **press wide** (2026-11-27 03:47, Ep 27, hit variation of press, D9 arm A = banner; VARIANTS press "wide" cfg 2.2,1.5,0.7 + PRESS_ENV PX0 300 / PX1 780 / SLOPE_Y 1500): slab ~480 px wide (base 300) over a SHALLOW V floor — each slam catches a whole row; curve 2/7–10/~30/~110/~250/~320/430–480, final ~445 packs the tank to the lid at 0:00. Faster slam cfgs (0.5–0.55 end interval) gave LOWER finals here. Also fixed make.py: the bg/shape no-repeat filter now strips the D9 '|A'/'|B' suffix (Ep26 slate was repeating).
- 2026-11-27 19:50 gates **g2** (Ep31, hit variation, D9 arm B no banner): only TWO ×2 gates (GY=960,1260, GACT=0,8) with fast recharge CH0=0.8 so the tank still fills (seed 69659: 2/7/21/55/104/183/758). One-parameter-away build from the gates base family on a dark bg (D9).
- **press chunky** (2026-11-27 23:47, Ep 33, hit variation of press, D9 arm A; VARIANTS press "chunky" cfg 2.2,1.5,0.7 + PRESS_ENV PBR 19, MAXN 600): the base press with much bigger cubes. Curve 1 → 4 @6 s → 27 @13 s → 67 @20 s → 122 @25 s → 183 final; fewer pieces but the glass is packed to the brim at 0:00 (the tank is not full before ~29 s). Tried first: "tall" (PBY0 700, PBR 17) — the taller glass ended half empty at 256 → rejected.
- **D15 Part 1 / Part 2** (2026-11-27 council): `concepts/part2.py <reel.mp4> <split_s> <outdir> <LABEL>` cuts ONE rendered reel into part2.mp4 (the real ending from split−2 s, 'PART 2 · THE ENDING' tag for 3 s) and part1.mp4 (0..split + 3 s held frame under 'HOW MANY AT 0:00? / THE ENDING IS PART 2 / already on our page'). Post part2 FIRST, part1 second.
