import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';
import { NPC_ANIM, npcFrameKey, idleOffset } from '../../src/view/npcAnim.js';

// NPC batch 1 (docs/npc/NPC_RELEASE_PLAN.md): the elder, the merchant and the guard at release
// quality, drawn like the adopted hero (tools/npc_release/), and how the game picks their frames.

const DIR = new URL('../../src/art-release/npc/', import.meta.url);
const HERO = new URL('../../src/art-release/hero/', import.meta.url);
const IDS = ['elder', 'merchant', 'guard'];
const DIRS = ['down', 'up', 'right', 'left'];
const files = readdirSync(DIR).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));

/** Decodes one of our PNGs (8-bit RGBA, filter 0 on every row, as tools/art_proto/pixel.py writes). */
function read(url) {
  const buf = readFileSync(url);
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  const chunks = [];
  for (let p = 8; p < buf.length; ) {
    const n = buf.readUInt32BE(p);
    if (buf.toString('ascii', p + 4, p + 8) === 'IDAT') chunks.push(buf.subarray(p + 8, p + 8 + n));
    p += 12 + n;
  }
  const raw = inflateSync(Buffer.concat(chunks));
  const at = (x, y) => raw.readUInt32BE(y * (w * 4 + 1) + 1 + x * 4);
  return { w, h, colourType: buf[25], bitDepth: buf[24], filters: [...Array(h).keys()].map((y) => raw[y * (w * 4 + 1)]), at, alpha: (x, y) => at(x, y) & 0xff };
}
const frame = (name) => read(new URL(`${name}.png`, DIR));
const expected = IDS.flatMap((id) => Object.entries(NPC_ANIM).flatMap(([a, { frames }]) => DIRS.flatMap((d) => [...Array(frames).keys()].map((i) => `npc.${id}.${a}.${d}.${i}`))));

/** The body only: the staff and the spear (with their heads) stand at the frame's edges (x < 8 or x > 24). */
const BODY = { x0: 8, x1: 24 };

describe('NPC release art, batch 1 (src/art-release/npc)', () => {
  it('120 frames: 3 villagers × (idle 4 + walk 6) × 4 directions, named npc.<id>.<idle|walk>.<dir>.<n>, nothing else', () => {
    expect(expected).toHaveLength(120);
    expect([...files].sort()).toEqual([...expected].sort());
    for (const f of files) expect(f).toMatch(/^npc\.(elder|merchant|guard)\.(idle|walk)\.(down|up|right|left)\.\d$/);
  });

  it('every frame is a 32×56 RGBA PNG with a transparent background', () => {
    for (const f of expected) {
      const img = frame(f);
      expect([img.w, img.h], f).toEqual([32, 56]);
      expect([img.bitDepth, img.colourType], `${f}: 8-bit RGBA`).toEqual([8, 6]);
      for (const [x, y] of [[0, 0], [31, 0], [0, 55], [31, 55]]) expect(img.alpha(x, y), `${f} (${x},${y}) transparent`).toBe(0);
      let opaque = 0;
      let partial = 0;
      for (let y = 0; y < 56; y++) {
        for (let x = 0; x < 32; x++) {
          const a = img.alpha(x, y);
          if (a === 255) opaque++;
          else if (a !== 0) partial++;
        }
      }
      expect(partial, `${f}: crisp pixels (no half-transparent edges)`).toBe(0);
      expect(opaque, `${f}: a figure`).toBeGreaterThan(400);
    }
  });

  it('the feet stand on the bottom rows, centred (the same anchor as the hero: feet at the bottom centre)', () => {
    for (const f of expected) {
      const img = frame(f);
      let lowest = -1;
      let sum = 0;
      let n = 0;
      for (let y = 0; y < 56; y++) {
        for (let x = BODY.x0; x <= BODY.x1; x++) {
          if (!img.alpha(x, y)) continue;
          lowest = y;
          if (y >= 53) {
            sum += x;
            n++;
          }
        }
      }
      expect(lowest, `${f}: feet on the ground line`).toBeGreaterThanOrEqual(54);
      expect(Math.abs(sum / n - 16), `${f}: feet centred`).toBeLessThan(6);
    }
  });

  it('standing still the feet do not move: the idle frames share their soles (the two bottom rows)', () => {
    for (const id of IDS) {
      for (const d of DIRS) {
        const rows = (i) => {
          const img = frame(`npc.${id}.idle.${d}.${i}`);
          const out = [];
          for (let y = 54; y < 56; y++) for (let x = BODY.x0; x <= BODY.x1; x++) out.push(img.at(x, y));
          return out.join(',');
        };
        for (let i = 1; i < 4; i++) expect(rows(i), `${id} idle ${d} ${i}`).toBe(rows(0));
      }
    }
  });

  it('every frame of a cycle is a different picture (breathing, glints, blinking, steps)', () => {
    for (const id of IDS) {
      for (const [a, { frames }] of Object.entries(NPC_ANIM)) {
        for (const d of DIRS) {
          const pics = new Set([...Array(frames).keys()].map((i) => readFileSync(new URL(`npc.${id}.${a}.${d}.${i}.png`, DIR)).toString('base64')));
          expect(pics.size, `${id} ${a} ${d}`).toBe(frames);
        }
      }
    }
  });

  it('facing left, the staff, the book and the spear stay in the same hand: left frames are drawn on their own', () => {
    const isMirror = (a, b) => {
      const A = frame(a);
      const B = frame(b);
      for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) if (A.at(x, y) !== B.at(31 - x, y)) return false;
      return true;
    };
    for (const id of IDS) {
      for (const [a, { frames }] of Object.entries(NPC_ANIM)) {
        for (let i = 0; i < frames; i++) expect(isMirror(`npc.${id}.${a}.left.${i}`, `npc.${id}.${a}.right.${i}`), `${id} ${a} ${i}`).toBe(false);
      }
    }
  });

  it('different builds in the same frame: the elder is the smallest, the guard reaches higher than the merchant', () => {
    const top = (url) => {
      const img = read(url);
      for (let y = 0; y < 56; y++) for (let x = BODY.x0; x <= BODY.x1; x++) if (img.alpha(x, y)) return y;
      return 56;
    };
    const hero = top(new URL('hero.idle.down.0.png', HERO));
    const t = Object.fromEntries(IDS.map((id) => [id, top(new URL(`npc.${id}.idle.down.0.png`, DIR))]));
    expect(t.elder).toBeGreaterThan(t.merchant);
    expect(t.elder).toBeGreaterThan(hero + 4);
    expect(t.guard).toBeLessThan(t.merchant);
    expect(t.guard).toBeLessThanOrEqual(hero + 1);
  });

  it('the same palette as the hero for shared materials: skin, leather and gold come from the same ramps', () => {
    // the outline of a part is the darkest tone of its material; all villagers have a dark outline
    for (const id of IDS) {
      const img = frame(`npc.${id}.idle.down.0`);
      let darkest = 255 * 3;
      for (let y = 0; y < 56; y++) {
        for (let x = 0; x < 32; x++) {
          if (!img.alpha(x, y)) continue;
          const c = img.at(x, y) >>> 8;
          darkest = Math.min(darkest, (c >> 16) + ((c >> 8) & 0xff) + (c & 0xff));
        }
      }
      expect(darkest, id).toBeLessThan(120);
    }
  });
});

