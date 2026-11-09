"""Review images for NPC batch 3 (docs/npc/release/batch3/): the princess of the star ring and the
traveller. The same sheets as sheets.py (drawn from the PNGs in src/art-release/npc/), plus:
  03b_princess_hero.png  the princess beside the hero, every direction, standing and mid-step (8x)
  05_game_size.png       the two with the hero and the batch 1 / 2 villagers at game size (1x and 2x)
  GIF_CHECK.md           every GIF read back: frame count and timing
Run: python3 tools/npc_release/sheets_b3.py
"""
import os
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
    S.hero_compare().save(os.path.join(S.OUT, "03_hero_compare.png"))
    princess_hero().save(os.path.join(S.OUT, "03b_princess_hero.png"))
    S.palette().save(os.path.join(S.OUT, "04_palette.png"))
    game_size().save(os.path.join(S.OUT, "05_game_size.png"))
    with open(os.path.join(S.OUT, "GIF_CHECK.md"), "w") as fh:
        fh.write("# GIF の再生確認\n\nすべての GIF を読み直して、コマ数と 1 周の長さを確かめた（待機 4 コマ・毎秒 3 コマ、歩行 6 コマ・毎秒 8 コマ）。\n\n" + gif_check() + "\n")
    # the gallery: the two of batch 3 (no game screenshots: they are not placed in the game yet)
    S.BATCH = 1
    shots = [("ゲーム内の大きさ：主人公と 9 人（1 倍・2 倍）", os.path.join(S.OUT, "05_game_size.png")),
             ("姫と主人公（4 方向・待機と歩行）", os.path.join(S.OUT, "03b_princess_hero.png"))]
    page = S.gallery(shots)
    page = page.replace("NPC製品版 第1回：長老・雑貨屋・見張り", "NPC製品版 第3回：星環の姫・旅人")
    page = page.replace("<title>NPC製品版 第1回 ギャラリー</title>", "<title>NPC製品版 第3回 ギャラリー</title>")
    page = page.replace("<h2>ゲーム画面</h2>", "<h2>比較（ゲームにはまだ置いていない）</h2>")
    with open(os.path.join(S.OUT, "NPCギャラリー.html"), "w") as fh:
        fh.write(page)
    print("sheets ->", os.path.relpath(S.OUT, S.ROOT))
