"""Review images for NPC batch 3 (docs/npc/release/batch3/): the princess of the star ring and the
traveller. The same sheets as sheets.py (drawn from the PNGs in src/art-release/npc/), plus:
  03b_princess_hero.png  the princess beside the hero, every direction, standing and mid-step (8x)
  05_game_size.png       the two with the hero and the batch 1 / 2 villagers at game size (1x and 2x)
  06_before_after.png    revision 1: the submitted frames (commit 034515b) beside the fixed ones
  GIF_CHECK.md           every GIF read back: frame count and timing
Run: python3 tools/npc_release/sheets_b3.py
"""
import io
import os
import subprocess
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import sheets as S  # noqa: E402

S.OUT = os.path.join(S.ROOT, "docs", "npc", "release", "batch3")
S.IDS = ("princess", "traveller")
S.NAMES.update({"princess": "星環の姫", "traveller": "旅人"})
OTHERS = ("elder", "merchant", "guard", "woman", "cook", "child", "smith")


def princess_hero():
    """The princess and the hero side by side in each direction: standing (idle 0) and mid-step (walk 1)."""
    rows, labels = [], []
    for a, i in (("idle", 0), ("walk", 1)):
        row = []
        for d in S.DIRS:
            row += [S.hero(a, d, i), S.npc("princess", a, d, i)]
        rows.append(row)
        labels.append("待機" if a == "idle" else "歩行")
    tops = []
    for d in S.DIRS:
        tops += [f"主人公・{d}", f"姫・{d}"]
    return S.labelled_grid(rows, 8, 32, 56, 6, labels_top=tops, labels_left=labels, left=70)


def hero_compare():
    """sheets.hero_compare with room for the game-size label on the right (it was cut off)."""
    f = S.font(18)
    figs = [("hero", S.hero("idle", "down", 0))] + [(i, S.npc(i, "idle", "down", 0)) for i in S.IDS]
    figs_side = [("hero", S.hero("idle", "right", 0))] + [(i, S.npc(i, "idle", "right", 0)) for i in S.IDS]
    k = 6
    x0 = 40 + len(figs) * (32 * k + 30) + 10
    W = x0 + max(len(figs) * 44 + 40, 330)
    Hh = 56 * k * 2 + 140
    c = Image.new("RGBA", (W, Hh), (34, 38, 46, 255))
    g = ImageDraw.Draw(c)
    for row, items in enumerate((figs, figs_side)):
        y0 = 50 + row * (56 * k + 40)
        ground = y0 + 56 * k
        tile = Image.new("RGBA", (len(items) * (32 * k + 30) + 10, 56 * k), S.GRASS)
        c.alpha_composite(tile, (30, y0))
        for n, (id_, im) in enumerate(items):
            x = 40 + n * (32 * k + 30)
            c.alpha_composite(S.big(im, k), (x, y0))
            g.text((x + 4, y0 - 30 if row == 0 else ground + 4), S.NAMES[id_], fill=(240, 240, 240), font=f)
        for yy in (0, 4, 8):  # height lines (art rows)
            g.line([(30, y0 + yy * k), (30 + tile.width, y0 + yy * k)], fill=(255, 255, 255, 90), width=1)
    g.text((x0, 20), "ゲーム内の大きさ（16×28・2倍表示）", fill=(240, 240, 240), font=S.font(16))
    tile = Image.new("RGBA", (len(figs) * 44 + 20, 56 * 2 + 20), S.GRASS)
    c.alpha_composite(tile, (x0, 50))
    for n, (id_, im) in enumerate(figs):
        small = im.resize((16, 28), Image.NEAREST).resize((32, 56), Image.NEAREST)
        c.alpha_composite(small, (x0 + 10 + n * 44, 60))
    return c


SUBMITTED = "034515b"  # the first submission of batch 3 (before the review's fixes)


def submitted(id_, action, d, i):
    blob = f"{SUBMITTED}:src/art-release/npc/npc.{id_}.{action}.{d}.{i}.png"
    data = subprocess.check_output(["git", "-C", S.ROOT, "show", blob])
    return Image.open(io.BytesIO(data)).convert("RGBA")


def before_after():
    """Revision 1: each fixed view, the submitted frame (left) and the fixed one (right), 5x."""
    views = {"princess": [("idle", "down", 0), ("idle", "up", 0), ("idle", "right", 0)],
             "traveller": [("idle", "down", 0), ("idle", "up", 2), ("walk", "right", 3)]}
    rows, labels = [], []
    for id_ in S.IDS:
        row = []
        for v in views[id_]:
            row += [submitted(id_, *v), S.npc(id_, *v)]
        rows.append(row)
        labels.append(S.NAMES[id_])
    tops = []
    for a, d, i in views["princess"]:
        tops += [f"前 {d}", f"後 {d}"]
    return S.labelled_grid(rows, 6, 32, 56, 5, labels_top=tops, labels_left=labels, left=90)


