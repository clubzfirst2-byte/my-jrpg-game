"""Terrain RELEASE art (art/terrain-release): every terrain sprite of docs/art-kit/LIST.md, at the release
size, written to src/art-release/terrain/<name>.png. Method approved with the samples (PR #52):
hand-placed stamps, 5-tone ramps, light from the top left, alpha 0 / 255 only. Seasons (approved):
palette shift tone for tone + hand-drawn additions (fallen leaves, snow, blossoms).

Also writes the review material to docs/art-release/terrain/:
  sheet.png            every sprite with its name (4x)
  repeat/<name>.png    each ground tile repeated 4x4 (2x), the mixed variants per region, the cliff stacks
  scene_<season>.png   a small scene per season (1x and 3x), check.txt   measured rule checks

Run: python3 tools/terrain_release/gen_release.py   (needs Pillow)
"""

import colorsys
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import gen_samples as S  # noqa: E402
from ramps import RELEASE, RELEASE_NEW  # noqa: E402
from release_ground import (ALL, tones, set_ramp, lake_grass, forest_grass, desert_sand, mountains_snow,  # noqa: E402
                            ruin_floor, wood_floor, metal_floor, pit_tile, dark_tile, vine_tile, ramp_tile)
from release_faces import KINDS, stone_face, ruin_face, wall_face  # noqa: E402
from release_nature import tree, pine, rock, bramble, stump, cactus  # noqa: E402
from release_v11 import build_v11  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "src", "art-release", "terrain")
DOCS = os.path.join(ROOT, "docs", "art-release", "terrain")


# ---------------------------------------------------------------------------------------------
# Seasons: palette shift + hand-drawn additions.
# ---------------------------------------------------------------------------------------------
LEAF_1 = ["12", "2."]  # a fallen leaf (fire tones, guide 3.7): 3 px
LEAF_2 = [".2", "21"]
LEAF_3 = ["21", ".1"]
FALLEN = {  # per summer layout: (x, y, leaf)
    "tile.grass.0": [(8, 9, LEAF_1), (24, 20, LEAF_2), (16, 30, LEAF_3)],
    "tile.grass.1": [(20, 10, LEAF_2), (6, 19, LEAF_3)],
    "tile.grass.2": [(10, 6, LEAF_3), (27, 12, LEAF_1), (8, 22, LEAF_2)],
    "plains.grass.0": [(14, 3, LEAF_2), (27, 21, LEAF_1)],
    "plains.grass.1": [(20, 20, LEAF_1), (22, 22, LEAF_3), (5, 12, LEAF_2)],  # where the white flower was
    "plains.grass.2": [(8, 6, LEAF_2), (10, 8, LEAF_1), (25, 25, LEAF_3)],
    "plains.grass.3": [(26, 8, LEAF_3), (28, 10, LEAF_1), (9, 27, LEAF_2)],
    "lake.grass.0": [(10, 10, LEAF_1), (25, 23, LEAF_3)],
    "lake.grass.1": [(22, 5, LEAF_2), (3, 21, LEAF_1)],
    "lake.grass.2": [(7, 4, LEAF_3), (26, 15, LEAF_2)],
    "lake.grass.3": [(14, 22, LEAF_1), (3, 6, LEAF_2)],
}
BLADES = [  # grass blades poking out of the snow (summer grass colour) with a blue dent around their foot
    "3.2",
    "21.",
    "s1s",
]
BLADES_2 = [
    ".3.",
    "3.2",
    "s1s",
]
MOUND = [  # a snow mound (over a flower / a mushroom)
    ".343.",
    "33331",
    ".1111",
]
POKE = {  # per summer layout: (x, y, stamp)
    "tile.grass.0": [(9, 9, BLADES), (24, 19, BLADES_2)],
    "tile.grass.1": [(20, 10, BLADES_2), (6, 19, BLADES)],
    "tile.grass.2": [(10, 6, BLADES), (27, 12, BLADES_2), (8, 22, BLADES)],
    "plains.grass.0": [(14, 3, BLADES), (27, 21, BLADES_2)],
    "plains.grass.1": [(5, 12, BLADES_2)],
    "plains.grass.2": [(25, 25, BLADES)],
    "plains.grass.3": [(9, 27, BLADES_2)],
    "lake.grass.0": [(10, 10, BLADES), (25, 23, BLADES_2)],
    "lake.grass.1": [(22, 5, BLADES_2)],
    "lake.grass.2": [(7, 4, BLADES), (26, 15, BLADES_2)],
    "lake.grass.3": [(14, 22, BLADES)],
    "forest.grass.0": [(12, 6, BLADES_2), (27, 22, BLADES)],
    "forest.grass.1": [(3, 4, BLADES)],
    "forest.grass.2": [(6, 25, BLADES_2)],
    "forest.grass.3": [(26, 4, BLADES)],
}
FLOWER_AT = {1: (20, 20), 2: (8, 6), 3: (26, 8)}
# Winter: one tuft of blades per tile. Island grass .0 stays plain and the others sit at different
# heights (guide 3.3: a mark at the same height on every variant shows rows every 32 px). The forest
# floor gets none (its one plant is in release_ground.WINTER_FOREST_AT).
WINTER_MARK = {n: p[0] for n, p in POKE.items() if not n.startswith(("forest.", "tile.grass."))}
WINTER_MARK.update({"tile.grass.1": (6, 19, BLADES), "tile.grass.2": (24, 27, BLADES_2)})


