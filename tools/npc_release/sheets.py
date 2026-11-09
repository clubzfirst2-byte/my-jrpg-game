"""Review images for NPC batch 1 (docs/npc/release/batch1/), from the PNGs in src/art-release/npc/:
  01_directions.png      the three villagers (and the hero) in all four directions
  02_frames_<id>.png     every frame of one villager (idle 4 + walk 6, four directions)
  03_hero_compare.png    beside the hero: at game size (16x28) and enlarged, with height lines
  04_palette.png         each villager's colour ramps next to the hero's
  anim_<id>_<action>.gif the loops, four directions side by side (6x)
  NPCギャラリー.html       one self-contained page (no server needed): directions, loops, all frames,
                         the hero comparison and the game screenshots
Run: python3 tools/npc_release/sheets.py
"""
import base64
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import gen_npc  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NPC_DIR = os.path.join(ROOT, "src", "art-release", "npc")
HERO_DIR = os.path.join(ROOT, "src", "art-release", "hero")
OUT = os.path.join(ROOT, "docs", "npc", "release", "batch1")
DIRS = ("down", "up", "right", "left")
IDS = ("elder", "merchant", "guard")
NAMES = {"elder": "長老", "merchant": "雑貨屋", "guard": "見張り", "hero": "主人公"}
FRAMES = {"idle": 4, "walk": 6}
GRASS = (79, 138, 62, 255)
FONT_PATHS = ["/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
              "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"]


def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def npc(id_, action, d, i):
    return Image.open(os.path.join(NPC_DIR, f"npc.{id_}.{action}.{d}.{i}.png")).convert("RGBA")


def hero(action, d, i):
    return Image.open(os.path.join(HERO_DIR, f"hero.{action}.{d}.{i}.png")).convert("RGBA")


