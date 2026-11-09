"""Preview images of the enemy & boss release art (needs Pillow and a Japanese font).

  docs/art-release/enemy/sheets/<kind>.png   every frame of one character, by action, labelled
  docs/art-release/enemy/gif/<kind>.<action>.gif   each action playing, on its own ground
  docs/art-release/enemy/compare_1x.png      the hero next to every enemy at 1x on 10 grounds (+ 2x)
  docs/art-release/enemy/arenas.png          each boss on its arena grounds next to the hero (1x and 2x)
  docs/art-release/enemy/minimal.png         the 12 frames of the minimal set (the code's current names)
  docs/art-release/enemy/silhouettes.png     black silhouettes of every character
Run after gen_enemy.py: python3 tools/enemy_release/previews.py
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src", "art-release", "enemy")
HERO = os.path.join(ROOT, "src", "art-release", "hero")
DOC = os.path.join(ROOT, "docs", "art-release", "enemy")
BG, INK, SUB = (34, 36, 46), (240, 240, 240), (170, 172, 186)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# grounds: the art style guide 2.5, tone 2 (the widest colour of each ground)
GROUNDS = [("草原の草", "#3c6a38"), ("森の苔", "#244834"), ("沼", "#36402a"), ("雪", "#b8c8e0"), ("灰紫の岩", "#585668"),
           ("赤い砂", "#a8603c"), ("砂岩", "#947a60"), ("深い水", "#22608e"), ("岸の草", "#36684c"), ("遺跡の石", "#5a6468"),
           ("洞窟の岩", "#2c2c3a")]
HOME = {"beast": "#3c6a38", "archer": "#3c6a38", "slime": "#244834", "sentinel": "#947a60", "boss_root": "#244834",
        "boss_frost": "#b8c8e0", "boss_sand": "#a8603c", "boss_storm": "#22608e", "boss_source": "#302c36", "shot": "#3c6a38"}
ARENA = {"boss_root": ["#244834"], "boss_frost": ["#b8c8e0", "#585668"], "boss_sand": ["#a8603c", "#947a60"],
         "boss_storm": ["#22608e", "#36684c"], "boss_source": ["#302c36"]}
JA = {"beast": "澱の獣", "archer": "小鬼の呪い手（archer）", "slime": "澱だまり", "sentinel": "遺跡の番兵", "boss_root": "朽ち根のヌシ",
      "boss_frost": "凍て角のヌシ", "boss_sand": "砂嵐のヌシ", "boss_storm": "雷鳴のヌシ", "boss_source": "淀みの源", "shot": "弾"}
ACT_JA = {"idle": "待機", "move": "移動", "windup": "構え", "attack": "攻撃", "hurt": "ひるみ", "defeat": "倒れる／浄化",
          "stagger": "よろけ", "idle2": "第2段階の待機", "transform": "変身", "tendril": "触手（別の絵）", "orb": "澱の玉",
          "ice": "氷", "sand": "砂", "spark": "火花"}
SPEED = {"idle": 400, "idle2": 400, "move": 140, "windup": 250, "attack": 160, "hurt": 300, "defeat": 260, "stagger": 220,
         "transform": 240, "tendril": 200}


def font(n):
    for p in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


def load(name):
    return Image.open(os.path.join(SRC, f"{name}.png")).convert("RGBA")


def hero():
    return Image.open(os.path.join(HERO, "hero.idle.right.0.png")).convert("RGBA")


def act_ja(a):
    if a.startswith("windup_"):
        return "構え・" + a[7:]
    if a.startswith("attack_"):
        return "攻撃・" + a[7:]
    return ACT_JA.get(a, a)


def on(img, color, pad=2):
    t = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), rgb(color) + (255,))
    t.alpha_composite(img, (pad, pad))
    return t


def up(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def sheet(kind, info):
    k = 2 if kind.startswith("boss") else 4 if kind == "shot" else 3
    acts = list(info["actions"].items())
    cw = max(a["size"][0] for _, a in acts) * k + 8
    rows = []
    for a, d in acts:
        rows.append((a, d, d["size"][1] * k + 8))
    ncol = max(d["frames"] for _, d in acts)
    W = 220 + cw * ncol + 10
    Hh = 60 + sum(h + 10 for _, _, h in rows)
    out = Image.new("RGB", (W, Hh), BG)
    g = ImageDraw.Draw(out)
    g.text((10, 10), f"{JA[kind]}（enemy.{kind}.*）  {k} 倍・{'右向き（左は反転）' if info['facing'] == 'right' else '正面'}", fill=INK, font=font(22))
    y = 50
    for a, d, h in rows:
        g.text((10, y + h // 2 - 22), act_ja(a), fill=INK, font=font(18))
        g.text((10, y + h // 2 + 2), f"{a} ×{d['frames']}  {d['size'][0]}×{d['size'][1]}", fill=SUB, font=font(13))
        for i in range(d["frames"]):
            im = up(on(load(f"enemy.{kind}.{a}.{i}"), HOME[kind]), k)
            out.paste(im, (220 + i * cw, y))
        y += h + 10
    os.makedirs(os.path.join(DOC, "sheets"), exist_ok=True)
    out.save(os.path.join(DOC, "sheets", f"{kind}.png"))


def gifs(kind, info):
    k = 2 if kind.startswith("boss") else 4 if kind == "shot" else 3
    os.makedirs(os.path.join(DOC, "gif"), exist_ok=True)
    for a, d in info["actions"].items():
        base = a.split("_")[0]
        frames = [up(on(load(f"enemy.{kind}.{a}.{i}"), HOME[kind], 4), k).convert("P", palette=Image.ADAPTIVE) for i in range(d["frames"])]
        dur = SPEED.get(base, 160) if kind != "shot" else 120
        if base == "defeat":
            durs = [dur] * (len(frames) - 1) + [900]
        else:
            durs = [dur] * len(frames)
        frames[0].save(os.path.join(DOC, "gif", f"{kind}.{a}.gif"), save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1)


def compare(man):
    """The hero next to each enemy (idle) at 1x on every ground, then the same at 2x."""
    h = hero()
    items = [h] + [load(f"enemy.{k}.idle.0") for k in ("beast", "archer", "slime", "sentinel")] + [load("enemy.shot.orb.0")]
    strips = []
    for name, col in GROUNDS:
        w = sum(i.width for i in items) + 6 * (len(items) + 1)
        st = Image.new("RGBA", (w, 62), rgb(col) + (255,))
        x = 6
        for im in items:
            st.alpha_composite(im, (x, 58 - im.height if im.height > 12 else 30))
            x += im.width + 6
        strips.append((name, st))
    W = 120 + strips[0][1].width * 3 + 20
    RH = 62 * 2 + 10
    out = Image.new("RGB", (W, 40 + len(strips) * RH + 20), BG)
    g = ImageDraw.Draw(out)
    g.text((10, 8), "実寸（左）と 2 倍（右）：主人公・獣・呪い手・澱だまり・番兵・澱の玉。地面はガイド 2.5 の 2 番の色", fill=INK, font=font(16))
    for i, (name, st) in enumerate(strips):
        y = 40 + i * RH
        g.text((10, y + 52), name, fill=INK, font=font(16))
        out.paste(st, (120, y + 62))
        out.paste(up(st, 2), (120 + st.width + 10, y))
    out.save(os.path.join(DOC, "compare_1x.png"))


def arenas():
    h = hero()
    tiles = []
    for kind, cols in ARENA.items():
        b = load(f"enemy.{kind}.idle.0")
        b2 = load(f"enemy.{kind}.idle2.0")
        for col in cols:
            t = Image.new("RGBA", (h.width + b.width * 2 + 24, max(b.height, h.height) + 8), rgb(col) + (255,))
            t.alpha_composite(h, (4, t.height - 4 - h.height))
            t.alpha_composite(b, (h.width + 10, t.height - 4 - b.height))
            t.alpha_composite(b2, (h.width + b.width + 18, t.height - 4 - b2.height))
            tiles.append((kind, col, t))
    W = 1800
    y, x, rowh = 44, 10, 0
    placed = []
    for kind, col, t in tiles:
        for k in (1, 2):
            im = up(t, k)
            if x + im.width > W - 10:
                x, y, rowh = 10, y + rowh + 30, 0
            placed.append((im, x, y, f"{JA[kind]} {col} {k}倍"))
            x += im.width + 12
            rowh = max(rowh, im.height)
    out = Image.new("RGB", (W, y + rowh + 40), BG)
    g = ImageDraw.Draw(out)
    g.text((10, 8), "ボス：闘技場の地面の上で主人公と並べる（主人公・第 1 段階の待機・第 2 段階の待機）。実寸と 2 倍", fill=INK, font=font(18))
    for im, px_, py_, label in placed:
        out.paste(im, (px_, py_))
        g.text((px_, py_ + im.height + 4), label, fill=SUB, font=font(12))
    out.save(os.path.join(DOC, "arenas.png"))


def minimal(man):
    names = list(man["minimal"].keys())
    ims = [(n, load(n)) for n in names]
    k = 2
    W = sum((im.width + 4) * k + 12 for _, im in ims) + 20
    out = Image.new("RGB", (W, 128 * k + 80), BG)
    g = ImageDraw.Draw(out)
    g.text((10, 8), "最小構成（今のコードの名前のまま差し替えられる 12 枚）2 倍：.0＝止まる、.1＝動く（.0 と交互）", fill=INK, font=font(16))
    x = 10
    for n, im in ims:
        kind = n.split(".")[1]
        t = up(on(im, HOME[kind]), k)
        out.paste(t, (x, 40 + 128 * k - t.height))
        g.text((x, 48 + 128 * k), n.replace("enemy.", ""), fill=SUB, font=font(11))
        x += t.width + 12
    out.save(os.path.join(DOC, "minimal.png"))


def silhouettes():
    kinds = ["beast", "archer", "slime", "sentinel", "boss_root", "boss_frost", "boss_sand", "boss_storm", "boss_source"]
    ims = [hero()] + [load(f"enemy.{k}.idle.0") for k in kinds]
    W = sum(i.width + 8 for i in ims) + 8
    st = Image.new("RGBA", (W, 136), (0xe8, 0xe4, 0xdc, 255))
    x = 8
    for im in ims:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s.paste((16, 14, 20, 255), mask=im.split()[3])
        st.alpha_composite(s, (x, 132 - im.height))
        x += im.width + 8
    up(st, 2).save(os.path.join(DOC, "silhouettes.png"))


def main():
    with open(os.path.join(DOC, "frames.json"), encoding="utf-8") as fp:
        man = json.load(fp)
    for kind, info in man["kinds"].items():
        sheet(kind, info)
        gifs(kind, info)
    compare(man)
    arenas()
    minimal(man)
    silhouettes()
    print("wrote docs/art-release/enemy previews")


if __name__ == "__main__":
    main()
