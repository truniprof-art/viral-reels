import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""HEAD START experiment (2026-11-26 15:47): the paddle wheel opens with N0 shapes already pouring into the trough, so the
machine is busy from frame one; 7 paddles, smaller shapes (BR 12), red x2 laser on the rising side as in wheel.py.
Counter starts honestly at N0 and the tank is full (~1000) at 0:00."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("NP", "7")
import base
base.BR = float(os.environ.get("BRR", "12"))
import wheel
from wheel import *
base.MAXN = int(os.environ.get("MAXN", "1000"))
N0 = int(os.environ.get("N0", "48"))

class WheelRush(wheel.Wheel):
    name = "wheel_rush"

def starts():
    r = random.Random(7); out = []
    for k in range(N0):
        row, col = divmod(k, 12)
        out.append(((200 + col * 62 + r.uniform(-6, 6), 640 + row * 34), (r.uniform(-40, 40), 0)))
    return out

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=starts())
    main(WheelRush, "wheel_rush")
