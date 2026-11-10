"""Review images of the v2 enemy & boss art (needs Pillow; a Japanese font if there is one).

  docs/art-release-v2/enemy/sheets/<kind>.png        every v2 frame, one row per action, labelled
  docs/art-release-v2/enemy/gif/<kind>.<action>.gif  each v2 action playing on its home ground (3x)
  docs/art-release-v2/enemy/gif/<kind>.<action>.vs_v1.gif   v1 (left) and v2 (right) playing side by side
  docs/art-release-v2/enemy/compare/<kind>.png       v1 vs v2: 1x next to the hero, then 4x (2x for the
                                                     final boss) key frames of every action
Run after gen_enemy.py: python3 tools/enemy_v2/previews.py [kind ...]
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V1 = os.path.join(ROOT, "src", "art-release", "enemy")
V2 = os.path.join(ROOT, "src", "art-release-v2", "enemy")
HERO = os.path.join(ROOT, "src", "art-release", "hero", "hero.idle.right.0.png")
DOC = os.path.join(ROOT, "docs", "art-release-v2", "enemy")
BG, INK, SUB = (34, 36, 46), (240, 240, 240), (170, 172, 186)
HOME = {"beast": "#3c6a38", "archer": "#3c6a38", "slime": "#244834", "sentinel": "#947a60", "boss_root": "#244834",
        "boss_frost": "#b8c8e0", "boss_sand": "#a8603c", "boss_storm": "#22608e", "boss_source": "#302c36", "shot": "#3c6a38"}
MS = {"idle": 180, "idle2": 180, "move": 90, "windup": 150, "attack": 80, "hurt": 90, "stagger": 120, "defeat": 140,
      "transform": 140, "tendril": 120}


def font(n):
    for p in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


def ms(action):
    for k, v in MS.items():
        if action == k or action.startswith(k + "_"):
            return v
    return 90


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def load(d, name):
    p = os.path.join(d, f"{name}.png")
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None


def frames(d, man, kind, action):
    n = man["kinds"][kind]["actions"].get(action, {}).get("frames", 0)
    return [load(d, f"enemy.{kind}.{action}.{i}") for i in range(n)]


def scale_of(kind):
    return 2 if kind in ("boss_source",) else (3 if kind.startswith("boss") else 4)


def sheet(kind, man):
    sc = scale_of(kind)
    acts = man["kinds"][kind]["actions"]
    rows = [(a, frames(V2, man, kind, a)) for a in acts]
    w = 170 + max(sum(im.width * sc + 6 for im in fr) for _, fr in rows)
    h = 40 + sum(max(im.height for im in fr) * sc + 26 for _, fr in rows)
    c = Image.new("RGBA", (w, h), BG + (255,))
    d = ImageDraw.Draw(c)
    d.text((8, 8), f"{kind}  v2  ({sc}x)  — " + "  ".join(f"{a} {len(fr)}" for a, fr in rows), fill=INK, font=font(16))
    y = 40
    for a, fr in rows:
        d.text((8, y + 4), a, fill=INK, font=font(15))
        d.text((8, y + 24), f"{len(fr)} frames  {fr[0].width}x{fr[0].height}", fill=SUB, font=font(12))
        x = 170
        for im in fr:
            t = Image.new("RGBA", (im.width * sc, im.height * sc), rgb(HOME[kind]) + (255,))
            t.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST))
            c.alpha_composite(t, (x, y))
            x += im.width * sc + 6
        y += max(im.height for im in fr) * sc + 26
    os.makedirs(os.path.join(DOC, "sheets"), exist_ok=True)
    c.save(os.path.join(DOC, "sheets", f"{kind}.png"))


def gif(path, seqs, sc, ground, dur):
    """seqs: list of frame lists, drawn side by side; the longest sets the length."""
    n = max(len(s) for s in seqs)
    fw = max(im.width for s in seqs for im in s)
    fh = max(im.height for s in seqs for im in s)
    out = []
    for i in range(n):
        c = Image.new("RGBA", (len(seqs) * (fw * sc + 8) + 8, fh * sc + 16), rgb(ground) + (255,))
        for j, s in enumerate(seqs):
            im = s[i % len(s)]
            c.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST),
                              (8 + j * (fw * sc + 8) + (fw - im.width) * sc // 2, 8 + (fh - im.height) * sc))
        out.append(c.convert("RGB"))
    out[0].save(path, save_all=True, append_images=out[1:], duration=dur, loop=0)


def gifs(kind, man, man1):
    os.makedirs(os.path.join(DOC, "gif"), exist_ok=True)
    sc = 3 if not kind.startswith("boss") else 2
    for a in man["kinds"][kind]["actions"]:
        fr = frames(V2, man, kind, a)
        gif(os.path.join(DOC, "gif", f"{kind}.{a}.gif"), [fr], sc, HOME[kind], ms(a))
        old = frames(V1, man1, kind, a) if a in man1["kinds"].get(kind, {}).get("actions", {}) else []
        if old:
            # v1 played at the same total time as v2 (its 2-frame actions hold each frame longer)
            stretched = [old[int(i * len(old) / len(fr))] for i in range(len(fr))]
            gif(os.path.join(DOC, "gif", f"{kind}.{a}.vs_v1.gif"), [stretched, fr], sc, HOME[kind], ms(a))


def compare(kind, man, man1):
    sc = 4 if kind != "boss_source" else 2
    hero = Image.open(HERO).convert("RGBA")
    acts = man["kinds"][kind]["actions"]
    old_all = [load(V1, f"enemy.{kind}.{a}.{i}") for a, v in man1["kinds"][kind]["actions"].items() for i in range(v["frames"])]
    new_all = [load(V2, f"enemy.{kind}.{a}.{i}") for a, v in acts.items() for i in range(v["frames"])]
    keys = []
    for a, v in acts.items():
        if a in man1["kinds"][kind]["actions"]:
            n1 = man1["kinds"][kind]["actions"][a]["frames"]
            keys.append((a, [load(V1, f"enemy.{kind}.{a}.{i}") for i in range(n1)], frames(V2, man, kind, a)))
    fw, fh = new_all[0].size
    W1 = 140 + max(len(old_all), len(new_all)) * (fw + 3) + hero.width + 20
    per = max(1, 2400 // (fw * sc + 6))
    blocks = []
    for a, o, n in keys:
        if a in ("tendril",) or len(blocks) > 40:
            continue
        blocks.append((a, o, n))
    rows4 = sum(((len(o) + per - 1) // per) + ((len(n) + per - 1) // per) for _, o, n in blocks)
    W = max(W1, 140 + per * (fw * sc + 6))
    H = 50 + 2 * (max(fh, hero.height) + 30) + rows4 * (fh * sc + 6) + len(blocks) * 40
    c = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(c)
    d.text((8, 8), f"{kind}: v1 (src/art-release/enemy) vs v2 (src/art-release-v2/enemy) — 1x next to the hero, then {sc}x by action",
           fill=INK, font=font(16))
    y = 44
    for tag, seq in (("v1 1x", old_all), ("v2 1x", new_all)):
        d.text((8, y + 8), tag, fill=INK, font=font(15))
        row = Image.new("RGBA", (W - 140, max(fh, hero.height) + 16), rgb(HOME[kind]) + (255,))
        row.alpha_composite(hero, (4, row.height - 6 - hero.height))
        x = hero.width + 12
        for im in seq:
            if im is None or im.size != (fw, fh):
                continue
            row.alpha_composite(im, (x, row.height - 6 - im.height))
            x += fw + 3
        c.alpha_composite(row, (130, y))
        y += row.height + 14
    for a, o, n in blocks:
        d.text((8, y + 6), a, fill=INK, font=font(15))
        d.text((8, y + 26), f"v1 {len(o)} → v2 {len(n)}", fill=SUB, font=font(12))
        y += 4
        for tag, seq in (("v1", o), ("v2", n)):
            for r0 in range(0, len(seq), per):
                x = 140
                d.text((110, y + 40), tag, fill=SUB, font=font(12))
                for im in seq[r0:r0 + per]:
                    t = Image.new("RGBA", (im.width * sc, im.height * sc), rgb(HOME[kind]) + (255,))
                    t.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST))
                    c.alpha_composite(t, (x, y))
                    x += im.width * sc + 6
                y += fh * sc + 6
        y += 36
    os.makedirs(os.path.join(DOC, "compare"), exist_ok=True)
    c.crop((0, 0, W, y + 10)).save(os.path.join(DOC, "compare", f"{kind}.png"))


def main():
    with open(os.path.join(V2, "frames.json"), encoding="utf-8") as fp:
        man = json.load(fp)
    with open(os.path.join(ROOT, "docs", "art-release", "enemy", "frames.json"), encoding="utf-8") as fp:
        man1 = json.load(fp)
    only = sys.argv[1:]
    for kind in man["kinds"]:
        if only and kind not in only:
            continue
        sheet(kind, man)
        gifs(kind, man, man1)
        compare(kind, man, man1)
    print("wrote docs/art-release-v2/enemy previews")


if __name__ == "__main__":
    main()
