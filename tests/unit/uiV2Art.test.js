import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';

// W4: the v2 UI art (src/art-release-v2/ui, tools/ui_v2). Not wired into the game yet: these tests pin
// the manifest the UI engineer builds on (names, sizes, densities, 9-slice insets) and the usability
// rules the art must keep (44 px tap targets, icons that fit their buttons).

const DIR = new URL('../../src/art-release-v2/ui/', import.meta.url);
const manifest = JSON.parse(readFileSync(new URL('manifest.json', DIR), 'utf8'));
const S = manifest.sprites;

const header = (name) => {
  const buf = readFileSync(new URL(`${name}.png`, DIR));
  expect(buf.toString('ascii', 1, 4), name).toBe('PNG');
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20), depth: buf[24], type: buf[25] };
};

describe('v2 UI art (src/art-release-v2/ui)', () => {
  it('holds exactly the sprites the manifest lists, each at its listed size, 8-bit RGBA', () => {
    const files = readdirSync(DIR).filter((f) => f.endsWith('.png')).sort();
    expect(files).toEqual(Object.keys(S).map((n) => `${n}.png`).sort());
    expect(files).toHaveLength(98);
    for (const [n, m] of Object.entries(S)) {
      const h = header(n);
      expect([h.w, h.h], n).toEqual([m.w, m.h]);
      expect([h.depth, h.type], n).toEqual([8, 6]);
    }
  });

  it('draws the title at 2 CSS px per art px and everything else at 1 (integer device px on DPR 2 and 3)', () => {
    for (const [n, m] of Object.entries(S)) expect(m.cssScale, n).toBe(n.startsWith('title.') ? 2 : 1);
    // the vista layers share one size and cover the 15 Pro (852x393 CSS) and SE (667x375) at x2
    for (const l of ['sky', 'far', 'mid', 'near']) {
      expect([S[`title.bg.${l}`].w, S[`title.bg.${l}`].h]).toEqual([480, 200]);
    }
    expect(S['title.bg.sky'].w * 2).toBeGreaterThanOrEqual(852 + 100);
    expect(S['title.bg.sky'].h * 2).toBeGreaterThanOrEqual(393);
  });

  it('keeps every HUD button at 44 px or more, with a ring and an icon at each button size', () => {
    for (const [id, b] of Object.entries(manifest.hud)) {
      for (const size of ['small', 'medium', 'large']) {
        const d = b.sizes[size];
        expect(d, `${id} ${size}`).toBeGreaterThanOrEqual(44);
        for (const st of ['idle', 'pressed']) expect(S[`btn.ring.${b.ring}.${d}.${st}`], `${id} ${d} ${st}`).toBeTruthy();
        const s = b.iconSize[size];
        expect(S[`icon.ui.${b.icon}.${s}`], `${id} icon ${s}`).toBeTruthy();
        // the icon's diagonal stays inside the glass (the rim is 4.5 px deep), give or take its outline
        expect(s * Math.SQRT2, `${id} ${size}`).toBeLessThanOrEqual(d - 9 + 6);
      }
    }
    // the medium sizes are the ones in src/styles.css today
    expect(manifest.hud['attack-button'].sizes.medium).toBe(78);
    expect(manifest.hud['ability-next'].sizes.medium).toBe(44);
  });

  it('gives every 9-slice insets that leave a middle to stretch', () => {
    const sliced = Object.entries(S).filter(([, m]) => m.slice);
    expect(sliced.length).toBe(17);
    for (const [n, m] of sliced) {
      const [l, t, r, b] = m.slice;
      expect(l + r, n).toBeLessThan(m.w);
      expect(t + b, n).toBeLessThan(m.h);
    }
    for (const n of ['panel.menu', 'panel.dialogue', 'panel.shop', 'panel.ending', 'panel.toast', 'tab.active', 'row.selected', 'btn.text.idle', 'bossbar.frame']) {
      expect(S[n]?.slice, n).toBeTruthy();
    }
  });

  it('has the five heart fills (quarters, like the HUD counts them) at the HUD size', () => {
    for (let q = 0; q <= 4; q++) expect([S[`heart.${q}`].w, S[`heart.${q}`].h]).toEqual([22, 20]);
  });
});
