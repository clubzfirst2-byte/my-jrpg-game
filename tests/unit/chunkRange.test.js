import { describe, it, expect } from 'vitest';
import { chunkRange, CHUNK_KEEP_MARGIN_TILES, CHUNK_LOAD_MARGIN_TILES } from '../../src/view/chunkRange.js';

// Which chunks the view builds and keeps (gameView.updateChunks): 32 × 32 tiles of 16 px.
const TS = 16;
const grid = { chunkPx: 32 * TS, ncx: 8, ncy: 10 };
// iPhone landscape at art density 2: about 426 × 196 game px on screen
const VIEW = { w: 426, h: 196 };
const count = (r) => (r.x1 - r.x0 + 1) * (r.y1 - r.y0 + 1);
const load = (o) => chunkRange(o, VIEW.w, VIEW.h, TS * CHUNK_LOAD_MARGIN_TILES, grid);
const keep = (o) => chunkRange(o, VIEW.w, VIEW.h, TS * CHUNK_KEEP_MARGIN_TILES, grid);
const inside = (r, cx, cy) => cx >= r.x0 && cx <= r.x1 && cy >= r.y0 && cy <= r.y1;

describe('chunk load / keep ranges', () => {
  it('builds 4 tiles beyond the screen and frees 12 beyond it (8 tiles of hysteresis)', () => {
    expect(CHUNK_LOAD_MARGIN_TILES).toBe(4);
    expect(CHUNK_KEEP_MARGIN_TILES).toBe(12);
  });

  it('everything built is kept, and a built chunk stays while the view moves back up to 8 tiles', () => {
    for (let x = 0; x < 3000; x += 37) {
      for (let y = 0; y < 3000; y += 41) {
        const o = { x, y };
        const built = load(o);
        for (let cx = built.x0; cx <= built.x1; cx++) for (let cy = built.y0; cy <= built.y1; cy++) {
          for (const [dx, dy] of [[8, 0], [-8, 0], [0, 8], [0, -8]]) {
            expect(inside(keep({ x: x + dx * TS, y: y + dy * TS }), cx, cy)).toBe(true);
          }
        }
      }
    }
  });

  it('the keep range is much smaller than with a whole-chunk margin (at most 3 × 3 instead of 4 × 4; 2 × 3 on average)', () => {
    const stats = (margin) => {
      let most = 0;
      let sum = 0;
      let n = 0;
      for (let x = 0; x < 3000; x += 13) {
        for (let y = 0; y < 3000; y += 17) {
          const c = count(chunkRange({ x, y }, VIEW.w, VIEW.h, margin, grid));
          most = Math.max(most, c);
          sum += c;
          n++;
        }
      }
      return { most, mean: sum / n };
    };
    const now = stats(TS * CHUNK_KEEP_MARGIN_TILES);
    const before = stats(32 * TS);
    expect(now.most).toBe(9);
    expect(before.most).toBe(16);
    expect(now.mean).toBeLessThan(6);
    expect(before.mean).toBeGreaterThan(11);
    // what is built at once stays within 3 × 2
    let built = 0;
    for (let x = 0; x < 3000; x += 13) for (let y = 0; y < 3000; y += 17) built = Math.max(built, count(load({ x, y })));
    expect(built).toBe(6);
  });

  it('?chunks=all keeps every chunk', () => {
    expect(chunkRange({ x: 100, y: 100 }, 10, 10, 0, { ...grid, all: true })).toEqual({ x0: 0, x1: 7, y0: 0, y1: 9 });
  });
});
