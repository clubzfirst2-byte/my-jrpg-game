import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { decodePng } from '../../tools/release-art-pack.mjs';
import { glassKind, v3HouseWindows, v3HouseFile, V3_WINDOW_SCALE } from '../../src/view/assets/houseWindowsV3.js';

// Graphics v3: the night windows of the v3 houses (VILLAGE.md 2). The table must be the glass of the
// pictures as they are (houseWindows' rule, glassKind), inside the windows the art side measured
// (village_windows.json), and nothing that is not glass may light.

const SPEC = JSON.parse(readFileSync(new URL('../../docs/art-release-v3/village_windows.json', import.meta.url), 'utf8')).houses;
const art = (key) => decodePng(readFileSync(new URL(`../../src/art-release-v3/objects/${key}.png`, import.meta.url)));

describe('v3 house windows', () => {
  for (const key of Object.keys(SPEC)) {
    it(`${key}: every window's glass is the picture's, the size and rectangles are the art side's`, () => {
      const t = v3HouseWindows(key);
      const img = art(key);
      const spec = SPEC[key];
      expect(t.size).toEqual(spec.game_size);
      expect([img.width, img.height]).toEqual([t.size[0] * V3_WINDOW_SCALE, t.size[1] * V3_WINDOW_SCALE]);
      t.windows.forEach((w, n) => {
        const s = spec.windows[n];
        expect([w.x, w.y, w.w, w.h]).toEqual(s.game);
        // the rectangle in texels, from the feet (bottom centre)
        const x0 = (w.x + t.size[0] / 2) * V3_WINDOW_SCALE;
        const y0 = (w.y + t.size[1]) * V3_WINDOW_SCALE;
        expect([x0, y0, w.w * V3_WINDOW_SCALE, w.h * V3_WINDOW_SCALE]).toEqual(s.art);
        let lit = 0;
        w.glass.forEach((row, y) => {
          expect(row.length).toBe(s.art[2]);
          for (let x = 0; x < row.length; x++) {
            const i = ((y0 + y) * img.width + x0 + x) * 4;
            const k = glassKind(img.data[i], img.data[i + 1], img.data[i + 2], img.data[i + 3]);
            expect('.gd'[k], `${key} window ${n} texel ${x},${y}`).toBe(row[x]);
            if (k) lit++;
          }
        });
        expect(lit).toBe(s.lit);
        expect(s.lit_not_glass).toBe(0);
      });
    });
  }
  it('the v1 window rectangles (gfx/fx-v2 houseWindows: game y -34 .. -28 on a 48×56 house) hold no glass on the v3 house: the v3 table is needed', () => {
    const img = art('obj.house');
    let glass = 0;
    for (const wx of [-18, 11]) {
      for (let y = (-34 + 56) * 4; y < (-28 + 56) * 4; y++) {
        for (let x = (wx + 24) * 4; x < (wx + 7 + 24) * 4; x++) {
          const i = (y * img.width + x) * 4;
          if (glassKind(img.data[i], img.data[i + 1], img.data[i + 2], img.data[i + 3])) glass++;
        }
      }
    }
    expect(glass).toBe(0);
    expect(v3HouseWindows('obj.house').windows[0].y).toBe(-25.5);
  });
  it('the picture a season draws: autumn / winter their own file, spring and summer the summer one', () => {
    expect(v3HouseFile('obj.house', 'winter')).toBe('winter.obj.house');
    expect(v3HouseFile('obj.v3.house_stone', 'autumn')).toBe('autumn.obj.v3.house_stone');
    expect(v3HouseFile('obj.house', 'spring')).toBe('obj.house');
    expect(v3HouseWindows('obj.chest.closed')).toBe(null);
  });
});
