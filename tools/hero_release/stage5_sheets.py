"""Review sheets for stage 5 (docs/hero/release/stage5/) and stage 6 (docs/hero/release/stage6/).
Every frame is labelled with its action, direction and frame number.

  python3 tools/hero_release/stage5_sheets.py <folder with the stage-4 frames>
  python3 tools/hero_release/stage5_sheets.py <folder with the stage-5 frames> stage6
"""

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from previews import BG, GRASS, INK, REL, font  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "hero", "release", "stage5")
DIRS = ("down", "up", "right", "left")
DJ = {"down": "下", "up": "上", "right": "右", "left": "左"}
ACT = {"idle": "待機", "walk": "歩行", "run": "走行", "jump": "ジャンプ", "land": "着地", "glide": "滑空", "climb": "崖登り",
       "swim": "水泳", "dodge": "回避", "attack1": "剣 1 段", "attack2": "剣 2 段", "attack3": "剣 3 段", "bow": "弓",
       "guard": "盾", "hurt": "被弾", "down": "倒れる"}
COUNT = {"idle": 4, "walk": 6, "run": 6, "jump": 2, "land": 2, "glide": 4, "climb": 4, "swim": 4, "dodge": 4, "attack1": 4,
         "attack2": 4, "attack3": 6, "bow": 4, "guard": 2, "hurt": 2, "down": 4}
DIM = (170, 172, 184)


def cell(path, scale):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, GRASS + (255,))
    bg.alpha_composite(im)
    return bg.resize((im.width * scale, im.height * scale), Image.NEAREST)


