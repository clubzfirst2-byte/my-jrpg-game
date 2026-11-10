"""Review images for the v1.1 terrain sprites (docs/art-release/terrain/v11/):
  shore_<set>_<frame>.png   a small map of land and water put together the way the engine would (mask of
                            the 4 water sides, inner corners where only a diagonal is water), 3x
  cliffs.png                long cliffs: v0 / v1 / v2 picked per tile, for every material, and the plateau faces, 2x
  autumn.png                the forest and the mountains in autumn, mixed variants, with their pines, 2x
"""

import os

from PIL import Image

from mock_scene import tile_hash


def release_variant(h, n):
    """terrainArt.groundVariant for the release art: variant 0 on about half the ground, the others an equal share."""
    k = h % (2 * n)
    return 0 if k <= n else k - n

# The demo map: ~ water, L land. A lake with a bay, an islet, a peninsula and a channel.
MAP = [
    "LLLLLLLLLLLLLLLL",
    "LLLLL~~~~LLLLLLL",
    "LLL~~~~~~~~LLLLL",
    "LL~~~~~~~~~~LLLL",
    "LL~~~LL~~~~~~LLL",
    "LL~~~LL~~~L~~LLL",
    "LLL~~~~~~~~~LLLL",
    "LLLL~~~~~~LLLLLL",
    "LLLLLL~~LLLLLLLL",
    "LLLLLL~~LLLLLLLL",
    "LLLLLLLLLLLLLLLL",
]


def _key(prefix, x, y, frame):
    def w(xx, yy):
        return 0 <= yy < len(MAP) and 0 <= xx < len(MAP[0]) and MAP[yy][xx] == "~"

    mask = (1 if w(x, y - 1) else 0) | (2 if w(x + 1, y) else 0) | (4 if w(x, y + 1) else 0) | (8 if w(x - 1, y) else 0)
    if mask:
        return f"{prefix}.{mask}.{frame}"
    for name, (dx, dy) in (("ne", (1, -1)), ("se", (1, 1)), ("sw", (-1, 1)), ("nw", (-1, -1))):
        if w(x + dx, y + dy):
            return f"{prefix}.inner.{name}.{frame}"
    return None


def shore_map(images, prefix, land, frame, overlay=False):
    im = Image.new("RGBA", (32 * len(MAP[0]), 32 * len(MAP)))
    for y, row in enumerate(MAP):
        for x, c in enumerate(row):
            if c == "~":
                im.paste(images[f"tile.water.{frame}"], (x * 32, y * 32))
                continue
            im.paste(images[land.format(tile_hash(x, y) % 3)], (x * 32, y * 32))
            k = _key(prefix, x, y, frame)
            if k:
                if overlay:
                    im.alpha_composite(images[k], (x * 32, y * 32))
                else:
                    im.paste(images[k], (x * 32, y * 32))
    return im.resize((im.width * 3, im.height * 3), Image.NEAREST)


def cliffs(images):
    rows = []
    for season, base, top in (("", "earth", "tile.grass.{}"), ("", "stone", "mountains.snow.{}"), ("", "ruin", "tile.ruin"),
                              ("", "wall", "tile.walltop"), ("", "sand", "tile.sand"), ("", "desert", "desert.sand.{}"),
                              ("", "path", "tile.path"), ("autumn", "earth", "autumn.tile.grass.{}"),
                              ("winter", "earth", "winter.tile.grass.{}"), ("autumn", "stone", "autumn.mountains.snow.{}")):
        n = 12
        strip = Image.new("RGBA", (n * 32, 32 + 64), (34, 36, 46, 255))
        for i in range(n):
            var = tile_hash(i, 7) % 3 if base in ("earth", "stone", "ruin", "wall") else 0
            strip.paste(images[top.format(i % 3)], (i * 32, 0))
            y = 32
            for seg in ("top.8", "mid.8", "mid.8", "mid-base.8"):
                v = f".v{var}" if var else ""
                names = ([f"{season}.face.{base}.{seg}{v}", f"{season}.face.{base}.{seg}"] if season else []) + [f"face.{base}.{seg}{v}"]
                key = next(k for k in names if k in images)
                strip.alpha_composite(images[key], (i * 32, y))
                y += 16
        rows.append(strip)
    out = Image.new("RGBA", (rows[0].width, sum(r.height + 8 for r in rows)), (20, 20, 26, 255))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + 8
    return out.resize((out.width * 2, out.height * 2), Image.NEAREST)


def autumn(images):
    out = Image.new("RGBA", (2 * 8 * 32 + 16, 6 * 32), (20, 20, 26, 255))
    for k, (ground, pine) in enumerate((("autumn.forest.grass", "autumn.forest.pine"), ("autumn.mountains.snow", "autumn.mountains.pine"))):
        x0 = k * (8 * 32 + 16)
        for y in range(6):
            for x in range(8):
                out.paste(images[f"{ground}.{release_variant(tile_hash(x, y), 4)}"], (x0 + x * 32, y * 32))
        for i, (px, py) in enumerate(((1, 3), (4, 2), (6, 5))):
            im = images[pine]
            out.alpha_composite(im, (x0 + px * 32, py * 32 + 32 - im.height))
    return out.resize((out.width * 2, out.height * 2), Image.NEAREST)