def big(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def labelled_grid(cells, cols, cell_w, cell_h, k, labels_top=None, labels_left=None, bg=GRASS, pad=8, top=40, left=0):
    """cells: list of rows of images (unscaled)."""
    f = font(18)
    W = left + cols * (cell_w * k + pad) + pad
    Hh = top + len(cells) * (cell_h * k + pad) + pad
    canvas = Image.new("RGBA", (W, Hh), (34, 38, 46, 255))
    g = ImageDraw.Draw(canvas)
    for r, row in enumerate(cells):
        for c, im in enumerate(row):
            if im is None:
                continue
            x = left + pad + c * (cell_w * k + pad)
            y = top + pad + r * (cell_h * k + pad)
            tile = Image.new("RGBA", (cell_w * k, cell_h * k), bg)
            b = big(im, k)
            tile.alpha_composite(b, ((cell_w * k - b.width) // 2, cell_h * k - b.height))
            canvas.alpha_composite(tile, (x, y))
        if labels_left:
            g.text((8, top + pad + r * (cell_h * k + pad) + cell_h * k // 2 - 10), labels_left[r], fill=(230, 230, 230), font=f)
    if labels_top:
        for c, t in enumerate(labels_top):
            g.text((left + pad + c * (cell_w * k + pad) + 4, 10), t, fill=(230, 230, 230), font=f)
    return canvas


def directions():
    rows = [[npc(i, "idle", d, 0) for d in DIRS] for i in IDS] + [[hero("idle", d, 0) for d in DIRS]]
    return labelled_grid(rows, 4, 32, 56, 5, labels_top=["正面 down", "背面 up", "右 right", "左 left"],
                         labels_left=[NAMES[i] for i in IDS] + ["主人公"], left=90)


def frames_sheet(id_):
    rows, labels = [], []
    for action, n in FRAMES.items():
        for d in DIRS:
            rows.append([npc(id_, action, d, i) for i in range(n)])
            labels.append(f"{action} {d}")
    return labelled_grid(rows, 6, 32, 56, 4, labels_top=[str(i) for i in range(6)], labels_left=labels, left=110)


def hero_compare():
    f = font(18)
    figs = [("hero", hero("idle", "down", 0))] + [(i, npc(i, "idle", "down", 0)) for i in IDS]
    figs_side = [("hero", hero("idle", "right", 0))] + [(i, npc(i, "idle", "right", 0)) for i in IDS]
    k = 6
    W = 40 + len(figs) * (32 * k + 30) + 40 + len(figs) * (16 * 2 + 10) + 40
    Hh = 56 * k * 2 + 140
    c = Image.new("RGBA", (W, Hh), (34, 38, 46, 255))
    g = ImageDraw.Draw(c)
    for row, items in enumerate((figs, figs_side)):
        y0 = 50 + row * (56 * k + 40)
        ground = y0 + 56 * k
        tile = Image.new("RGBA", (len(items) * (32 * k + 30) + 10, 56 * k), GRASS)
        c.alpha_composite(tile, (30, y0))
        for n, (id_, im) in enumerate(items):
            x = 40 + n * (32 * k + 30)
            c.alpha_composite(big(im, k), (x, y0))
            g.text((x + 4, y0 - 30 if row == 0 else ground + 4), NAMES[id_], fill=(240, 240, 240), font=f)
        for yy in (0, 4, 8):  # height lines (art rows)
            g.line([(30, y0 + yy * k), (30 + tile.width, y0 + yy * k)], fill=(255, 255, 255, 90), width=1)
    # actual game size (16x28 game px = the PNG halved), twice enlarged so it can be seen
    x0 = 40 + len(figs) * (32 * k + 30) + 10
    g.text((x0, 20), "ゲーム内の大きさ（16×28・2倍表示）", fill=(240, 240, 240), font=font(16))
    tile = Image.new("RGBA", (len(figs) * 44 + 20, 56 * 2 + 20), GRASS)
    c.alpha_composite(tile, (x0, 50))
    for n, (id_, im) in enumerate(figs):
        small = im.resize((16, 28), Image.NEAREST).resize((32, 56), Image.NEAREST)
        c.alpha_composite(small, (x0 + 10 + n * 44, 60))
    return c


def palette():
    f = font(16)
    sets = []
    hero_ramps = {"cloak": ["#10180e", "#3e6234", "#6a9048", "#8eb062", "#b8d48a"], "shirt": ["#4a4640", "#a8a296", "#e4e0d6", "#f6f4ee", "#ffffff"],
                  "hair": ["#2a160c", "#4e2e1a", "#7a4a2a", "#a8703f", "#d09a62"], "skin": ["#6e3e2c", "#c8906a", "#f2c49b", "#ffdcbc", "#fff0e0"]}
    sets.append(("主人公", hero_ramps))
    for n in gen_npc.NPCS:
        sets.append((NAMES[n.id], n.ramps))
    sw = 26
    W = 140 + 6 * (5 * sw + 90)
    Hh = 30 + len(sets) * (sw + 34)
    c = Image.new("RGBA", (W, Hh), (34, 38, 46, 255))
    g = ImageDraw.Draw(c)
    for r, (name, ramps) in enumerate(sets):
        y = 20 + r * (sw + 34)
        g.text((10, y + 4), name, fill=(240, 240, 240), font=f)
        for k, (m, ramp) in enumerate(ramps.items()):
            x = 140 + k * (5 * sw + 90)
            g.text((x, y - 16), m, fill=(200, 200, 200), font=font(13))
            for t, col in enumerate(ramp):
                g.rectangle([x + t * sw, y, x + t * sw + sw - 2, y + sw], fill=col)
    return c


def gif(id_, action, path, k=5):
    n = FRAMES[action]
    fps = 3 if action == "idle" else 8
    frames = []
    for i in range(n):
        canvas = Image.new("RGBA", (4 * (32 * k + 10) + 10, 56 * k + 20), GRASS)
        for j, d in enumerate(DIRS):
            canvas.alpha_composite(big(npc(id_, action, d, i), k), (10 + j * (32 * k + 10), 10))
        frames.append(canvas.convert("RGB"))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)


def data_uri(path_or_img):
    if isinstance(path_or_img, Image.Image):
        b = io.BytesIO()
        path_or_img.save(b, "PNG")
        raw = b.getvalue()
    else:
        raw = open(path_or_img, "rb").read()
    return "data:image/png;base64," + base64.b64encode(raw).decode()


def gallery(shots):
    sprites = {}
    for i in IDS:
        for a, n in FRAMES.items():
            for d in DIRS:
                for k in range(n):
                    sprites[f"{i}.{a}.{d}.{k}"] = data_uri(os.path.join(NPC_DIR, f"npc.{i}.{a}.{d}.{k}.png"))
    for d in DIRS:
        for k in range(4):
            sprites[f"hero.idle.{d}.{k}"] = data_uri(os.path.join(HERO_DIR, f"hero.idle.{d}.{k}.png"))
        for k in range(6):
            sprites[f"hero.walk.{d}.{k}"] = data_uri(os.path.join(HERO_DIR, f"hero.walk.{d}.{k}.png"))
    import json
    shots_html = "".join(f'<figure><img src="{data_uri(p)}" alt="{t}"><figcaption>{t}</figcaption></figure>' for t, p in shots if os.path.exists(p))
    return GALLERY.replace("__SPRITES__", json.dumps(sprites)).replace("__SHOTS__", shots_html)


GALLERY = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NPC製品版 第1回 ギャラリー</title>
<style>
:root{--bg:#1d2129;--panel:#272c36;--text:#eceff4;--sub:#a9b1bf;--grass:#4f8a3e}
body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif}
header{padding:16px}h1{font-size:20px;margin:0 0 4px}p{color:var(--sub);margin:4px 0;font-size:14px}
section{background:var(--panel);margin:12px 16px;padding:12px;border-radius:10px}h2{font-size:16px;margin:0 0 10px}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end}.cell{text-align:center;font-size:12px;color:var(--sub)}
canvas{background:var(--grass);image-rendering:pixelated;border-radius:6px;display:block}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}button{background:#3a4252;color:var(--text);border:0;border-radius:8px;padding:8px 12px;font-size:14px}
button.on{background:#5b7bd5}figure{margin:0}figure img{max-width:100%;border-radius:6px}figcaption{font-size:12px;color:var(--sub)}
.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}
</style></head><body>
<header><h1>NPC製品版 第1回：長老・雑貨屋・見張り</h1>
<p>32×56（ゲーム内 16×28）・待機4コマ＋歩行6コマ×4方向＝1人40枚。主人公の正式版と同じ描き方。</p>
<p>この画面はゲームとは別のファイルです（ゲームの動作には影響しません）。</p></header>
<section><h2>4方向（アニメーション）</h2>
<div class="controls"><button data-act="idle" class="on">待機</button><button data-act="walk">歩行</button>
<button data-k="3">3倍</button><button data-k="5" class="on">5倍</button><button data-bg="#4f8a3e" class="on">草</button><button data-bg="#8a6a46">土</button><button data-bg="#20242c">暗</button></div>
<div id="dirs"></div></section>
<section><h2>主人公との大きさ比較</h2><div class="row" id="compare"></div></section>
<section><h2>全コマ一覧</h2><div id="all"></div></section>
<section><h2>ゲーム画面</h2><div class="shots">__SHOTS__</div></section>
<script>
const S=__SPRITES__;const IDS=['elder','merchant','guard'];const NAMES={elder:'長老',merchant:'雑貨屋',guard:'見張り',hero:'主人公'};
const DIRS=['down','up','right','left'];const DN={down:'正面',up:'背面',right:'右',left:'左'};const N={idle:4,walk:6};const FPS={idle:3,walk:8};
const imgs={};for(const k in S){const i=new Image();i.src=S[k];imgs[k]=i;}
let act='idle',K=5,bg='#4f8a3e';const live=[];
function cv(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;c.style.background=bg;return c}
function draw(c,key,k){const g=c.getContext('2d');g.imageSmoothingEnabled=false;g.clearRect(0,0,c.width,c.height);const im=imgs[key];if(im&&im.complete)g.drawImage(im,(c.width-32*k)/2,c.height-56*k,32*k,56*k)}
function build(){live.length=0;const d=document.getElementById('dirs');d.innerHTML='';
for(const id of IDS){const row=document.createElement('div');row.className='row';row.style.marginBottom='10px';
for(const dir of DIRS){const cell=document.createElement('div');cell.className='cell';const c=cv(32*K+8,56*K+4);cell.append(c);cell.append(NAMES[id]+'・'+DN[dir]);row.append(cell);live.push({c,id,dir})}d.append(row)}
const cmp=document.getElementById('compare');cmp.innerHTML='';
for(const id of ['hero',...IDS]){const cell=document.createElement('div');cell.className='cell';const c=cv(32*K+8,56*K+4);cell.append(c);cell.append(NAMES[id]);cmp.append(cell);live.push({c,id,dir:'down',hero:id==='hero'})}
const all=document.getElementById('all');all.innerHTML='';
for(const id of IDS)for(const a of ['idle','walk'])for(const dir of DIRS){const row=document.createElement('div');row.className='row';row.style.marginBottom='6px';
const lab=document.createElement('div');lab.className='cell';lab.style.width='110px';lab.textContent=NAMES[id]+' '+a+' '+DN[dir];row.append(lab);
for(let i=0;i<N[a];i++){const c=cv(32*3,56*3);c.style.background=bg;row.append(c);setTimeout(()=>draw(c,id+'.'+a+'.'+dir+'.'+i,3),50)}all.append(row)}}
function tick(t){for(const l of live){const n=N[act];const f=Math.floor(t/1000*FPS[act])%n;draw(l.c,(l.hero?'hero':l.id)+'.'+act+'.'+l.dir+'.'+f,K)}requestAnimationFrame(tick)}
document.querySelectorAll('button').forEach(b=>b.onclick=()=>{if(b.dataset.act){act=b.dataset.act}if(b.dataset.k){K=+b.dataset.k}if(b.dataset.bg){bg=b.dataset.bg}
document.querySelectorAll('button').forEach(x=>{if((x.dataset.act&&x.dataset.act===act)||(x.dataset.k&&+x.dataset.k===K)||(x.dataset.bg&&x.dataset.bg===bg))x.classList.add('on');else x.classList.remove('on')});build()});
window.addEventListener('load',()=>{build();requestAnimationFrame(tick)});
</script></body></html>
"""


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    directions().save(os.path.join(OUT, "01_directions.png"))
    for i in IDS:
        frames_sheet(i).save(os.path.join(OUT, f"02_frames_{i}.png"))
        for a in FRAMES:
            gif(i, a, os.path.join(OUT, f"anim_{i}_{a}.gif"))
    hero_compare().save(os.path.join(OUT, "03_hero_compare.png"))
    palette().save(os.path.join(OUT, "04_palette.png"))
    shots = [("村：長老・見張りと主人公（iPhone 横画面）", os.path.join(OUT, "05_ingame_village.png")),
             ("長老に話しかける（主人公の方を向く）", os.path.join(OUT, "06_ingame_talk_elder.png")),
             ("見張りに話しかける", os.path.join(OUT, "07_ingame_talk_guard.png")),
             ("お店：カウンターの奥の雑貨屋", os.path.join(OUT, "08_ingame_shop.png")),
             ("変更前：仮素材の NPC（?npc=placeholder）", os.path.join(OUT, "09_ingame_before.png"))]
    with open(os.path.join(OUT, "NPCギャラリー.html"), "w") as fh:
        fh.write(gallery(shots))
    print("sheets ->", os.path.relpath(OUT, ROOT))
