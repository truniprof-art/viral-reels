"""Story image with the CURRENT World Ball League table (from league.json). Posted as an Instagram story after every race.
Usage: python3 league_story.py league.json OUT.jpg [NEXT_TEXT]"""
import sys, json, cairo, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from country_race import ball_sprite, text, BG, GOLD, W, H
from PIL import Image

lg = json.load(open(sys.argv[1])); out = sys.argv[2]
nxt = sys.argv[3] if len(sys.argv) > 3 else f"RACE #{len(lg['races']) + 1} NEXT"
last = lg["races"][-1]; n = last["race"]
gain = {c: lg["points"][i] for i, c in enumerate(last["standings"][:len(lg["points"])])}
rows = sorted(lg["table"].items(), key=lambda kv: (-kv[1], -gain.get(kv[0], 0)))
s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(s)
c.set_source_rgb(*BG); c.paint()
text(c, "WORLD BALL LEAGUE", 540, 250, 76, (*GOLD, 1), True, 4)
text(c, "SEASON 1 · FINAL TABLE" if lg.get("champion") else f"TABLE AFTER RACE #{n}", 540, 330, 44, (1, 1, 1, .85), True, 6)
w = last["standings"][0]; sp = ball_sprite(w, 46); c.set_source_surface(sp, 300 - sp.get_width() / 2, 380); c.paint()
text(c, f"RACE #{n} WINNER: {w}", 380, 440, 44, (1, 1, 1, 1), True, 2, "l")
y = 540
for j, (code, pts) in enumerate(rows[:10]):
    c.set_source_rgba(1, 1, 1, .16 if j == 0 else .08); c.rectangle(110, y, 860, 96); c.fill()
    text(c, f"{j + 1}", 170, y + 64, 46, (1, 1, 1, .6), True)
    sp = ball_sprite(code, 32); c.set_source_surface(sp, 225, y + 8); c.paint()
    text(c, code, 320, y + 66, 54, ((*GOLD, 1) if j == 0 else (1, 1, 1, 1)), True, 3, "l")
    if gain.get(code): text(c, f"+{gain[code]}", 720, y + 64, 38, (.55, .9, .6, 1), True, 0, "r")
    text(c, f"{pts} PTS", 930, y + 66, 50, (1, 1, 1, 1), True, 1, "r")
    y += 108
c.set_source_rgba(*GOLD, 1); c.rectangle(80, y + 40, 920, 250); c.fill()
text(c, nxt, 540, y + 125, 56, (.08, .08, .1, 1), True, 3)
L2, L3 = (("a brand-new series starts tomorrow", "follow @crush.multiply") if lg.get("champion") else
          ("comment your country under the race reel", "requested countries join as wildcards"))
text(c, L2, 540, y + 190, 36, (.08, .08, .1, 1), False, 1)
text(c, L3, 540, y + 245, 36, (.08, .08, .1, 1), False, 1)
Image.frombuffer("RGBA", (W, H), bytes(s.get_data()), "raw", "BGRA", 0, 1).convert("RGB").save(out, quality=92)
print(out)