def place(out, path, scale, x, y):
    t = cell(path, scale)
    out.paste(t, (x + (48 * scale - t.width) // 2, y))


def table(actions, name, scale=3, src=REL):
    """Rows: action × direction; columns: frames, each with its number."""
    cw, ch = 48 * scale + 6, 56 * scale + 28
    n = max(COUNT[a] for a in actions)
    out = Image.new("RGB", (200 + cw * n, 10 + ch * len(actions) * 4), BG)
    d = ImageDraw.Draw(out)
    y = 10
    for a in actions:
        for dr in DIRS:
            d.text((10, y + ch // 2 - 22), f"{ACT[a]}（{a}）", fill=INK, font=font(18))
            d.text((10, y + ch // 2 + 2), f"{DJ[dr]}向き（{dr}）", fill=DIM, font=font(15))
            for i in range(COUNT[a]):
                x = 200 + i * cw
                d.text((x + 4, y), f"{a}.{dr}.{i}", fill=DIM, font=font(13))
                place(out, os.path.join(src, f"hero.{a}.{dr}.{i}.png"), scale, x, y + 22)
            y += ch
    out.save(os.path.join(OUT, name))


def compare(before, pairs, name, scale=4, title=("修正前（第 4 段階）", "修正後（第 5 段階）")):
    """Two rows: the same frames before and after."""
    cw, ch = 48 * scale + 8, 56 * scale + 30
    out = Image.new("RGB", (190 + cw * len(pairs), 10 + ch * 2), BG)
    d = ImageDraw.Draw(out)
    for r, (src, label) in enumerate(((before, title[0]), (REL, title[1]))):
        y = 10 + r * ch
        d.text((10, y + ch // 2 - 10), label, fill=INK, font=font(18))
        for i, (key, note) in enumerate(pairs):
            x = 190 + i * cw
            d.text((x + 4, y), f"{key[5:]}  {note}", fill=DIM, font=font(13))
            place(out, os.path.join(src, f"{key}.png"), scale, x, y + 24)
    out.save(os.path.join(OUT, name))


def strip(keys, name, scale=4, rows=None):
    """Labelled frames side by side (rows: lists of (key, label))."""
    rows = rows or [keys]
    cw, ch = 48 * scale + 8, 56 * scale + 30
    out = Image.new("RGB", (20 + cw * max(len(r) for r in rows), 10 + ch * len(rows)), BG)
    d = ImageDraw.Draw(out)
    for r, row in enumerate(rows):
        for i, (key, label) in enumerate(row):
            x, y = 10 + i * cw, 10 + r * ch
            d.text((x + 4, y), label, fill=INK, font=font(14))
            place(out, os.path.join(REL, f"{key}.png"), scale, x, y + 24)
    out.save(os.path.join(OUT, name))


def main(before):
    os.makedirs(OUT, exist_ok=True)
    # 1 / problem frames enlarged: the four issues of stage 4, before and after
    compare(before, [("hero.glide.down.0", "滑空：握る"), ("hero.glide.right.0", "滑空：横"), ("hero.attack1.down.0", "振りかぶり"),
                     ("hero.attack1.down.2", "振り抜き"), ("hero.attack1.left.1", "左向き剣"), ("hero.guard.left.1", "左向き盾"),
                     ("hero.bow.left.3", "左向き弓"), ("hero.attack1.up.2", "背面の攻撃"), ("hero.run.right.1", "走行の腕")],
            "01_before_after.png", scale=4)
    compare(before, [("hero.glide.down.1", "滑空"), ("hero.attack1.left.0", "左・振りかぶり"), ("hero.attack1.up.1", "背面"),
                     ("hero.attack3.up.1", "背面・決め")], "01b_problem_frames_zoom.png", scale=7)
    # 3 / the four directions side by side (sword, shield, bow, glide)
    strip(None, "03_four_directions.png", rows=[[(f"hero.{a}.{d}.{i}", f"{ACT[a]} {DJ[d]}向き {i}") for d in DIRS]
                                                 for a, i in (("attack1", 1), ("attack2", 2), ("guard", 1), ("bow", 3), ("glide", 0))], scale=3)
    # 4 / 5 / every frame
    table(["jump", "land", "glide", "climb", "swim", "dodge", "attack1"], "04a_actions_all_frames.png")
    table(["attack2", "attack3", "bow", "guard", "hurt", "down"], "04b_actions_all_frames.png")
    table(["idle", "walk", "run"], "05_idle_walk_run_all_frames.png")
    # one sheet per action too (big enough to read on a page)
    for k, a in enumerate(["jump", "land", "glide", "climb", "swim", "dodge", "attack1", "attack2", "attack3", "bow", "guard", "hurt", "down"]):
        table([a], f"04_{k + 1:02d}_{a}.png", scale=4)
    for a in ("idle", "walk", "run"):
        table([a], f"05_{a}.png", scale=4)
    # 6 / right and left for the weapons
    rows = []
    for a in ("attack1", "attack2", "attack3", "guard", "bow"):
        for d in ("right", "left"):
            rows.append([(f"hero.{a}.{d}.{i}", f"{ACT[a]} {DJ[d]}向き {i}") for i in range(COUNT[a])])
    strip(None, "06_weapons_right_left.png", rows=rows, scale=3)
    # 7 / the glide
    table(["glide"], "07_glide_all_frames.png", scale=4)


def main6(before):
    """Stage 6 review sheets (docs/hero/release/stage6/), against the stage-5 frames in `before`."""
    global OUT
    OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "hero", "release", "stage6")
    os.makedirs(OUT, exist_ok=True)
    title = ("修正前（第 5 段階）", "修正後（第 6 段階）")
    compare(before, [("hero.attack2.right.2", "振り上げ"), ("hero.attack2.left.2", "振り上げ"), ("hero.attack3.right.2", "振り上げ"),
                     ("hero.attack3.left.2", "振り上げ"), ("hero.attack1.left.1", "左・柄"), ("hero.attack2.left.1", "左・柄"),
                     ("hero.bow.up.2", "背面の弓"), ("hero.bow.up.3", "背面の弓")], "01_before_after.png", scale=4, title=title)
    # every frame that changed, before and after
    changed = []
    for f in sorted(os.listdir(REL)):
        a, b = os.path.join(before, f), os.path.join(REL, f)
        if not os.path.exists(a) or open(a, "rb").read() != open(b, "rb").read():
            changed.append(f[:-4])
    for k in range(0, len(changed), 8):
        compare(before, [(c, "") for c in changed[k:k + 8]], f"02_changed_{k // 8 + 1}.png", scale=3, title=title)
    with open(os.path.join(OUT, "02_changed_list.txt"), "w") as fh:
        fh.write("\n".join(changed) + "\n")
    strip(None, "03_four_directions.png", rows=[[(f"hero.{a}.{d}.{i}", f"{ACT[a]} {DJ[d]}向き {i}") for d in DIRS]
                                                 for a, i in (("attack1", 1), ("attack2", 2), ("attack3", 2), ("guard", 1), ("bow", 3), ("glide", 0))], scale=3)
    rows = []
    for a in ("attack1", "attack2", "attack3", "guard", "bow"):
        for d in ("right", "left"):
            rows.append([(f"hero.{a}.{d}.{i}", f"{ACT[a]} {DJ[d]}向き {i}") for i in range(COUNT[a])])
    strip(None, "04_weapons_right_left.png", rows=rows, scale=3)
    strip(None, "05_back_weapons.png", rows=[[(f"hero.{a}.up.{i}", f"{ACT[a]} 上向き {i}") for i in range(COUNT[a])]
                                              for a in ("attack1", "attack2", "attack3", "bow", "guard")], scale=3)
    table(["glide"], "06_glide_all_frames.png", scale=4)
    for a in ("idle", "walk", "run", "attack1", "attack2", "attack3", "jump", "land", "dodge"):
        table([a], f"07_{a}.png", scale=4)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "stage6":
        main6(sys.argv[1])
    else:
        main(sys.argv[1])