def game_size():
    """Everyone at game size: 16x28 game pixels drawn as 32x56 (2 pixels per game pixel, as on an iPhone),
    shown once at 1x and once at 2x."""
    figs = [S.hero("idle", "down", 0)] + [S.npc(i, "idle", "down", 0) for i in OTHERS + S.IDS]
    names = ["主人公"] + [S.NAMES[i] for i in OTHERS + S.IDS]
    w = len(figs) * 36 + 8
    strip = Image.new("RGBA", (w, 64), S.GRASS)
    for n, im in enumerate(figs):
        strip.alpha_composite(im, (6 + n * 36, 4))
    out = Image.new("RGBA", (w * 2 + 20, 64 * 3 + 64 + 40), (34, 38, 46, 255))
    out.alpha_composite(strip, (10, 30))
    out.alpha_composite(S.big(strip, 2), (10, 64 + 60))
    g = ImageDraw.Draw(out)
    f = S.font(14)
    g.text((10, 8), "1倍（実機の Retina 画面と同じ点の数）", fill=(230, 230, 230), font=f)
    g.text((10, 64 + 38), "2倍", fill=(230, 230, 230), font=f)
    for n, t in enumerate(names):
        g.text((10 + (6 + n * 36) * 2, 64 + 60 + 128 + 4), t, fill=(230, 230, 230), font=S.font(12))
    return out


def gif_check():
    lines = []
    for id_ in S.IDS:
        for a, n in S.FRAMES.items():
            path = os.path.join(S.OUT, f"anim_{id_}_{a}.gif")
            im = Image.open(path)
            frames, total = 0, 0
            try:
                while True:
                    frames += 1
                    total += im.info.get("duration", 0)
                    im.seek(im.tell() + 1)
            except EOFError:
                pass
            lines.append(f"| `anim_{id_}_{a}.gif` | {frames} | {total} ms | {'OK' if frames == n else 'NG'} |")
    return "\n".join(["| GIF | コマ数 | 1 周の長さ | 判定 |", "|---|---|---|---|"] + lines)


if __name__ == "__main__":
    os.makedirs(S.OUT, exist_ok=True)
    S.directions().save(os.path.join(S.OUT, "01_directions.png"))
    for i in S.IDS:
        S.frames_sheet(i).save(os.path.join(S.OUT, f"02_frames_{i}.png"))
        for a in S.FRAMES:
            S.gif(i, a, os.path.join(S.OUT, f"anim_{i}_{a}.gif"))
    hero_compare().save(os.path.join(S.OUT, "03_hero_compare.png"))
    before_after().save(os.path.join(S.OUT, "06_before_after.png"))
    princess_hero().save(os.path.join(S.OUT, "03b_princess_hero.png"))
    S.palette().save(os.path.join(S.OUT, "04_palette.png"))
    game_size().save(os.path.join(S.OUT, "05_game_size.png"))
    with open(os.path.join(S.OUT, "GIF_CHECK.md"), "w") as fh:
        fh.write("# GIF の再生確認\n\nすべての GIF を読み直して、コマ数と 1 周の長さを確かめた（待機 4 コマ・毎秒 3 コマ、歩行 6 コマ・毎秒 8 コマ）。\n\n" + gif_check() + "\n")
    # the gallery: the two of batch 3 (no game screenshots: they are not placed in the game yet)
    S.BATCH = 1
    shots = [("ゲーム内の大きさ：主人公と 9 人（1 倍・2 倍）", os.path.join(S.OUT, "05_game_size.png")),
             ("姫と主人公（4 方向・待機と歩行）", os.path.join(S.OUT, "03b_princess_hero.png")),
             ("修正の前と後（左：提出時 034515b、右：修正後）", os.path.join(S.OUT, "06_before_after.png"))]
    page = S.gallery(shots)
    page = page.replace("NPC製品版 第1回：長老・雑貨屋・見張り", "NPC製品版 第3回：星環の姫・旅人")
    page = page.replace("<title>NPC製品版 第1回 ギャラリー</title>", "<title>NPC製品版 第3回 ギャラリー</title>")
    page = page.replace("<h2>ゲーム画面</h2>", "<h2>比較（ゲームにはまだ置いていない）</h2>")
    with open(os.path.join(S.OUT, "NPCギャラリー.html"), "w") as fh:
        fh.write(page)
    print("sheets ->", os.path.relpath(S.OUT, S.ROOT))
