import os, colorsys
H = float(os.environ.get("HUE", "0")) / 360.0
def rot(c):
    h, l, s = colorsys.rgb_to_hls(*c)
    return colorsys.hls_to_rgb((h + H) % 1.0, l, s)
