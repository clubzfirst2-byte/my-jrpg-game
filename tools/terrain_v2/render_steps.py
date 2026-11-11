"""Reference renderer of ground v2 WITH heights (round 10): what gameView.buildChunk does with the v2 ground,
for the review images of the step art (NAMES.md 2b / 2c). Not the engine; the engine follows NAMES.md.

  1. the flat ground on the dual grid (render_ref.render_v2), tinted as level 0
  2. rows top to bottom; in a row, cells left to right, every raised cell (elev > 0, not a ramp):
       its surface (the ground's calm tile render_ref.calm_number) at (tx·32, ty·32 − 2·elev) art px, tinted
       by its level; its south face (v1 face keys, gameView.addFace); its step pieces right after it
  3. after each row, the step shadows on the lower east cells (2b)
Step pieces: mode "step2" (round 10, 2c), "step" (rounds 7-9, 2b), "line" (v1: 1-px lines).

Run: python3 tools/terrain_v2/render_steps.py   (writes docs/art-release-v2/terrain/review/steps_*.png)
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image  # noqa: E402

import render_ref as R  # noqa: E402
from keys_v2 import final_name  # noqa: E402
from steps import step2_corners  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "src", "art-release-v2", "terrain")
LEVEL_PX = 16  # game px (tilemap.LEVEL_PX)
G_GRASS, G_PATH, G_WATER, G_RUIN, G_SAND = 0, 1, 2, 3, 4
REGION_GRASS = {"island": "g", "plains": "p", "forest": "m", "mountains": "n", "lake": "l", "desert": "g"}
CH_CLASS = {v: k for k, v in R.CLASS.items()}


class Art(dict):
    def __missing__(self, k):
        name = k[3:] if k.startswith("v1:") else final_name(k) if k.startswith(("g2.", "autumn.g2.", "winter.g2.")) else k
        self[k] = Image.open(os.path.join(ART, name + ".png")).convert("RGBA")
        return self[k]


def load_world(path=None):
    """The world map from the game's own code (node): width, height, ground, elev (game px), shape, regions."""
    import tempfile

    path = path or os.path.join(tempfile.gettempdir(), "terrain_v2_world.json")
    if not os.path.exists(path):
        js = ("const W='" + os.path.join(ROOT, "src", "game", "world") + "/';"
              "const {WORLD}=await import(W+'world.js');const {parseMap}=await import(W+'tilemap.js');"
              "const m=parseMap(WORLD);const fs=await import('node:fs');"
              f"fs.writeFileSync('{path}',JSON.stringify({{width:m.width,height:m.height,ground:Array.from(m.ground),"
              "elev:Array.from(m.elev),shape:Array.from(m.shape),regions:WORLD.regions}));")
        subprocess.run(["node", "--input-type=module", "-e", js], check=True)
    with open(path) as f:
        return json.load(f)


def region_at(world, tx, ty):
    for r in world["regions"]:
        if r["tx"] <= tx < r["tx"] + r["tw"] and r["ty"] <= ty < r["ty"] + r["th"]:
            return r["id"]
    return None


def class_char(world, tx, ty):
    g = world["ground"][ty * world["width"] + tx]
    reg = region_at(world, tx, ty)
    if g == G_GRASS:
        return REGION_GRASS.get(reg, "g")
    return {G_PATH: "=", G_WATER: "~", G_RUIN: "u", G_SAND: "d" if reg == "desert" else "s"}.get(g, "x")


def _tint(im, k):
    if k >= 0.999:
        return im
    return Image.merge("RGBA", [b.point(lambda v: int(v * k)) if i < 3 else b for i, b in enumerate(im.split())])


def level_tint(elev):
    return min(1.0, 0.95 + 0.05 * elev / LEVEL_PX)


def vertex_state(vx, vy):
    """NAMES.md 2c: the state of the cell corner (vertex) (vx, vy)."""
    return (R.dhash(vx + 211, vy + 97) >> 3) & 1


