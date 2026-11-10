"""Ground v2 (gfx W1): writes every sprite to src/art-release-v2/terrain/<key>.png, the ramps used to
docs/art-release-v2/terrain/ramps.json (read by the test), NAMES.md (the key scheme for the engine),
check.txt (measured values) and the review images (review_v2.py).

Run: python3 tools/terrain_v2/gen_v2.py   (needs Pillow)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import grounds as G  # noqa: E402
import transitions as T  # noqa: E402
import water as WA  # noqa: E402
from ramps_v2 import EXT, BASE5, NEW_RAMPS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "src", "art-release-v2", "terrain")
DOCS = os.path.join(ROOT, "docs", "art-release-v2", "terrain")

VARIANTS = [0, 1, 2, 3]
MACRO = ["m0", "m1", "m2", "m3"]  # TL, TR, BL, BR of a 2x2 block
MASKS = range(1, 15)
SEASON_MAT = {"autumn": G.AUTUMN_RAMP}


def ground_tiles(ground, season=None):
    """{suffix: canvas} for the 4 singles and the 4 macro pieces."""
    out = {}
    build = (lambda v: G.seasonal(ground, v, season)) if season else (lambda v: G.GROUNDS[ground](v))
    for v in VARIANTS:
        out[str(v)] = build(v)
    for k, piece in enumerate(G.cut_macro(build("m"))):
        out[MACRO[k]] = piece
    return out


def overlay_tiles(ground, tex, season=None):
    if season == "winter":
        mat, style = "snow", "snow"
    elif season == "autumn":
        mat, style = G.AUTUMN_RAMP[ground], T.STYLE[ground]
    else:
        mat, style = ground, T.STYLE[ground]
    return {f"e{m}.{v}": T.overlay(tex, mat, m, v, style) for m in MASKS for v in (0, 1)}


def build():
    """key -> canvas"""
    out = {}
    for g in G.GROUNDS:
        tiles = ground_tiles(g)
        out.update({f"g2.{g}.{k}": c for k, c in tiles.items()})
        out.update({f"g2.{g}.{k}": c for k, c in overlay_tiles(g, tiles["0"]).items()})
    for season in ("autumn", "winter"):
        for g in G.SEASONAL:
            tiles = ground_tiles(g, season)
            out.update({f"{season}.g2.{g}.{k}": c for k, c in tiles.items()})
            out.update({f"{season}.g2.{g}.{k}": c for k, c in overlay_tiles(g, tiles["0"], season).items()})
    for depth in ("shallow", "deep"):
        for v in (0, 1):
            for f in range(WA.FRAMES):
                out[f"g2.water.{depth}.{v}.{f}"] = WA.water_tile(depth, f, v)
    for m in MASKS:
        for f in range(WA.FRAMES):
            out[f"g2.water.deep.e{m}.{f}"] = WA.deep_overlay(m, f)
            out[f"g2.water.foam.e{m}.{f}"] = WA.foam_overlay(m, f)
    return out


def check_seams(cv):
    """Every single variant and every macro piece of a ground must have the same 2-px edge band on the
    edges it shares with any other tile (the seam layer): that is what makes them join in any order."""
    errors = []
    bands = {"top": lambda c: [c.px[y][x] for y in (0, 1) for x in range(32)],
             "bottom": lambda c: [c.px[y][x] for y in (30, 31) for x in range(32)],
             "left": lambda c: [c.px[y][x] for y in range(32) for x in (0, 1)],
             "right": lambda c: [c.px[y][x] for y in range(32) for x in (30, 31)]}
    outer = {"m0": ("top", "left"), "m1": ("top", "right"), "m2": ("bottom", "left"), "m3": ("bottom", "right")}
    prefixes = sorted({k.rsplit(".", 1)[0] for k in cv if k.rsplit(".", 1)[1] == "0" and ".e" not in k and "water" not in k})
    for p in prefixes:
        ref = cv[f"{p}.0"]
        for s in [str(v) for v in VARIANTS[1:]] + MACRO:
            c = cv[f"{p}.{s}"]
            for side in outer.get(s, bands.keys()):
                if bands[side](c) != bands[side](ref):
                    errors.append(f"{p}.{s} {side}")
    return errors


def lum(rgb):
    r, g, b = rgb[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b) / 2.55


def stats(im):
    px = [p for p in im.get_flattened_data() if p[3] == 255]
    ls = [lum(p) for p in px]
    m = sum(ls) / len(ls)
    sd = (sum((v - m) ** 2 for v in ls) / len(ls)) ** 0.5
    return len({p[:3] for p in px}), sd


def write_names(files, redrawn, new, copied, path):
    from names_v2 import names_md
    with open(path, "w", encoding="utf-8") as f:
        f.write(names_md(files, redrawn, new, copied))


V1 = os.path.join(ROOT, "src", "art-release", "terrain")


def main():
    import shutil

    from keys_v2 import final_name

    cv = build()
    errs = check_seams(cv)
    if errs:
        raise SystemExit("seam layer differs: " + ", ".join(errs[:20]))
    images = {k: c.image() for k, c in cv.items()}  # internal names (render_ref / review use these)
    files = {final_name(k): im for k, im in images.items()}
    assert len(files) == len(images), "two internal names map to one file"
    v1_keys = sorted(f[:-4] for f in os.listdir(V1) if f.endswith(".png"))
    copied = [k for k in v1_keys if k not in files]  # not redrawn this round: the v1 file, unchanged
    redrawn = [k for k in v1_keys if k in files]
    new = sorted(k for k in files if k not in set(v1_keys))
    os.makedirs(OUT, exist_ok=True)
    keep = set(files) | set(copied)
    for f in os.listdir(OUT):
        if f.endswith(".png") and f[:-4] not in keep:
            os.remove(os.path.join(OUT, f))
    for k, im in files.items():
        im.save(os.path.join(OUT, f"{k}.png"), optimize=True)
    for k in copied:
        shutil.copyfile(os.path.join(V1, f"{k}.png"), os.path.join(OUT, f"{k}.png"))
    os.makedirs(DOCS, exist_ok=True)
    used = sorted({v[0] for c in cv.values() for row in c.px for v in row if v})
    with open(os.path.join(DOCS, "ramps.json"), "w", encoding="utf-8") as f:
        json.dump({"ramps": {m: EXT[m] for m in used}, "base5": {m: BASE5[m] for m in used}, "new": sorted(NEW_RAMPS & set(used))},
                  f, indent=1)
    with open(os.path.join(DOCS, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"redrawn": redrawn, "new": new, "copied_from_v1": copied}, f, indent=1)
    lines = ["# ground v2: measured (gen_v2.py writes this)", "",
             f"files: {len(keep)} = {len(redrawn)} v1 keys redrawn + {len(new)} new keys + {len(copied)} v1 keys copied unchanged",
             "seam check: OK", "", "ground tiles: colours per tile / lightness spread (std, 0-100)"]
    for k, im in images.items():
        if k.split(".")[-1] in ("0", "m0") and ".e" not in k and "water" not in k:
            n, sd = stats(im)
            lines.append(f"  {final_name(k):<30} colours {n:2d}  spread {sd:4.1f}")
    with open(os.path.join(DOCS, "check.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    write_names(files, redrawn, new, copied, os.path.join(DOCS, "NAMES.md"))
    from review_v2 import reviews
    reviews(images, os.path.join(DOCS, "review"))
    print("\n".join(lines))
    print("wrote", len(keep), "files to", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
