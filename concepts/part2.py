"""D15 (council 2026-11-27): honest PART 1 / PART 2 split of one rendered satisfying reel.

usage: python3 part2.py <reel.mp4> <split_s> <outdir> <label e.g. CUBES>
  part2.mp4 = the real ending (from split-2 s to the end incl. the end card) with a 'PART 2 · THE ENDING' tag  -> post FIRST
  part1.mp4 = 0..split, then the last frame held 3 s under a card 'THE ENDING IS PART 2 — ALREADY ON OUR PAGE' -> post SECOND
Part 2 is published before Part 1, so the promise on Part 1 is true the moment anyone sees it.
"""
import sys, os, subprocess, cairo

src, S, out, label = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
W, H = 1080, 1920
YEL = (1, .72, .25)

def txt(ctx, s, x, y, size, rgba, bold=True):
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size); e = ctx.text_extents(s)
    ctx.move_to(x - e.width / 2 - e.x_bearing, y); ctx.set_source_rgba(*rgba); ctx.show_text(s)

def card(path):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.set_source_rgba(.07, .07, .09, .80); c.paint()
    txt(c, "HOW MANY AT 0:00?", 540, 760, 74, (1, 1, 1, 1))
    txt(c, "THE ENDING IS", 540, 920, 60, (1, 1, 1, .85), False)
    c.set_source_rgba(*YEL, 1); c.rectangle(140, 960, 800, 150); c.fill()
    txt(c, "PART 2", 540, 1065, 100, (.08, .08, .1, 1))
    txt(c, "already on our page", 540, 1200, 52, (1, 1, 1, .95), False)
    txt(c, "→ @CRUSH.MULTIPLY", 540, 1290, 58, (*YEL, 1))
    s.write_to_png(path)

def tag(path):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.set_source_rgba(*YEL, .95); c.rectangle(240, 300, 600, 110); c.fill()
    txt(c, "PART 2 · THE ENDING", 540, 375, 52, (.08, .08, .1, 1))
    s.write_to_png(path)

card(f"{out}/card.png"); tag(f"{out}/tag.png")
ff = ["ffmpeg", "-loglevel", "error", "-y"]
# Part 1: 0..S, hold last frame 3 s, card fades in over the hold
subprocess.run(ff + ["-i", src, "-loop", "1", "-i", f"{out}/card.png", "-filter_complex",
    f"[0:v]trim=0:{S},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=3[v];"
    f"[1:v]format=rgba,fade=in:st={S}:d=0.3:alpha=1[c];[v][c]overlay=0:0:shortest=1:enable='gte(t,{S})'[vo];"
    f"[0:a]atrim=0:{S},asetpts=PTS-STARTPTS,afade=out:st={S-0.4}:d=0.4,apad=pad_dur=3[ao]",
    "-map", "[vo]", "-map", "[ao]", "-t", str(S + 3), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{out}/part1.mp4"], check=True)
# Part 2: from S-2 to the end, tag for the first 3 s
P = S - 2
subprocess.run(ff + ["-ss", str(P), "-i", src, "-loop", "1", "-i", f"{out}/tag.png", "-filter_complex",
    "[1:v]format=rgba[t];[0:v][t]overlay=0:0:shortest=1:enable='lt(t,3)'[vo];[0:a]afade=in:d=0.3[ao]",
    "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{out}/part2.mp4"], check=True)
print("ok", out)