def reviews(images, docs):
    d = os.path.join(docs, "v11")
    os.makedirs(d, exist_ok=True)
    for f in (0, 1):
        shore_map(images, "tile.shore", "tile.sand", f).save(os.path.join(d, f"shore_tile.shore_{f}.png"))
        shore_map(images, "tile.shore-desert", "desert.sand.{}", f).save(os.path.join(d, f"shore_tile.shore-desert_{f}.png"))
        shore_map(images, "tile.bank", "tile.grass.{}", f, overlay=True).save(os.path.join(d, f"shore_tile.bank_grass_{f}.png"))
    shore_map(images, "tile.bank", "forest.grass.{}", 0, overlay=True).save(os.path.join(d, "shore_tile.bank_forest_0.png"))
    shore_map(images, "tile.bank", "winter.plains.grass.{}", 0, overlay=True).save(os.path.join(d, "shore_tile.bank_winter_0.png"))
    shore_map(images, "tile.bank", "mountains.snow.{}", 0, overlay=True).save(os.path.join(d, "shore_tile.bank_snow_0.png"))
    cliffs(images).save(os.path.join(d, "cliffs.png"))
    autumn(images).save(os.path.join(d, "autumn.png"))


GROUPS = [  # (title, how the engine uses it, test on the name)
    ("Water edges: island sand", "Instead of `tile.sand` on a sand tile next to water. Full tile (opaque). "
     "Animate with the water (frame = the water's frame).", lambda n: n.startswith("tile.shore.")),
    ("Water edges: desert sand", "Instead of `desert.sand.N` on a desert sand tile next to water. Full tile (opaque). "
     "Animate with the water.", lambda n: n.startswith("tile.shore-desert.")),
    ("Water edges: grass banks (overlay)", "Drawn ON TOP of the grass-like ground of a tile next to water (island / plains / "
     "lake grass, forest moss, mountain snow and their season variants): transparent on the land side, opaque water, "
     "foam and a 1-2 px earth bank. Animate with the water.", lambda n: n.startswith("tile.bank.")),
    ("Cliff band variants", "Pick per tile (e.g. `hash(tx, ty) % 3`: 0 = the existing key without suffix, 1 = `.v1`, 2 = `.v2`) "
     "for every segment of that tile's face. All variants join each other and the existing faces.",
     lambda n: n.startswith("face.") and n[-3:-1] == ".v" and not n.startswith(("face.sand.", "face.desert.", "face.path."))),
    ("Season lips of the cliff variants", "`<season>.<key>` like every season key: the season bundle replaces the variant key.",
     lambda n: n.startswith(("autumn.face.earth.", "winter.face.earth.")) and n[-3:-1] == ".v"),
    ("Plateau faces", "`face.sand.*` under a raised `tile.sand`, `face.desert.*` under raised desert sand, `face.path.*` "
     "under a raised path (instead of `face.earth.*`). Same parts and stacking as `face.earth.*`. Each part also has a "
     "`.v1` (other pebble / clod positions): pick per tile (e.g. `hash % 2`: 0 = no suffix, 1 = `.v1`).",
     lambda n: n.startswith(("face.sand.", "face.desert.", "face.path."))),
    ("Autumn: forest and mountains", "`<season>.<key>` keys for the autumn season bundle (add them to its key set, like "
     "`autumn.tile.grass.0`). `autumn.mountains.snow.N` is the mountains' ground in autumn (mostly snow: .0 plain, .1-.3 one small melted patch of warm rock and dry grass).",
     lambda n: n.startswith(("autumn.forest.", "autumn.mountains.", "autumn.face.stone."))),
]


def write_names(images, v10, path):
    """docs/art-release/terrain/NAMES.md: every v1.1 key with size, anchor and frames."""
    new = [n for n in images if n not in v10]
    lines = ["# Terrain v1.1: new sprite keys (for wiring)", "",
             f"{len(new)} new PNGs in `src/art-release/terrain/` (the 111 of v1.0 are unchanged). Generated by "
             "`tools/terrain_release/gen_release.py` (`release_v11.py`); this file is written by it too.", "",
             "- Anchor: **top-left** for every tile and face (like `tile.*` / `face.*`); **feet** (bottom centre) for the pines.",
             "- Frames: `.0` / `.1` at the end of the water-edge keys = the 2 frames of `tile.water` (show the same frame as the water). "
             "Everything else has 1 frame.",
             "- Mask (water edges): bit N = 1, E = 2, S = 4, W = 8 = the 4-neighbours that are WATER; 1-15. "
             "`inner.<ne|se|sw|nw>`: no 4-neighbour is water, only that diagonal one. A tile with mask 0 and 2+ diagonal "
             "water neighbours has no piece (use the plain ground; rare in the maps).",
             "- Season keys follow the existing scheme `<season>.<key>` (gameView.seasonKey).",
             "- Each water-edge piece's 2 frames differ by 12-30 px, like `tile.water` (guide 3.5).",
             "- No water edge for path (`=`) or ruin floor (`u`) next to water (~150 tiles in the maps): they keep the "
             "straight edge (built stone and roads; by design).", ""]
    for title, how, test in GROUPS:
        names = [n for n in new if test(n)]
        if not names:
            continue
        lines += [f"## {title} ({len(names)})", "", how, "", "| key | size | anchor | frames |", "|---|---|---|---|"]
        seen = set()
        for n in names:
            frame = n.rsplit(".", 1)[1] if n.startswith(("tile.shore", "tile.bank.")) else None
            key = n.rsplit(".", 1)[0] + ".<0|1>" if frame else n
            if key in seen:
                continue
            seen.add(key)
            w, h = images[n].size
            anchor = "feet" if n.endswith(".pine") else "top-left"
            lines.append(f"| `{key}` | {w}×{h} | {anchor} | {2 if frame else 1} |")
        lines.append("")
    assert sum(1 for n in new if any(t(n) for _, _, t in GROUPS)) == len(new), "a new key in no group"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
