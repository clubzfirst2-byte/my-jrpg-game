"""Mockups for review: the v2 UI laid over the baseline iPhone 15 Pro screenshots (2556x1179, DPR 3).

Run: python3 tools/ui_v2/mockups.py <baseline/15pro dir> <out dir>
CSS px -> device px is x3; UI art is drawn at 1 art px = 1 CSS px (x3 here), the title at x6.
Japanese text stays a readable web font: drawn here with IPA P Gothic as a stand-in for the system font.
The old HUD buttons and hearts are first painted out with the same ground copied a whole number of world
tiles (40 device px each) aside, so the new art is not judged on top of the old.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import col, nine_slice  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
UI = os.path.join(ROOT, "src", "art-release-v2", "ui")
OBJ = os.path.join(ROOT, "src", "art-release", "objects")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
K = 3  # device px per CSS px
MAN = json.load(open(os.path.join(UI, "manifest.json")))["sprites"]


def art(name, d=UI):
    return Image.open(os.path.join(d, name + ".png")).convert("RGBA")


def up(im, k=K):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def nine(name, w, h):
    """A 9-slice at w x h CSS px, returned at device size."""
    return nine_slice(art(name), w, h, MAN[name]["slice"], K)


def text(im, xy, s, size, fill=(236, 240, 248), bold=False, anchor="la"):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, size * K)
    d.text((xy[0] * K, xy[1] * K), s, font=f, fill=fill, anchor=anchor,
           stroke_width=1 if bold else 0, stroke_fill=fill)


def outlined(im, xy, s, size, fill, anchor="la"):
    """HUD text with the game's dark outline."""
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, size * K)
    d.text((xy[0] * K, xy[1] * K), s, font=f, fill=fill, anchor=anchor, stroke_width=3, stroke_fill=(10, 12, 20))


def paste(im, sprite, x, y):
    """Paste at CSS coordinates (top-left)."""
    im.alpha_composite(sprite, (int(x * K), int(y * K)))