def summer_ground(name, winter=False):
    """(tile, ground material) for a summer ground that has seasons."""
    kind, v = name.rsplit(".", 1)
    v = int(v)
    if kind == "tile.grass":
        return S.grass_tile(v), "grass"
    if kind == "plains.grass":
        layout, (dx, dy), _, _ = S.MEADOW[v]
        return S.grass_tile(layout, mat="meadow", dx=dx, dy=dy), "meadow"  # the flower is replaced per season
    if kind == "lake.grass":
        return lake_grass(v, winter=winter), "lake.grass"
    if kind == "forest.grass":
        return forest_grass(v, winter=winter), "forest.moss"
    raise KeyError(name)


def _ensure(t, *mats):
    for m in mats:
        if m not in t.ramps:
            set_ramp(t, m, m)


def autumn_ground(name):
    t, mat = summer_ground(name)
    _ensure(t, "fire")
    set_ramp(t, mat, "lake.reed" if mat == "lake.grass" else "autumn.grass")
    if mat == "lake.grass":
        set_ramp(t, "reed", "autumn.grass")  # the reed clump stands out golden on the duller shore
    for x, y, p in FALLEN[name]:
        t.stamp(x, y, p, tones("fire"))
    return t


def winter_ground(name):
    t, mat = summer_ground(name, winter=True)
    _ensure(t, "grass_g", "mount.snow")
    green = {"grass": "grass_g", "meadow": "grass_g", "lake.grass": "lakeg", "forest.moss": "forest.pine"}[mat]
    _ensure(t, green)
    set_ramp(t, mat, "mount.snow")
    # On snow the summer tufts would have ~3x the contrast ("dirty snow", design inspection 1): keep the
    # tufts as soft lit humps only (tone 3, same places as summer), no shadow tone, every second one gone.
    marks = {(x, y) for y in range(t.h) for x in range(t.w) if t.px[y][x] and t.px[y][x][0] == mat and t.px[y][x][1] != 2}
    seen, n = set(), 0
    for start in sorted(marks, key=lambda p: (p[1], p[0])):  # each tuft = one 8-connected group (wrapping)
        if start in seen:
            continue
        group, todo = set(), [start]
        while todo:
            x, y = todo.pop()
            if (x, y) in group:
                continue
            group.add((x, y))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = ((x + dx) % t.w, (y + dy) % t.h)
                    if q in marks and q not in group:
                        todo.append(q)
        seen |= group
        keep = n % 2 == 0
        n += 1
        lit = {p for p in group if t.px[p[1]][p[0]][1] >= 3}
        # no lone pixel: a lit pixel stays only with a lit neighbour (marks of 2+ px, guide 3.2)
        lit = {(x, y) for x, y in lit if any(((x + dx) % t.w, (y + dy) % t.h) in lit
                                             for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)}
        for x, y in group:
            t.px[y][x] = (mat, 3) if keep and (x, y) in lit else (mat, 2)
    kind, v = name.rsplit(".", 1)
    if kind == "plains.grass" and int(v) in FLOWER_AT:
        x, y = FLOWER_AT[int(v)]
        t.stamp(x - 1, y, MOUND, tones(mat))
    pokes = [WINTER_MARK[name]] if name in WINTER_MARK else []  # one mark, at a different height per variant
    for x, y, p in pokes:  # one tuft of blades out of the snow per tile
        t.stamp(x, y, p[:2], tones(green))
    return t


