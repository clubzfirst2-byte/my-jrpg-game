"""The v3 village houses' night-window table for the game: src/view/assets/houseWindowsV3.json.

Read off docs/art-release-v3/village_windows.json (the windows' rectangles, by the art side) and the
house pictures in src/art-release-v3/objects/ (which texels are glass, by the rule of gfx/fx-v2's
houseWindows.glassKind: blue 20+ over red, blue >= green, brightness < 110; < 40 = the darkest glass).
Per house key and season file: its size (game px), and per window its rectangle (game px from the
feet) and the glass mask, one string per texel row, run-length coded ("14g2.14g": 14 glass, 2 not,
14 glass; d = the darkest glass). The game draws the lit glass from it (no read-back from the GPU);
tests/unit/houseWindowsV3.test.js checks it still matches the pictures.
  python3 tools/house_windows_v3.py
"""
import json
import os
import re

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def glass_kind(r, g, b, a):
    if a < 128 or b < r + 20 or b < g:
        return 0
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return 2 if lum < 40 else (1 if lum < 110 else 0)


def rle(row):
    return "".join(f"{len(m.group(0))}{m.group(1)}" for m in re.finditer(r"(.)\1*", row))


def main():
    src = json.load(open(os.path.join(ROOT, "docs", "art-release-v3", "village_windows.json")))["houses"]
    out = {}
    for key, v in sorted(src.items()):
        im = Image.open(os.path.join(ROOT, "src", "art-release-v3", "objects", f"{key}.png")).convert("RGBA")
        px = im.load()
        wins = []
        for w in v["windows"]:
            x0, y0, ww, hh = w["art"]
            rows = ["".join(".gd"[glass_kind(*px[x, y])] for x in range(x0, x0 + ww)) for y in range(y0, y0 + hh)]
            assert sum(r.count("g") + r.count("d") for r in rows) == w["lit"], key
            wins.append({"game": w["game"], "glass": [rle(r) for r in rows]})
        out[key] = {"size": v["game_size"], "windows": wins}
    path = os.path.join(ROOT, "src", "view", "assets", "houseWindowsV3.json")
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(path, os.path.getsize(path))


if __name__ == "__main__":
    main()
