# How to add a new mechanism

Series format: a 33 s vertical (1080x1920) flat-matte 2D video. A countdown runs 0:30 → 0:00, with an object counter. Objects multiply when the video's mechanism acts on them (crush, slice, x2 gate…): one is removed and two new ones spawn. At 0:00 the tank explodes.

## Rules from the owner (do not break)
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
- Start very slow (1–3 balls at 5 s, ≤12 at 10 s). Growth then explodes, and the tank is full at 0:00 (≥500 balls).
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
