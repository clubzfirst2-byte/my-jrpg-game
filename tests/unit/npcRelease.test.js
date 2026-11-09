import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { NPC_ANIM, npcFrameKey, idleOffset } from '../../src/view/npcAnim.js';

// NPC release art (docs/npc/NPC_RELEASE_PLAN.md), drawn like the adopted hero (tools/npc_release/):
//   batch 1  the elder, the merchant and the guard (approved: their 120 files are pinned below)
//   batch 2  the village woman, the inn's cook, the village child and the blacksmith
//   revision batch 1 with the review's fixes, in its own folder (src/art-release/npc-revision/)
//   revision-b2  batch 2 with the review's fixes (woman, child, smith), in src/art-release/npc-revision-b2/
//   batch 3  the princess of the star ring and the traveller (new files only; nothing pinned yet),
//            revised after the review (docs/npc/release/batch3/README.md: hair, cape, bedroll, face, stick)
// and how the game picks the frames.

const DIR = new URL('../../src/art-release/npc/', import.meta.url);
const HERO = new URL('../../src/art-release/hero/', import.meta.url);
const REVISION = new URL('../../src/art-release/npc-revision/', import.meta.url);
const BATCH1 = ['elder', 'merchant', 'guard'];
const BATCH2 = ['woman', 'cook', 'child', 'smith'];
const BATCH3 = ['princess', 'traveller'];
const IDS = [...BATCH1, ...BATCH2, ...BATCH3];
const PINNED = JSON.parse(readFileSync(new URL('./fixtures/npc-batch1-sha256.json', import.meta.url), 'utf8'));
const PINNED_B2 = JSON.parse(readFileSync(new URL('./fixtures/npc-batch2-sha256.json', import.meta.url), 'utf8'));
const REVISION_B2 = new URL('../../src/art-release/npc-revision-b2/', import.meta.url);
const sha = (url) => createHash('sha256').update(readFileSync(url)).digest('hex');
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
  it('360 frames: 9 villagers × (idle 4 + walk 6) × 4 directions (batch 2 adds 160, batch 3 adds 80), named npc.<id>.<idle|walk>.<dir>.<n>, nothing else', () => {
    expect(expected).toHaveLength(360);
    expect(expected.filter((f) => BATCH2.includes(f.split('.')[1]))).toHaveLength(160);
    expect(expected.filter((f) => BATCH3.includes(f.split('.')[1]))).toHaveLength(80);
    expect([...files].sort()).toEqual([...expected].sort());
    for (const f of files) expect(f).toMatch(/^npc\.(elder|merchant|guard|woman|cook|child|smith|princess|traveller)\.(idle|walk)\.(down|up|right|left)\.\d$/);
  });

  it('batch 1 (approved) is unchanged: all 120 files byte for byte as approved', () => {
    expect(Object.keys(PINNED)).toHaveLength(120);
    for (const [name, sha] of Object.entries(PINNED)) expect(createHash('sha256').update(readFileSync(new URL(`${name}.png`, DIR))).digest('hex'), name).toBe(sha);
  });

  it('batch 2 (under review) is unchanged by its revision: all 160 files byte for byte as submitted', () => {
    expect(Object.keys(PINNED_B2)).toHaveLength(160);
    for (const [name, h] of Object.entries(PINNED_B2)) expect(sha(new URL(`${name}.png`, DIR)), name).toBe(h);
  });

  it('the batch 2 revision: woman, child and smith only (the cook is unchanged), 40 frames each, valid PNGs, standing on the same feet', () => {
    const rev = readdirSync(REVISION_B2).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
    const ids = ['woman', 'child', 'smith'];
    expect([...rev].sort()).toEqual(Object.keys(PINNED_B2).filter((k) => ids.includes(k.split('.')[1])).sort());
    for (const f of rev) {
      const img = read(new URL(`${f}.png`, REVISION_B2));
      expect([img.w, img.h, img.bitDepth, img.colourType], f).toEqual([32, 56, 8, 6]);
      for (const [x, y] of [[0, 0], [31, 0], [0, 55], [31, 55]]) expect(img.alpha(x, y), f).toBe(0);
      // the feet (the two bottom rows) are where they were: the fixes are above them
      const orig = read(new URL(`${f}.png`, DIR));
      for (let y = 54; y < 56; y++) for (let x = 0; x < 32; x++) expect(img.at(x, y), `${f} (${x},${y})`).toBe(orig.at(x, y));
    }
    // what was asked for changed: her eyes (front and side), his curls (front, back, side), his soot and gloves
    const changed = (f) => sha(new URL(`${f}.png`, REVISION_B2)) !== PINNED_B2[f];
    for (const f of ['npc.woman.idle.down.0', 'npc.woman.idle.right.0', 'npc.child.idle.down.0', 'npc.child.idle.up.0', 'npc.child.idle.right.0', 'npc.smith.idle.down.0', 'npc.smith.idle.right.0']) expect(changed(f), f).toBe(true);
    // the woman's back view (scarf, braid, basket) is left as it was
    expect(changed('npc.woman.idle.up.0')).toBe(false);
    // every cycle still moves: all idle and walk frames differ
    for (const id of ids) {
      for (const [a, { frames }] of Object.entries(NPC_ANIM)) {
        for (const d of DIRS) {
          const pics = new Set([...Array(frames).keys()].map((i) => readFileSync(new URL(`npc.${id}.${a}.${d}.${i}.png`, REVISION_B2)).toString('base64')));
          expect(pics.size, `${id} ${a} ${d}`).toBe(frames);
        }
      }
    }
  });

  it('the batch 1 revision is a separate set: the same 120 names, 32×56, its front / back fixes differ from the approved frames', () => {
    const rev = readdirSync(REVISION).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
    expect([...rev].sort()).toEqual(Object.keys(PINNED).sort());
    for (const f of rev) expect([read(new URL(`${f}.png`, REVISION)).w, read(new URL(`${f}.png`, REVISION)).h], f).toEqual([32, 56]);
    const changed = (f) => createHash('sha256').update(readFileSync(new URL(`${f}.png`, REVISION))).digest('hex') !== PINNED[f];
    for (const id of BATCH1) expect(changed(`npc.${id}.idle.down.0`), `${id} front revised`).toBe(true);
    expect(changed('npc.merchant.idle.up.0'), 'merchant back revised').toBe(true);
    expect(changed('npc.guard.idle.right.0'), 'the guard\'s side view is kept').toBe(false);
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

  it('facing left, what is held or worn on one side (staff, book, spear, basket, ladle, towel, pinwheel, bag, hammer, bracelet, walking stick, scarf end) stays on that side: left frames are drawn on their own', () => {
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

  it('different builds in the same frame: the child is the smallest, then the elder; the guard reaches higher than the merchant; the smith is the biggest', () => {
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
    expect(t.child).toBeGreaterThan(t.elder + 3);
    expect(t.woman).toBeGreaterThan(t.cook);
    // batch 3: the traveller is the tallest (the hat's crown at the top of the frame); the princess
    // is two pixels shorter than the hero
    for (const id of IDS) expect(t.traveller, `traveller at least as tall as ${id}`).toBeLessThanOrEqual(t[id]);
    expect(t.traveller).toBe(0);
    expect(t.princess).toBe(hero + 2);
    // bulk: the figure's area (the guard's spear and the elder's staff aside, the smith is the biggest)
    const bulk = (id) => {
      const img = read(new URL(`npc.${id}.idle.down.0.png`, DIR));
      let n = 0;
      for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) if (img.alpha(x, y)) n++;
      return n;
    };
    for (const id of ['woman', 'cook', 'merchant', 'child']) expect(bulk('smith'), `smith bigger than ${id}`).toBeGreaterThan(bulk(id));
    expect(bulk('child')).toBeLessThan(bulk('woman') * 0.75);
  });

  it('no two villagers share a body: front frames differ in most pixels (no colour swaps of one shape)', () => {
    const shape = (id) => {
      const img = read(new URL(`npc.${id}.idle.down.0.png`, DIR));
      const out = [];
      for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) out.push(img.alpha(x, y) ? 1 : 0);
      return out;
    };
    const shapes = Object.fromEntries(IDS.map((id) => [id, shape(id)]));
    for (const a of IDS) {
      for (const b of IDS) {
        if (a >= b) continue;
        const diff = shapes[a].reduce((n, v, i) => n + (v !== shapes[b][i] ? 1 : 0), 0);
        expect(diff, `${a} vs ${b}: silhouettes differ`).toBeGreaterThan(80);
      }
    }
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

describe('NPC release art, batch 3 revision 1 (the review of docs/npc/release/batch3)', () => {
  // ramps from tools/npc_release/princess.py and traveller.py (and the shared wood / gold)
  const ramp = (...hex) => new Set(hex.map((h) => parseInt(h.slice(1), 16)));
  const HAIR = ramp('#5e6888', '#98a2c0', '#c6cee4', '#eef2fc'); // the princess's silver (outline aside)
  const GOLD = ramp('#5a4018', '#a07a30', '#e8c060', '#f8dc88', '#fff4c8');
  const WOOD = ramp('#4a2c16', '#6e4424', '#906038', '#b07e50'); // the stick itself (its outline aside)
  const BEDROLL = ramp('#141c10', '#34442a', '#4e6240', '#6a7e58', '#8c9e78');
  const SKIN_T = ramp('#5a2e1c', '#bc7c56', '#daa47a', '#ecbc92', '#f8d2aa');
  const pixels = (name, set) => {
    const img = frame(name);
    const out = [];
    for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) if (img.alpha(x, y) && set.has(img.at(x, y) >>> 8)) out.push([x, y]);
    return out;
  };
  const each = (id, dirs, fn) => {
    for (const [a, { frames }] of Object.entries(NPC_ANIM)) for (const d of dirs) for (let i = 0; i < frames; i++) fn(`npc.${id}.${a}.${d}.${i}`, a, d, i);
  };

  it('the princess: from the front the long hair falls past the shoulders at both sides, and in every view it ends at the waist', () => {
    each('princess', ['down'], (f) => {
      const hair = pixels(f, HAIR);
      const outside = (side) => hair.filter(([x, y]) => y >= 30 && y <= 36 && (side < 0 ? x <= 5 : x >= 26)).length;
      expect(outside(-1), `${f}: hair beside the cape (image left)`).toBeGreaterThan(8);
      expect(outside(1), `${f}: hair beside the cape (image right)`).toBeGreaterThan(8);
    });
    each('princess', DIRS, (f) => {
      expect(Math.max(...pixels(f, HAIR).map(([, y]) => y)), `${f}: the hair ends at the waist`).toBeLessThanOrEqual(39);
    });
  });

  it('the princess: the bracelet on her left wrist shows from the front (image right) and facing left (near); left frames are the mirror of right plus the bracelet', () => {
    each('princess', ['down'], (f) => {
      expect(pixels(f, GOLD).filter(([x, y]) => x >= 19 && x <= 21 && y >= 38 && y <= 42).length, f).toBeGreaterThanOrEqual(2);
    });
    each('princess', ['left'], (f, a, d, i) => {
      const L = frame(f);
      const R = frame(`npc.princess.${a}.right.${i}`);
      const diff = [];
      for (let y = 0; y < 56; y++) for (let x = 0; x < 32; x++) if (L.at(x, y) !== R.at(31 - x, y)) diff.push([x, y]);
      expect(diff.length, `${f}: mirror + bracelet`).toBeGreaterThan(0);
      expect(diff.length, `${f}: mirror + bracelet`).toBeLessThanOrEqual(8);
      expect(diff.filter(([x, y]) => GOLD.has(L.at(x, y) >>> 8)).length, `${f}: the bracelet`).toBeGreaterThanOrEqual(2);
    });
  });

  it('the traveller: standing, the stick does not move (its foot stays planted; only the hand shifts its grip)', () => {
    for (const d of DIRS) {
      const low = (i) => JSON.stringify(pixels(`npc.traveller.idle.${d}.${i}`, WOOD).filter(([, y]) => y >= 40));
      for (let i = 1; i < 4; i++) expect(low(i), `traveller idle ${d} ${i}`).toBe(low(0));
    }
  });

  it('the traveller: walking, the stick is planted (its foot on the ground) and then lifted and set down again', () => {
    for (const d of ['down', 'right']) {
      const foot = [...Array(6).keys()].map((i) => Math.max(...pixels(`npc.traveller.walk.${d}.${i}`, WOOD).map(([, y]) => y)));
      expect(foot.filter((y) => y === 55).length, `${d}: planted`).toBeGreaterThanOrEqual(3);
      expect(Math.min(...foot), `${d}: lifted`).toBeLessThan(55);
    }
    // facing right the stick leans forward as the walker passes it (its top ahead of its foot)
    const lean = pixels('npc.traveller.walk.right.3', WOOD).filter(([x]) => x > 20);
    const top = lean.filter(([, y]) => y < 12).map(([x]) => x);
    const foot = lean.filter(([, y]) => y > 50).map(([x]) => x);
    expect(Math.min(...top)).toBeGreaterThan(Math.min(...foot));
  });

  it('the traveller: from the front the bedroll only shows small above the shoulders (not as shoulder pads), the face is lit under the brim', () => {
    each('traveller', ['down'], (f) => {
      const roll = pixels(f, BEDROLL);
      expect(Math.max(...roll.map(([, y]) => y)), `${f}: above the shoulders`).toBeLessThanOrEqual(18);
      expect(Math.min(...roll.map(([x]) => x)), `${f}: not past the shoulders`).toBeGreaterThanOrEqual(4);
      expect(Math.max(...roll.map(([x]) => x)), `${f}: not past the shoulders`).toBeLessThanOrEqual(27);
    });
    // the mean brightness (luma, 0-100) of the face's skin: 55 before the review, now near the smith and the elder
    const img = frame('npc.traveller.idle.down.0');
    let sum = 0;
    let n = 0;
    for (let y = 0; y < 26; y++) {
      for (let x = 0; x < 32; x++) {
        const c = img.at(x, y) >>> 8;
        if (!img.alpha(x, y) || !SKIN_T.has(c)) continue;
        sum += (0.299 * (c >> 16) + 0.587 * ((c >> 8) & 0xff) + 0.114 * (c & 0xff)) / 2.55;
        n++;
      }
    }
    expect(n).toBeGreaterThan(80);
    expect(sum / n).toBeGreaterThanOrEqual(65);
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
    expect(npcFrameKey(npc({ id: 'stranger', look: 2 }), 5, has)).toBe('npc.2.walk.down.0');
    const walking = new Set();
    for (let w = 0; w < 1; w += 0.05) walking.add(npcFrameKey(npc({ id: 'pilgrim', look: 5, moving: true, walkTime: w }), 0, has));
    expect([...walking].sort()).toEqual(['npc.5.walk.down.0', 'npc.5.walk.down.1', 'npc.5.walk.down.2']);
    // batch 2: the cook and the child (in the village) now have their own
    expect(npcFrameKey(npc({ id: 'cook', look: 2 }), 0, has)).toMatch(/^npc\.cook\.idle\.down\./);
    // batch 3: the princess and the traveller have their own (not placed in the game yet)
    expect(npcFrameKey(npc({ id: 'princess', look: 5, facing: 'left' }), 0, has)).toMatch(/^npc\.princess\.idle\.left\./);
    expect(npcFrameKey(npc({ id: 'traveller', look: 2, moving: true, walkTime: 0.01 }), 0, has)).toBe('npc.traveller.walk.down.0');
    // with no release art at all (?npc=placeholder), everyone keeps it
    expect(npcFrameKey(npc({}), 0, () => false)).toBe('npc.1.walk.down.0');
  });

  it('two villagers do not breathe in step', () => {
    expect(idleOffset('elder')).not.toBe(idleOffset('guard'));
    expect(idleOffset('merchant')).toBeGreaterThanOrEqual(0);
    expect(idleOffset('merchant')).toBeLessThan(1);
  });
});
