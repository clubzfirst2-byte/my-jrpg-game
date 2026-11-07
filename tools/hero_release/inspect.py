"""Enlarges a 32x56 frame with a coordinate grid, to place pixel edits by hand.
Run: python3 tools/hero_release/inspect.py <png> <out.png> [y0 y1]"""
import sys
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
y0, y1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 56)
im = Image.open(src).convert("RGBA")
S = 18
W, H = im.width, y1 - y0
canvas = Image.new("RGB", (W * S + 30, H * S + 20), (40, 40, 48))
bg = Image.new("RGBA", im.size, (79, 138, 62, 255)); bg.alpha_composite(im)
canvas.paste(bg.crop((0, y0, W, y1)).resize((W * S, H * S), Image.NEAREST), (30, 20))
g = ImageDraw.Draw(canvas)
f = ImageFont.load_default()
for x in range(W + 1):
    g.line([(30 + x * S, 20), (30 + x * S, 20 + H * S)], fill=(0, 0, 0) if x % 4 else (255, 255, 255), width=1)
    if x < W and x % 2 == 0: g.text((30 + x * S + 4, 4), str(x), fill=(220, 220, 220), font=f)
for y in range(H + 1):
    g.line([(30, 20 + y * S), (30 + W * S, 20 + y * S)], fill=(0, 0, 0) if (y + y0) % 4 else (255, 255, 255), width=1)
    if y < H: g.text((4, 20 + y * S + 4), str(y + y0), fill=(220, 220, 220), font=f)
canvas.save(out)