def autumn_lip(kind, seg):
    t = S.face_tile(kind, seg)
    _ensure(t, "fire")
    set_ramp(t, "grass", "autumn.grass")
    for x, y, s in [(5, 0, "21"), (14, 1, "12"), (23, 0, "21")]:  # fallen leaves on the lip
        for k, ch in enumerate(s):
            t.put(x + k, y, "fire", int(ch))
    return t


def winter_lip(kind, seg):
    t = S.face_tile(kind, seg)
    _ensure(t, "mount.snow")
    set_ramp(t, "grass", "mount.snow")
    short = seg == 4
    lip_d = [max(2, d - 1) for d in S.LIP_DEPTH] if short else S.LIP_DEPTH
    for x in range(32):  # rounder snow edge: a lit cushion row, and drips over the edge at a few places
        t.put(x, 1, "grass", 3 if lip_d[x] > 2 else 2)
    for x in (3, 4, 11, 20, 21, 27):
        if x % 9 in (2, 3, 4):
            t.put(x, 0, "grass", 4)
    for x in (7, 15, 26):
        d = lip_d[x] + S.HANG.get(x, 0)
        t.put(x, d, "grass", 2)
        t.put(x, d + 1, "grass", 1)
        t.put(x + 1, d, "grass", 1)
    return t


# ---------------------------------------------------------------------------------------------
def build():
    out = {}
    # the approved samples (unchanged)
    for v in range(3):
        out[f"tile.grass.{v}"] = S.grass_tile(v)
    out["tile.path"] = S.path_tile()
    out["tile.sand"] = S.sand_tile()
    out["tile.water.0"] = S.water_tile(0)
    out["tile.water.1"] = S.water_tile(1)
    for v in range(4):
        out[f"plains.grass.{v}"] = S.meadow_tile(v)
    for seg in (4, 8):
        for kind in KINDS:
            out[f"face.earth.{kind}.{seg}"] = S.face_tile(kind, seg)
    out["tile.walltop"] = S.walltop_tile()
    out["obj.tree"] = tree()
    # base tiles
    out["tile.ruin"] = ruin_floor()
    out["tile.ramp"] = ramp_tile()
    out["tile.metal"] = metal_floor()
    out["tile.pit"] = pit_tile()
    out["tile.vine"] = vine_tile()
    out["tile.wood"] = wood_floor()
    out["tile.dark"] = dark_tile()
    for seg in (4, 8):
        for kind in KINDS:
            out[f"face.ruin.{kind}.{seg}"] = ruin_face(kind, seg)
            out[f"face.wall.{kind}.{seg}"] = wall_face(kind, seg)
            out[f"face.stone.{kind}.{seg}"] = stone_face(kind, seg)
    # regions
    for v in range(3):
        out[f"desert.sand.{v}"] = desert_sand(v)
    for v in range(4):
        out[f"forest.grass.{v}"] = forest_grass(v)
        out[f"mountains.snow.{v}"] = mountains_snow(v)
        out[f"lake.grass.{v}"] = lake_grass(v)
    out["forest.pine"] = pine()
    out["mountains.pine"] = pine(snow=3, slim=True)
    # nature objects
    out["obj.rock"] = rock()
    out["obj.bramble"] = bramble()
    out["obj.stump"] = stump()
    out["obj.cactus"] = cactus()
    # seasons
    out["spring.obj.tree"] = tree("spring")
    out["autumn.obj.tree"] = tree("autumn")
    out["winter.obj.tree"] = tree("winter")
    out["winter.forest.pine"] = pine(snow=2)
    grounds = [f"tile.grass.{v}" for v in range(3)] + [f"plains.grass.{v}" for v in range(4)] + [f"lake.grass.{v}" for v in range(4)]
    for n in grounds:
        out[f"autumn.{n}"] = autumn_ground(n)
    for n in grounds + [f"forest.grass.{v}" for v in range(4)]:
        out[f"winter.{n}"] = winter_ground(n)
    for seg in (4, 8):
        for kind in ("top", "top-base"):
            out[f"autumn.face.earth.{kind}.{seg}"] = autumn_lip(kind, seg)
            out[f"winter.face.earth.{kind}.{seg}"] = winter_lip(kind, seg)
    V10.update(out)
    out.update(build_v11(autumn_lip, winter_lip))  # v1.1: new sprites only (release_v11.py)
    return {n: t.image() for n, t in out.items()}


