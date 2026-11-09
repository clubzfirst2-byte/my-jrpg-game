"""Review images for the batch 2 revision (docs/npc/release/batch2-fix/): the same sheets as
sheets.py, drawn from src/art-release/npc-revision-b2/ for the woman, the child and the smith (the
cook from src/art-release/npc/, unchanged), plus the before / after comparison and a GIF check.
Run: python3 tools/npc_release/sheets_b2fix.py
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import sheets as S  # noqa: E402

REV = os.path.join(S.ROOT, "src", "art-release", "npc-revision-b2")
FIXED = ("woman", "child", "smith")
ORIG_NPC = S.npc
S.OUT = os.path.join(S.ROOT, "docs", "npc", "release", "batch2-fix")
S.IDS = ("woman", "cook", "child", "smith")


def npc_revised(id_, action, d, i):
    if id_ in FIXED:
        return Image.open(os.path.join(REV, f"npc.{id_}.{action}.{d}.{i}.png")).convert("RGBA")
    return ORIG_NPC(id_, action, d, i)


def before_after():
    rows, labels = [], []
    for id_ in FIXED:
        rows.append([ORIG_NPC(id_, "idle", d, 0) for d in S.DIRS] + [ORIG_NPC(id_, "walk", "right", 1)])
        labels.append(f"{S.NAMES[id_]} 修正前")
        rows.append([npc_revised(id_, "idle", d, 0) for d in S.DIRS] + [npc_revised(id_, "walk", "right", 1)])
        labels.append(f"{S.NAMES[id_]} 修正後")
    return S.labelled_grid(rows, 5, 32, 56, 5, labels_top=["正面", "背面", "右", "左", "歩行（右・1）"], labels_left=labels, left=150)


def gif_check():
    """Reads every GIF back: frame count and timing (they are played, not only looked at)."""
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
    S.npc = npc_revised
    before_after().save(os.path.join(S.OUT, "00_before_after.png"))
    S.directions().save(os.path.join(S.OUT, "01_directions.png"))
    for i in S.IDS:
        S.frames_sheet(i).save(os.path.join(S.OUT, f"02_frames_{i}.png"))
        for a in S.FRAMES:
            S.gif(i, a, os.path.join(S.OUT, f"anim_{i}_{a}.gif"))
    S.hero_compare().save(os.path.join(S.OUT, "03_hero_compare.png"))
    with open(os.path.join(S.OUT, "GIF_CHECK.md"), "w") as fh:
        fh.write("# GIF の再生確認\n\nすべての GIF を読み直して、コマ数と 1 周の長さを確かめた（待機 4 コマ・毎秒 3 コマ、歩行 6 コマ・毎秒 8 コマ）。\n\n" + gif_check() + "\n")
    # the gallery: the four of batch 2, with a button for the revision (woman, child, smith)
    S.BATCH, S.BATCH1, S.REV_DIR, S.IDS = 2, FIXED, REV, ("cook",)
    shots = [("村：第 2 回の修正案と主人公（iPhone 横画面）", os.path.join(S.OUT, "05_ingame_village.png")),
             ("修正案：村の女性・村の子・鍛冶職人（近く）", os.path.join(S.OUT, "06_ingame_close.png")),
             ("修正前（第 2 回の提出版）", os.path.join(S.OUT, "07_ingame_before.png"))]
    page = S.gallery(shots)
    page = page.replace("NPC製品版 第2回：村の女性・宿の料理人・村の子・鍛冶職人（＋第1回）", "NPC製品版 第2回 最終調整：村の女性・村の子・鍛冶職人（料理人は変更なし）")
    page = page.replace("第1回：修正案", "修正案を表示")
    with open(os.path.join(S.OUT, "NPCギャラリー.html"), "w") as fh:
        fh.write(page)
    print("sheets ->", os.path.relpath(S.OUT, S.ROOT))
