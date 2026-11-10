"""A review sheet of the v2 UI art -> docs/art-release-v2/ui/review_sheet.png.

Run: python3 tools/ui_v2/review.py   (after gen_ui.py). The title at x2, everything else at x2-x3;
9-slices are shown stretched to sample sizes, the way the engineer will use them.
"""
import os
import sys

from PIL import Image

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
out = os.path.join(root, "docs", "art-release-v2", "ui", "review_sheet.png")
sys.path.insert(0, os.path.join(root, "tools", "ui_v2"))
from common import nine_slice  # noqa: E402
import json  # noqa: E402

D = os.path.join(root, "src", "art-release-v2", "ui")
M = json.load(open(os.path.join(D, "manifest.json")))["sprites"]


def L(n):
    return Image.open(os.path.join(D, n + ".png")).convert("RGBA")


S = Image.new("RGBA", (1600, 1500), (40, 70, 50, 255))
y = 10
bg = L("title.bg").resize((960, 400), Image.NEAREST)
S.paste(bg, (10, y))
logo = L("title.logo")
lg = logo.resize((logo.width * 2, logo.height * 2), Image.NEAREST)
S.alpha_composite(lg, (10 + 480 - lg.width // 2, y + 60))
big = logo.resize((logo.width * 3, logo.height * 3), Image.NEAREST)
S.alpha_composite(big, (990, y))
y += 420
x = 10
for n in ["btn.ring.gold.78.idle", "btn.ring.gold.78.pressed", "btn.ring.std.60.idle", "btn.ring.std.52.idle", "btn.ring.teal.52.idle", "btn.ring.std.44.idle"]:
    im = L(n).resize((L(n).width * 2, L(n).height * 2), Image.NEAREST)
    S.alpha_composite(im, (x, y))
    x += im.width + 10
y += 170
x = 10
for ic in ["attack", "jump", "dodge", "bow", "guard", "dash", "ability", "swap", "pause", "bag", "close"]:
    for s in (20, 26, 34):
        im = L(f"icon.ui.{ic}.{s}")
        im = im.resize((s * 3, s * 3), Image.NEAREST)
        S.alpha_composite(im, (x, y))
        x += im.width + 4
    if x > 1300:
        x = 10
        y += 110
y += 110
x = 10
for n, (w, h) in [("panel.menu", (200, 120)), ("panel.dialogue", (240, 80)), ("panel.shop", (200, 120)), ("panel.ending", (200, 120)), ("panel.toast", (140, 30))]:
    sl = M[n]["slice"]
    im = nine_slice(L(n), w, h, sl, 2)
    S.alpha_composite(im, (x, y))
    x += im.width + 10
    if x > 1200:
        x = 10
        y += 260
y += 260
x = 10
for n in ["tab.idle", "tab.active", "tab.pressed", "row.idle", "row.selected", "row.pressed", "btn.text.idle", "btn.text.pressed", "btn.text.selected", "btn.text.disabled"]:
    im = nine_slice(L(n), 60, 30, M[n]["slice"], 2)
    S.alpha_composite(im, (x, y))
    x += im.width + 8
y += 80
x = 10
for n in ["heart.0", "heart.1", "heart.2", "heart.3", "heart.4", "cue.more.0", "cue.more.1", "panel.crest", "panel.nameplate"]:
    im = L(n)
    im = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
    S.alpha_composite(im, (x, y))
    x += im.width + 10
im = nine_slice(L("bossbar.frame"), 180, 12, M["bossbar.frame"]["slice"], 3)
S.alpha_composite(im, (x, y))
S.save(out)