def render(world, x0, y0, w, h, art, mode="step2"):
    """A window of w x h cells at (x0, y0) of the world, all heights (a 1-cell margin is read around it)."""
    W = world["width"]
    grid = ["".join(class_char(world, x, y) for x in range(x0 - 1, x0 + w + 1)) for y in range(y0 - 1, y0 + h + 1)]
    elev = lambda x, y: world["elev"][y * W + x] if 0 <= x < W and 0 <= y < world["height"] else 0  # noqa: E731
    shape = lambda x, y: world["shape"][y * W + x]  # noqa: E731
    south_h = lambda x, y: elev(x, y) - LEVEL_PX if shape(x, y) == 1 else elev(x, y)  # noqa: E731
    base = R.render_v2(grid, art)  # covers cells x0 - 0.5 ... ; its pixel (0, 0) is art px (x0 - 0.5) * 32
    im = Image.new("RGBA", ((w + 2) * 32, (h + 2) * 32), (0, 0, 0, 255))
    im.alpha_composite(_tint(base, level_tint(0)), (16, 16))
    R._PIC.clear()
    R._CALMN.clear()

    def cls_of(x, y):
        return R.CLASS.get(class_char(world, x, y))

    def put(key, x, y, k=1.0):
        im.alpha_composite(_tint(art[key], k), (int(x), int(y)))

    for ty in range(y0 - 1, y0 + h + 1):
        shades = []
        for tx in range(x0 - 1, x0 + w + 1):
            hh = elev(tx, ty)
            if hh == 0 and shape(tx, ty) != 1:
                continue
            px, top = (tx - x0 + 1) * 32, (ty - y0 + 1) * 32 - 2 * hh
            cls = cls_of(tx, ty)
            k = level_tint(0) if mode == "step2" else level_tint(hh)  # 2c: one tint for every level
            if cls in (None, "water"):
                continue
            put(f"g2.{cls}.{R.calm_number(tx, ty)}", px, top, k)
            # south face
            face_top = (ty + 1) * LEVEL_PX - south_h(tx, ty)
            face_bot = (ty + 1) * LEVEL_PX - elev(tx, ty + 1)
            rem, yy, first = face_bot - face_top, face_top, True
            mat = {"ruin": "ruin", "path": "path", "sand": "sand", "dsand": "desert"}.get(cls) or ("stone" if region_at(world, tx, ty) == "mountains" else "earth")
            while rem > 0:
                seg = 8 if rem >= 8 else 4
                last = rem - seg <= 0
                put(f"v1:face.{mat}.{'top' if first else 'mid'}{'-base' if last else ''}.{seg}", px, (yy - (y0 - 1) * LEVEL_PX) * 2)
                yy += seg
                rem -= seg
                first = False
            if shape(tx, ty) == 1:
                continue
            ln = south_h(tx, ty - 1) < hh
            le = elev(tx + 1, ty) < hh
            lw = elev(tx - 1, ty) < hh
            mask = (1 if ln else 0) + (2 if le else 0) + (4 if lw else 0)
            lower = lambda x, y: elev(x, y) < hh  # noqa: E731
            if mode == "line":
                pass  # (drawn after the row)
            elif mode == "step":
                if mask:
                    put(f"g2.{cls}.step{mask}.{R.dhash(tx + 5, ty + 9) % 2}", px, top, k)
                if not ln and not le and lower(tx + 1, ty - 1):
                    put(f"g2.{cls}.stepinner.ne", px, top, k)
                if not ln and not lw and lower(tx - 1, ty - 1):
                    put(f"g2.{cls}.stepinner.nw", px, top, k)
            else:
                if mask:
                    vx = {"NW": (tx, ty), "NE": (tx + 1, ty), "SE": (tx + 1, ty + 1), "SW": (tx, ty + 1)}
                    code = sum(vertex_state(*vx[c]) << i for i, c in enumerate(step2_corners(mask)))
                    put(f"g2.{cls}.steptwo{mask}.{code}", px, top, k)
                if not ln and not le and lower(tx + 1, ty - 1):
                    put(f"g2.{cls}.steptwoinnerne.{vertex_state(tx + 1, ty)}", px, top, k)
                if not ln and not lw and lower(tx - 1, ty - 1):
                    put(f"g2.{cls}.steptwoinnernw.{vertex_state(tx, ty)}", px, top, k)
            if le:
                eh = elev(tx + 1, ty)
                ecls = cls_of(tx + 1, ty)
                ey = (ty - y0 + 1) * 32 - 2 * eh
                if mode == "line" or ecls in (None, "water"):
                    shades.append(("strip", px + 32, ey))
                elif mode == "step2":
                    pass  # 2c: the shadow is in the rim piece (no step.shade on the east cell)
                else:
                    shades.append((f"g2.{ecls}.stepshade.{R.dhash(tx + 6, ty + 9) % 2}", px + 32, ey, level_tint(eh)))  # (2b)
            if mode == "line":
                for (on, box) in ((le, (px + 30, top, 2, 32)), (lw, (px, top, 2, 32)), (ln, (px, top, 32, 2))):
                    if on:
                        _dark(im, box, 0.55)
        for s in shades:
            if s[0] == "strip":
                _dark(im, (s[1], s[2], 6, 32), 0.3)
            else:
                put(s[0], s[1], s[2], s[3])
    return im.crop((32, 32, (w + 1) * 32, (h + 1) * 32))


def _dark(im, box, a):
    x, y, w, h = box
    patch = im.crop((x, y, x + w, y + h))
    dark = Image.new("RGBA", patch.size, (16, 20, 28, int(255 * a)))
    patch.alpha_composite(dark)
    im.paste(patch, (x, y))


SCENES = {  # the wiring inspection's scenes (tools/shoot.cjs): the hero's tile; a 34 x 16 window around it
    "mtn_cliffs": (177, 26),
    "desert_cliff": (74, 184),
    "ruin_steps": (48, 22),
}


def scene_window(world, name, w=32, h=15):
    """The screen around a scene's hero (world tiles): 32 x 15 cells (iPhone 15 Pro landscape), centred on where
    the hero is drawn (raised by its height)."""
    tx, ty = SCENES[name]
    lift = round(world["elev"][ty * world["width"] + tx] / LEVEL_PX)
    return tx - w // 2, ty - lift - h // 2, w, h


if __name__ == "__main__":
    world = load_world()
    art = Art()
    out = os.path.join(ROOT, "docs", "art-release-v2", "terrain", "review")
    for name in SCENES:
        x0, y0, w, h = scene_window(world, name)
        for mode in ("line", "step", "step2"):
            render(world, x0, y0, w, h, art, mode).save(os.path.join(out, f"steps_{name}_{mode}.png"))
    print("wrote", out)