describe('npcFrameKey: which frame a villager shows', () => {
  const release = new Set(expected);
  const has = (k) => release.has(k);
  const npc = (o) => ({ id: 'elder', look: 1, facing: 'down', moving: false, walkTime: 0, ...o });

  it('standing: the idle loop in the facing direction, by time (4 frames, 3 per second)', () => {
    const seen = new Set();
    for (let t = 0; t < 2; t += 0.05) {
      const k = npcFrameKey(npc({ facing: 'right' }), t, has);
      expect(k).toMatch(/^npc\.elder\.idle\.right\.[0-3]$/);
      seen.add(k);
    }
    expect(seen.size).toBe(4);
  });

  it('walking: the walk cycle by the time spent walking, so the steps match the movement', () => {
    const seen = [];
    for (let w = 0; w < 6 / NPC_ANIM.walk.fps; w += 1 / NPC_ANIM.walk.fps) seen.push(npcFrameKey(npc({ moving: true, facing: 'up', walkTime: w + 0.01 }), 0, has));
    expect(seen).toEqual([0, 1, 2, 3, 4, 5].map((i) => `npc.elder.walk.up.${i}`));
  });

  it('stopping goes straight to a standing frame; facing the hero (talking) shows that direction', () => {
    expect(npcFrameKey(npc({ moving: false, walkTime: 3.3, facing: 'left' }), 1, has)).toMatch(/^npc\.elder\.idle\.left\./);
    for (const d of DIRS) expect(npcFrameKey(npc({ id: 'guard', facing: d }), 0, has)).toMatch(new RegExp(`^npc\\.guard\\.idle\\.${d}\\.`));
  });

  it('a villager without release art keeps the placeholder frames (npc.<look>.walk.<dir>.<0..2>)', () => {
    expect(npcFrameKey(npc({ id: 'cook', look: 2 }), 5, has)).toBe('npc.2.walk.down.0');
    const walking = new Set();
    for (let w = 0; w < 1; w += 0.05) walking.add(npcFrameKey(npc({ id: 'child', look: 5, moving: true, walkTime: w }), 0, has));
    expect([...walking].sort()).toEqual(['npc.5.walk.down.0', 'npc.5.walk.down.1', 'npc.5.walk.down.2']);
    // with no release art at all (?npc=placeholder), everyone keeps it
    expect(npcFrameKey(npc({}), 0, () => false)).toBe('npc.1.walk.down.0');
  });

  it('two villagers do not breathe in step', () => {
    expect(idleOffset('elder')).not.toBe(idleOffset('guard'));
    expect(idleOffset('merchant')).toBeGreaterThanOrEqual(0);
    expect(idleOffset('merchant')).toBeLessThan(1);
  });
});