# ---------------------------------------------------------------------------------------------
# Checks and review images
# ---------------------------------------------------------------------------------------------
CLOAK = "#6a9048"


def lightness(rgb):
    r, g, b = rgb[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 * 100


def hue(rgb):
    return colorsys.rgb_to_hsv(*(c / 255 for c in rgb[:3]))[0] * 360


V10 = {}  # the 111 sprites of v1.0 (filled by build)


def is_water_edge(name):
    return name.startswith(("tile.shore", "tile.bank."))


def v11_size(name):
    """The size of a v1.1 sprite (not in LIST.md): tiles 32x32, faces 32x8 / 32x16, pines 32x60."""
    base = name[:-3] if name[-3:-1] == ".v" else name
    if ".face." in "." + base:
        return (32, 8) if base.endswith(".4") else (32, 16)
    return (32, 60) if base.endswith(".pine") else (32, 32)


def is_ground(name, im):
    return not is_water_edge(name) and im.size == (32, 32) and name.split(".")[-2:] != ["obj", "tree"] and "vine" not in name


def ramp_colours():
    cols = {}
    for name, ramp in ALL.items():
        for k, c in enumerate(ramp):
            cols.setdefault(tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)), (name, k))
    return cols


def list_sizes():
    """name -> (w, h) from docs/art-kit/LIST.md."""
    import re
    sizes = {}
    with open(os.path.join(ROOT, "docs", "art-kit", "LIST.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\| `([^`]+)` \| (\d+)×(\d+)", line)
            if m:
                sizes[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return sizes


def checks(images):
    cols = ramp_colours()
    sizes = list_sizes()
    lines = ["# 自動の確認（gen_release.py が毎回書く）", ""]
    bad = []
    for n, im in images.items():
        px = list(im.get_flattened_data())
        alpha = sum(1 for p in px if p[3] not in (0, 255))
        off = {p[:3] for p in px if p[3] == 255 and p[:3] not in cols}
        size_ok = (sizes.get(n) or v11_size(n)) == im.size
        if alpha or off or not size_ok:
            bad.append(f"  {n}: 半透明 {alpha} / ランプ外の色 {len(off)} / 大きさ {im.size} 一覧 {sizes.get(n)}")
    lines.append(f"枚数: {len(images)}")
    lines.append("半透明の点・ランプ外の色・大きさの違い: " + ("なし（全部 OK）" if not bad else ""))
    lines += bad
    d = sum(1 for a, b in zip(images["tile.water.0"].get_flattened_data(), images["tile.water.1"].get_flattened_data()) if a != b)
    lines.append(f"水の 2 コマの違い: {d} ドット（ガイド 3.5：12〜30）")
    lines.append("")
    lines.append("地面（32×32）: いちばん多い色（2 番の面）・その面積・4 番の割合（3% 以下）・継ぎ目（左右・上下の端の色の差）")
    for n, im in images.items():
        if not is_ground(n, im) or n == "tile.dark":
            continue
        px = list(im.get_flattened_data())
        cnt, rgb = max(im.getcolors(4096))
        t4 = sum(1 for p in px if p[3] == 255 and cols.get(p[:3], ("", -1))[1] == 4) / len(px) * 100
        seam_x = sum(abs(lightness(im.getpixel((0, y))) - lightness(im.getpixel((31, y)))) for y in range(32)) / 32
        seam_y = sum(abs(lightness(im.getpixel((x, 0))) - lightness(im.getpixel((x, 31)))) for x in range(32)) / 32
        inner = max(max(sum(abs(lightness(im.getpixel((x, y))) - lightness(im.getpixel((x + 1, y)))) for y in range(32)) / 32
                        for x in range(31)),
                    max(sum(abs(lightness(im.getpixel((x, y))) - lightness(im.getpixel((x, y + 1)))) for x in range(32)) / 32
                        for y in range(31)))
        ls = [lightness(p) for p in px]
        mean = sum(ls) / len(ls)
        rough = (sum((v - mean) ** 2 for v in ls) / len(ls)) ** 0.5
        flag = f"  ざらつき {rough:3.1f}"
        flag += "" if t4 <= 3 else "  ← 4 番が多い"
        if max(seam_x, seam_y) > inner + 0.5:
            flag += "  ← 端の差が中より大きい"
        lines.append(f"  {n:<26} {'#%02x%02x%02x' % rgb[:3]} {100 * cnt / 1024:3.0f}%  4番 {t4:3.1f}%  "
                     f"明るさ {lightness(rgb):4.1f}（マント差 {lightness((0x6a, 0x90, 0x48)) - lightness(rgb):+5.1f}・色合い {hue(rgb):3.0f}°）  "
                     f"端の差 左右 {seam_x:3.1f} 上下 {seam_y:3.1f}（中の最大 {inner:4.1f}）{flag}")
    used = set()
    for im in images.values():
        for p in im.get_flattened_data():
            if p[3] == 255:
                used.add(cols[p[:3]][0])
    lines.append("")
    lines.append("使ったランプ: " + ", ".join(sorted(used)))
    return "\n".join(lines) + "\n", used


def sheet(images, scale=4, cols=8):
    names = list(images)
    cw, ch = 34 * scale, 64 * scale + 14
    rows = (len(names) + cols - 1) // cols
    sh = Image.new("RGBA", (cols * cw, rows * ch), (52, 54, 66, 255))
    dr = ImageDraw.Draw(sh)
    for i, n in enumerate(names):
        im = images[n]
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        sh.alpha_composite(big, (x0 + 2, y0 + 12))
        dr.text((x0 + 2, y0), n, fill=(230, 230, 230, 255))
    return sh


def repeats(images, rep_dir):
    from mock_scene import tile_hash
    os.makedirs(rep_dir, exist_ok=True)
    for n, im in images.items():
        if not is_ground(n, im) or n == "tile.dark":
            continue
        rep = Image.new("RGBA", (128, 128))
        for j in range(4):
            for i in range(4):
                rep.paste(im, (i * 32, j * 32))
        rep.resize((256, 256), Image.NEAREST).save(os.path.join(rep_dir, f"repeat_{n}.png"))
    groups = [("tile.grass", 3), ("plains.grass", 4), ("desert.sand", 3), ("forest.grass", 4), ("mountains.snow", 4),
              ("lake.grass", 4)]
    for season in ("", "autumn.", "winter."):
        for prefix, k in groups:
            names = [f"{season}{prefix}.{v}" for v in range(k)]
            if not all(n in images for n in names):
                continue
            mix = Image.new("RGBA", (256, 256))
            for j in range(8):
                for i in range(8):
                    mix.paste(images[names[tile_hash(i, j) % k]], (i * 32, j * 32))
            mix.resize((512, 512), Image.NEAREST).save(os.path.join(rep_dir, f"mixed_{season}{prefix}.png"))
    # cliff stacks per material, as gameView.addFace stacks them, with the ground above / below
    stacks = [["top-base.4"], ["top-base.8"], ["top.8", "mid-base.8"], ["top.8", "mid.8", "mid.8", "mid-base.8"],
              ["top.8", "mid.8", "mid-base.4"]]
    for mat, above, below in [("earth", "tile.grass.{}", "tile.path"), ("stone", "mountains.snow.{}", "mountains.snow.0"),
                              ("ruin", "tile.ruin", "tile.ruin"), ("wall", "tile.walltop", "tile.wood"),
                              ("autumn.earth", "autumn.tile.grass.{}", "autumn.tile.grass.0"),
                              ("winter.earth", "winter.tile.grass.{}", "winter.tile.grass.0")]:
        cw = 3 * 32 + 12
        st = Image.new("RGBA", (len(stacks) * cw + 12, 32 + 64 + 40), (34, 36, 46, 255))
        season = mat.split(".")[0] + "." if "." in mat else ""
        base_mat = mat.split(".")[-1]
        for i, segs in enumerate(stacks):
            x0 = 12 + i * cw
            for k in range(3):
                st.paste(images[above.format(k % 3)], (x0 + k * 32, 8))
                y = 40
                for sname in segs:
                    key = f"{season}face.{base_mat}.{sname}"
                    if key not in images:
                        key = f"face.{base_mat}.{sname}"
                    im = images[key]
                    st.alpha_composite(im, (x0 + k * 32, y))
                    y += im.height
                st.paste(images[below].crop((0, 0, 32, min(32, st.height - y))), (x0 + k * 32, y))
        st.resize((st.width * 2, st.height * 2), Image.NEAREST).save(os.path.join(rep_dir, f"stack_face.{mat}.png"))


def objects_on_grounds(images):
    """Each object / tree on the 5 grounds of guide 7-23 (grass, sand, snow, water, floor), 3x."""
    grounds = ["tile.grass.0", "tile.sand", "mountains.snow.0", "tile.water.0", "tile.wood"]
    objs = ["obj.tree", "spring.obj.tree", "autumn.obj.tree", "winter.obj.tree", "forest.pine", "winter.forest.pine",
            "mountains.pine", "obj.rock", "obj.bramble", "obj.stump", "obj.cactus", "tile.vine"]
    cw, ch = 40, 72
    out = Image.new("RGBA", (len(objs) * cw, len(grounds) * ch), (0, 0, 0, 255))
    for j, g in enumerate(grounds):
        for i, o in enumerate(objs):
            for yy in range(0, ch, 32):
                for xx in range(0, cw, 32):
                    out.paste(images[g], (i * cw + xx, j * ch + yy))
            im = images[o]
            out.alpha_composite(im, (i * cw + (cw - im.width) // 2, j * ch + ch - im.height - 4))
    return out.crop((0, 0, len(objs) * cw, len(grounds) * ch)).resize((out.width * 3, out.height * 3), Image.NEAREST)


def main():
    images = build()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".png") and f[:-4] not in images:
            os.remove(os.path.join(OUT, f))
    for n, im in images.items():
        im.save(os.path.join(OUT, f"{n}.png"), optimize=True)
    os.makedirs(DOCS, exist_ok=True)
    sheet({n: im for n, im in images.items() if n in V10}).save(os.path.join(DOCS, "sheet.png"))
    sheet({n: im for n, im in images.items() if n not in V10}, cols=12).save(os.path.join(DOCS, "sheet_v11.png"))
    from review_v11 import reviews, write_names
    reviews(images, DOCS)
    write_names(images, V10, os.path.join(DOCS, "NAMES.md"))
    repeats(images, os.path.join(DOCS, "repeat"))
    objects_on_grounds(images).save(os.path.join(DOCS, "objects_on_grounds.png"))
    report, used = checks(images)
    report += "新規のランプ（ガイド 2.5 に登録してほしいもの）: " + ", ".join(sorted(used & RELEASE_NEW)) + "\n"
    with open(os.path.join(DOCS, "check.txt"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("wrote", len(images), "sprites to", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
