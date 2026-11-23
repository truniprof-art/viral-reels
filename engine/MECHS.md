# How to add a new mechanism

Series format: a 33 s vertical (1080x1920) flat-matte 2D video. A countdown runs 0:30 → 0:00, with a ball counter. Balls multiply ONLY when a mechanism crushes them: one ball is removed and two new balls spawn above it. At 0:00 the tank explodes.

## Rules from the owner (do not break)
- Balls multiply only by a clear, visible crush. Touching never multiplies a ball.
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