def title_screen(out, css_w=852, css_h=393, dpr=3):
    """The title at a phone's CSS size and DPR (15 Pro 852x393 x3, SE 667x375 x2): the 960x400 CSS
    background is centred and cropped, the logo and the buttons sit in the middle column."""
    global K
    keep, K = K, dpr
    W, H = css_w * dpr, css_h * dpr
    flat = Image.new("RGBA", (480, 200))
    for layer in ("sky", "far", "mid", "near"):
        flat.alpha_composite(art(f"title.bg.{layer}"))
    big = up(flat, 2 * dpr)
    im = big.crop(((big.width - W) // 2, (big.height - H) // 2, (big.width - W) // 2 + W, (big.height - H) // 2 + H))
    logo = up(art("title.logo"), 2 * dpr)
    im.alpha_composite(logo, ((W - logo.width) // 2, 34 * K))
    for i, label in enumerate(("はじめから", "つづきから")):
        bw, bh = 200, 44
        x, y = (css_w - bw) / 2, 196 + i * 54
        paste(im, nine("btn.text.idle" if i else "btn.text.selected", bw, bh), x, y)
        text(im, (css_w / 2, y + 22), label, 16, anchor="mm", bold=True)
    im.save(out)
    K = keep


HUD_BUTTONS = [  # (centre in device px measured on 03_beach, CSS diameter, ring variant, icon, paint-out shift)
    ((2385, 994), 78, "gold", "attack", -720), ((2155, 1045), 60, "std", "jump", -560),
    ((2385, 763), 58, "std", "dodge", -720), ((2183, 849), 52, "std", "bow", -560),
    ((1968, 981), 52, "std", "guard", -400), ((2003, 795), 48, "std", "dash", -400),
]


def apply_hud(im, shifts=None):
    """The new HUD over a baseline frame: paint the old buttons and hearts out (ground copied a whole
    number of tiles aside), then lay the rings, icons, hearts, pause and bag buttons."""
    clean = im.copy()
    for i, ((cx, cy), d, _, _, dx) in enumerate(HUD_BUTTONS):
        dx = shifts[i] if shifts else dx
        r = d * K / 2 + 8
        for y in range(int(cy - r), min(im.height, int(cy + r) + 1)):
            for x in range(int(cx - r), min(im.width, int(cx + r) + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    im.putpixel((x, y), clean.getpixel((x + dx, y)))
    for x0 in (212, 288, 365):  # the old hearts
        for y in range(36, 102):
            for x in range(x0 - 36, x0 + 36):
                im.putpixel((x, y), clean.getpixel((x + 480, y)))
    for (cx, cy), d, variant, ic, _ in HUD_BUTTONS:
        ring = up(art(f"btn.ring.{variant}.{d}.idle"))
        im.alpha_composite(ring, (cx - ring.width // 2, cy - ring.height // 2))
        s = 20 if d < 52 else 26 if d <= 69 else 34
        icon = up(art(f"icon.ui.{ic}.{s}"))
        im.alpha_composite(icon, (cx - icon.width // 2, cy - icon.height // 2))
    paste(im, nine("btn.text.idle", 44, 44), 8, 8)
    paste(im, up(art("icon.ui.pause.20")), 20, 20)
    paste(im, nine("btn.text.idle", 50, 44), 8, 58)
    paste(im, up(art("icon.ui.bag.20")), 23, 60)
    text(im, (33, 92), "持ち物", 12, anchor="mm", bold=True)
    for i, q in enumerate((4, 4, 3)):
        paste(im, up(art(f"heart.{q}")), 60 + i * 25, 12)
    return im


def hud(base, out, src="03_beach.png"):
    im = Image.open(os.path.join(base, src)).convert("RGBA")
    apply_hud(im).save(out)

def dialogue(base, out):
    im = apply_hud(Image.open(os.path.join(base, "04_village_day.png")).convert("RGBA"), [-760] * 6)
    x, w, h = 12, 852 - 24, 104
    y = 393 - 10 - h
    paste(im, nine("panel.dialogue", w, h), x, y)
    paste(im, nine("panel.nameplate", 64, 24), x + 12, y - 14)
    text(im, (x + 44, y - 2), "長老", 13, fill=(255, 215, 94), anchor="mm", bold=True)
    text(im, (x + 18, y + 20), "よく来たな、旅の者よ。この島には、星環と呼ばれる古い輪がある。", 15)
    text(im, (x + 18, y + 44), "星のかけらを集めれば、輪はふたたび光を取り戻すだろう。", 15)
    paste(im, up(art("cue.more.1")), x + w - 26, y + h - 18)
    im.save(out)


def menu_frame(im, kind):
    # the old panel stood here: in the game it is gone, so cover it before laying the new (94 % fill) one
    ImageDraw.Draw(im).rectangle([8 * K, 8 * K, (852 - 8) * K, (393 - 8) * K], fill=col("navy", 0))
    paste(im, nine(kind, 852 - 16, 393 - 16), 8, 8)


def tabs(im, labels, active, x0=18, y=18):
    x = x0
    for i, lab in enumerate(labels):
        w = max(44, 20 + 16 * len(lab))
        paste(im, nine("tab.active" if i == active else "tab.idle", w, 40), x, y)
        text(im, (x + w / 2, y + 20), lab, 14, anchor="mm", bold=i == active,
             fill=(255, 244, 200) if i == active else (200, 214, 236))
        x += w + 6
    return x


def rows(im, items, y0=68, selected=0):
    for i, (icon, name, detail) in enumerate(items):
        y = y0 + i * 50
        paste(im, nine("row.selected" if i == selected else "row.idle", 852 - 36, 46), 18, y)
        if i == selected:
            paste(im, up(art("cue.more.0").rotate(90, expand=True)), 26, y + 18)
        paste(im, up(art(icon, OBJ)), 40, y + 13)
        text(im, (70, y + 23), name, 14, anchor="lm", bold=True)
        nx = 70 + 15 * len(name) + 12
        text(im, (nx, y + 23), detail, 12, fill=(176, 190, 214), anchor="lm")


def close_button(im):
    paste(im, nine("btn.text.idle", 76, 40), 852 - 18 - 76, 18)
    paste(im, up(art("icon.ui.close.20")), 852 - 18 - 76 + 8, 28)
    text(im, (852 - 18 - 30, 38), "閉じる", 13, anchor="mm", bold=True)


def inventory(base, out):
    im = Image.open(os.path.join(base, "22_menu_inventory.png")).convert("RGBA")
    menu_frame(im, "panel.menu")
    tabs(im, ["武器", "弓", "防具", "素材", "料理", "能力", "クエスト"], 0)
    close_button(im)
    outlined(im, (852 - 106, 38), "★ 0 星貨", 15, (255, 215, 94), anchor="rm")
    rows(im, [("icon.sword", "◆ 木の剣", "耐久 25/25　軽くて振りやすいが、すぐに傷む。"),
              ("icon.sword", "旅人の剣", "耐久 35/35　よく手入れされた片手剣。"),
              ("icon.spear", "見張りの槍", "耐久 30/30　長い。離れた敵に届く。")])
    im.save(out)


def shop(base, out):
    im = Image.open(os.path.join(base, "23_menu_shop.png")).convert("RGBA")
    menu_frame(im, "panel.shop")
    outlined(im, (24, 38), "風見の雑貨屋", 15, (255, 210, 138), anchor="lm")
    tabs(im, ["買う", "売る"], 0, x0=130)
    close_button(im)
    outlined(im, (852 - 106, 38), "★ 300 星貨", 15, (255, 215, 94), anchor="rm")
    rows(im, [("icon.arrows", "矢", "3 星貨　弓で撃つ。"), ("icon.mushroom", "森きのこ", "6 星貨　森の木陰に生える。"),
              ("icon.berry", "赤い実", "5 星貨　甘酸っぱい木の実。"),
              ("icon.dish.grilled_meat", "焼き肉", "20 星貨　香ばしい。"),
              ("icon.sword", "旅人の剣", "80 星貨　よく手入れされた片手剣。"),
              ("icon.armor", "樹皮の胴当て", "70 星貨　厚い樹皮を重ねた胴当て。")], selected=3)
    paste(im, up(art("cue.more.0")), 421, 372)
    im.save(out)


def pause(base, out):
    im = apply_hud(Image.open(os.path.join(base, "07_plains.png")).convert("RGBA"), [-1200] * 6)
    dim = Image.new("RGBA", im.size, col("navy", 0, 150))
    im.alpha_composite(dim)
    w, h = 340, 230
    x, y = (852 - w) / 2, (393 - h) / 2 + 8
    paste(im, nine("panel.menu", w, h), x, y)
    cr = up(art("panel.crest"))
    im.alpha_composite(cr, (int((x + w / 2) * K - cr.width / 2), int((y - 8) * K)))
    text(im, (426, y + 34), "一時停止中", 22, anchor="mm", bold=True)
    text(im, (426, y + 56), "v1.0.0", 11, fill=(150, 170, 200), anchor="mm")
    for i, lab in enumerate(("タップで再開", "設定", "タイトルへ")):
        bw = 200
        by = y + 74 + i * 50
        paste(im, nine("btn.text.selected" if i == 0 else "btn.text.idle", bw, 44), (852 - bw) / 2, by)
        text(im, (426, by + 22), lab, 16 if i == 0 else 15, anchor="mm", bold=True)
    im.save(out)


def main():
    base, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    title_screen(os.path.join(out, "mock_title.png"))
    title_screen(os.path.join(out, "mock_title_se.png"), 667, 375, 2)
    hud(base, os.path.join(out, "mock_hud.png"))
    dialogue(base, os.path.join(out, "mock_dialogue.png"))
    inventory(base, os.path.join(out, "mock_inventory.png"))
    shop(base, os.path.join(out, "mock_shop.png"))
    pause(base, os.path.join(out, "mock_pause.png"))
    print("wrote 7 mockups to", out)


if __name__ == "__main__":
    main()
