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
import marks as M  # noqa: E402
import transitions as T  # noqa: E402
import water as WA  # noqa: E402
from ramps_v2 import EXT, BASE5, NEW_RAMPS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "src", "art-release-v2", "terrain")
DOCS = os.path.join(ROOT, "docs", "art-release-v2", "terrain")

MASKS = range(1, 15)
SEASON_MAT = {"autumn": G.AUTUMN_RAMP}


def ground_tiles(ground, season=None):
    """{suffix: canvas}: the 16 edge-matched tiles (0-15) and the macro pieces (macro.q, macro2.q, macro3.q)."""
    import wang as WG

    out = {}
    if season == "winter":  # the winter of a grass-like ground: the snow tile of the same index + a few buried tips
        tip = {"grass": "grass", "plains": "plains", "lake": "lake", "moss": "pine"}[ground]

        def single(n):
            c = WG.wang_tile("snow", n)
            if n % 4 == 1:  # a few buried tips, anywhere in the tile (16 of the 64 tiles)
                M.draw_clump(c, tip, 3 + (n * 11) % 26, 4 + (n * 23) % 27, "S", light=False)
            return c

        def big(name):
            return WG.macro_canvas("snow", name)
    else:
        def single(n):
            return WG.wang_tile(ground, n, season=season)

        def big(name):
            return WG.macro_canvas(ground, name, season=season)
    look = "snow" if season == "winter" else ground
    for n in range(WG.tile_count(look)):
        out[str(n)] = single(n)
    if look not in WG.TEX4:  # macro pieces: the grass-likes, moss and path only (round 3)
        for name, k in WG.MACROS.items():
            for q, piece in enumerate(WG.cut(big(name), k)):
                out[f"{name}.{q}"] = piece
    if season == "autumn":
        for c in out.values():
            c.remap({ground: G.AUTUMN_RAMP[ground]})
    return out


def overlay_tiles(ground, tex, season=None):
    if ground == "ruin":  # one overlay per row phase R (v = R), so the courses run on into the full tiles beside it
        import wang as WG
        out = {}
        for R in range(11):
            c = WG.Canvas(32, 32, ("ruin", 3), wrap=False)
            WG.draw_ruin(c, "ruin", 0, 0, R, 3, 3)
            out.update({f"e{m}.{R}": T.overlay(c, "ruin", m, R % 2, "ruin") for m in MASKS})
        return out
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


def build_faces():
    """The cliff faces redrawn in round 3, under their v1 keys (faces_v2.py)."""
    import faces_v2 as FA

    cv = FA.build()
    errs = FA.check_joins(cv)
    if errs:
        raise SystemExit("face variants do not join: " + ", ".join(errs[:20]))
    return cv


def check_seams(cv):
    """Edge matching: for every ground (and season), every tile whose edge on a side has type t must show the
    same outermost row / column on that side (so any two tiles that agree on a shared edge's type join); macro
    pieces show the type-0 band on their outer edges. Sand / snow: the W / E columns only (nothing crosses
    their N / S edges). Ruin: the W column by (row phase, west symbol), the E column by (row phase, east symbol)."""
    import wang as WG

    errors = []
    bands = {WG.N: lambda c: [c.px[0][x] for x in range(1, 31)],
             WG.S: lambda c: [c.px[31][x] for x in range(1, 31)],
             WG.W: lambda c: [c.px[y][0] for y in range(32)],
             WG.E: lambda c: [c.px[y][31] for y in range(32)]}
    sets = sorted({k.rsplit(".", 1)[0] for k in cv if k.endswith(".15") and ".e" not in k and "water" not in k})
    for p in sets:
        look = "snow" if p.startswith("winter.") else p.rsplit(".", 1)[1]
        for side, band in bands.items():
            if look in WG.TEX4 and side in (WG.N, WG.S):
                continue
            ref = {}
            for n in range(WG.tile_count(look)):
                ty = WG.types_of(n, look)
                t = (ty.get("R"), ty[side])
                b = band(cv[f"{p}.{n}"])
                if t in ref and ref[t] != b:
                    errors.append(f"{p}.{n} side {side} type {t}")
                ref.setdefault(t, b)
            if look in WG.TEX4:
                continue
            for name, k in WG.MACROS.items():
                for q in range(k * k):
                    a, r = q % k, q // k
                    outer = {WG.N: r == 0, WG.S: r == k - 1, WG.W: a == 0, WG.E: a == k - 1}[side]
                    if outer and band(cv[f"{p}.{name}.{q}"]) != ref[(None, 0)]:
                        errors.append(f"{p}.{name}.{q} side {side}")
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
    faces = build_faces()
    cv.update(faces)  # (for the ramps used)
    files.update({k: c.image() for k, c in faces.items()})
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
    from measure_repeat import measure
    from PIL import Image

    imgs = dict(images)
    for k in ("tile.metal", "tile.walltop", "tile.wood", "tile.dark", "tile.pit"):
        imgs["v1:" + k] = Image.open(os.path.join(V1, k + ".png")).convert("RGBA")
    bands = []
    lines += ["", "32-px repeat (the inspection's measure: mean |dL| at 32 px / at 24 px on 40x24 fields; target >= 0.8)"]
    for season in (None, "autumn", "winter"):
        res = measure(imgs, season, "gplmnsd=u" if season is None else "gplm")
        lines.append(f"  {season or 'summer':<7} " + "  ".join(f"{k}:{r[2]:.2f}" for k, r in res.items()))
        bands.append(f"  {season or 'summer':<7} " + "  ".join(f"{k}:{r[3]:+.2f}/{r[4]:+.2f}" for k, r in res.items()))
    lines += ["", "32-px banding (round 3: autocorrelation at 32 px of the row means / of the column means, 40x24 fields; "
              "target <= 0.3 on snow, sand, desert, ruin and the winter grounds)"] + bands
    with open(os.path.join(DOCS, "check.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    write_names(files, redrawn, new, copied, os.path.join(DOCS, "NAMES.md"))
    from review_v2 import reviews
    reviews(images, os.path.join(DOCS, "review"), faces={k: c.image() for k, c in faces.items()})
    print("\n".join(lines))
    print("wrote", len(keep), "files to", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
