"""v2 UI art (W4) -> src/art-release-v2/ui/*.png + manifest.json (sizes, density, 9-slice insets).

Run: python3 tools/ui_v2/gen_ui.py        (deterministic)
     python3 tools/ui_v2/mockups.py <out>  (composites over the baseline screenshots, for review)
Stops if a rule breaks: buttons below 44 px, an icon that does not fit its button, an empty sprite, a
9-slice whose insets leave no stretchable middle.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buttons  # noqa: E402
import panels  # noqa: E402
import title  # noqa: E402
from common import save  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "src", "art-release-v2", "ui")

# which ring and icon each HUD button uses, per --btn size (small 0.85 / medium 1 / large 1.15)
HUD = {
    "attack-button": ("gold", "attack", (66, 78, 90)),
    "jump-button": ("std", "jump", (51, 60, 69)),
    "dodge-button": ("std", "dodge", (49, 58, 67)),
    "bow-button": ("std", "bow", (44, 52, 60)),
    "guard-button": ("std", "guard", (44, 52, 60)),
    "dash-button": ("std", "dash", (44, 48, 55)),
    "ability-button": ("teal", "ability", (44, 52, 60)),
    "ability-next": ("std", "swap", (44, 44, 44)),
}


def icon_size_for(d):
    return 20 if d < 52 else 26 if d <= 69 else 34


def build():
    sprites, meta = {}, {}

    def add(name, im, **m):
        assert im.getbbox() is not None, f"{name}: empty"
        sprites[name] = im
        meta[name] = {"w": im.width, "h": im.height, **m}

    # title (2 CSS px per art px)
    add("title.logo", title.logo(), cssScale=2)
    for layer, f, par in (("sky", title.sky, 0.0), ("far", title.far, 0.15), ("mid", title.mid, 0.4), ("near", title.near, 1.0)):
        add(f"title.bg.{layer}", f(), cssScale=2, parallax=par)
    flat = title.sky()
    for f in (title.far, title.mid, title.near):
        flat.alpha_composite(f())
    add("title.bg", flat, cssScale=2)
    # HUD rings and icons (1 CSS px per art px)
    for variant, sizes in buttons.RING_SIZES.items():
        for d in sizes:
            assert d >= 44, f"ring {d} is below the 44 px tap target"
            for state in ("idle", "pressed"):
                add(f"btn.ring.{variant}.{d}.{state}", buttons.ring(d, variant, state == "pressed"), cssScale=1)
    for n in buttons.ICONS:
        for s in buttons.ICON_SIZES:
            add(f"icon.ui.{n}.{s}", buttons.icon(n, s), cssScale=1)
    for bid, (variant, ic, sizes) in HUD.items():
        for d in sizes:
            assert f"btn.ring.{variant}.{d}.idle" in sprites, (bid, d)
            s = icon_size_for(d)
            inner = d - 2 * 4.5
            assert s * 1.414 <= inner + 6, f"{bid}: icon {s} does not fit the ring {d}"
    # panels (9-slice, 1 CSS px per art px)
    for name, f in (("panel.menu", panels.panel_menu), ("panel.dialogue", panels.panel_dialogue),
                    ("panel.shop", panels.panel_shop), ("panel.ending", panels.panel_ending),
                    ("panel.toast", panels.toast), ("panel.nameplate", panels.nameplate)):
        im, inset = f()
        add(name, im, cssScale=1, slice=inset)
    add("panel.crest", panels.crest(), cssScale=1)
    for st in ("idle", "active", "pressed"):
        im, inset = panels.tab(st)
        add(f"tab.{st}", im, cssScale=1, slice=inset)
    for st in ("idle", "selected", "pressed"):
        im, inset = panels.row(st)
        add(f"row.{st}", im, cssScale=1, slice=inset)
    for st in ("idle", "pressed", "selected", "disabled"):
        im, inset = panels.text_button(st)
        add(f"btn.text.{st}", im, cssScale=1, slice=inset)
    for i in (0, 1):
        add(f"cue.more.{i}", panels.cue(i), cssScale=1)
    for q in range(5):
        add(f"heart.{q}", panels.heart(q), cssScale=1)
    im, inset = panels.bossbar_frame()
    add("bossbar.frame", im, cssScale=1, slice=list(inset))
    for p in (1, 2):
        add(f"bossbar.fill.{p}", panels.bossbar_fill(p), cssScale=1, repeat="x")
    for n, m in meta.items():
        if "slice" in m:
            sl = m["slice"] if isinstance(m["slice"], list) else [m["slice"]] * 4
            m["slice"] = sl
            assert sl[0] + sl[2] < m["w"] and sl[1] + sl[3] < m["h"], f"{n}: no middle left"
    return sprites, meta


def main():
    sprites, meta = build()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".png"):
            os.remove(os.path.join(OUT, f))
    for name, im in sorted(sprites.items()):
        save(im, os.path.join(OUT, name + ".png"))
    manifest = {"density": {"default": "1 art px = 1 CSS px", "title": "1 art px = 2 CSS px"},
                "hud": {k: {"ring": v[0], "icon": v[1], "sizes": {"small": v[2][0], "medium": v[2][1], "large": v[2][2]},
                            "iconSize": {"small": icon_size_for(v[2][0]), "medium": icon_size_for(v[2][1]),
                                         "large": icon_size_for(v[2][2])}} for k, v in HUD.items()},
                "sprites": dict(sorted(meta.items()))}
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.write("\n")
    write_names(manifest)
    print(f"wrote {len(sprites)} sprites + manifest.json to {os.path.relpath(OUT, ROOT)}")


def write_names(manifest):
    """docs/art-release-v2/ui/NAMES.md: every file with its exact size, CSS size and 9-slice insets."""
    S = manifest["sprites"]
    lines = ["# v2 UI art: names, sizes, 9-slice insets", "",
             "Generated by `tools/ui_v2/gen_ui.py` from `src/art-release-v2/ui/manifest.json` (do not edit by hand).",
             "Art px -> CSS px: x`cssScale` (title x2, everything else x1). Always `image-rendering: pixelated`.",
             "9-slice: `border-image: url(..) <t> <r> <b> <l> fill / <t*cssScale>px <r>px <b>px <l>px stretch;` "
             "(the edges are uniform along their length, so `stretch` never resamples a pattern).", ""]
    groups = [("Title", "title."), ("HUD rings", "btn.ring."), ("UI icons", "icon.ui."), ("Panels", "panel."),
              ("Tabs", "tab."), ("List rows", "row."), ("Text buttons", "btn.text."), ("Cues", "cue."),
              ("Hearts", "heart."), ("Boss bar", "bossbar.")]
    for title_, pre in groups:
        names = [n for n in S if n.startswith(pre)]
        lines += [f"## {title_} ({len(names)})", "", "| file | art px | CSS px | 9-slice (t r b l, art px) | notes |",
                  "|---|---|---|---|---|"]
        for n in names:
            m = S[n]
            k = m["cssScale"]
            sl = m.get("slice")
            sl_s = f"{sl[1]} {sl[2]} {sl[3]} {sl[0]}" if sl else ""
            note = []
            if "parallax" in m:
                note.append(f"parallax {m['parallax']}")
            if "repeat" in m:
                note.append(f"repeat-{m['repeat']}")
            lines.append(f"| `{n}.png` | {m['w']}×{m['h']} | {m['w'] * k}×{m['h'] * k} | {sl_s} | {', '.join(note)} |")
        lines.append("")
    lines += ["## HUD buttons: which ring and icon per `--btn` size", "",
              "| element | ring | small (0.85) | medium (1) | large (1.15) | icon (small / medium / large) |",
              "|---|---|---|---|---|---|"]
    for k, v in manifest["hud"].items():
        sz, ic = v["sizes"], v["iconSize"]
        lines.append(f"| `#{k}` | {v['ring']} | {sz['small']} | {sz['medium']} | {sz['large']} | "
                     f"`icon.ui.{v['icon']}.{ic['small']}` / `.{ic['medium']}` / `.{ic['large']}` |")
    path = os.path.join(ROOT, "docs", "art-release-v2", "ui", "NAMES.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
