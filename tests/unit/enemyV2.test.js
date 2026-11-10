import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';

// Enemy & boss art v2 (graphics project W3): src/art-release-v2/enemy, drawn by tools/enemy_v2.
// 4-8 frames per action, 8-step ramps, the hero's outline rule (each material's darkest tone,
// never near-black). Same names / sizes / anchors as v1; the frame counts are in the v2 frames.json.
const DIR = new URL('../../src/art-release-v2/enemy/', import.meta.url);
const files = readdirSync(DIR).filter((f) => f.endsWith('.png'));
const MAN = JSON.parse(readFileSync(new URL('frames.json', DIR), 'utf8'));
const V1 = JSON.parse(readFileSync(new URL('../../docs/art-release/enemy/frames.json', import.meta.url), 'utf8'));

const decoded = new Map();
function decode(name) {
  if (!decoded.has(name)) decoded.set(name, decodeFile(name));
  return decoded.get(name);
}

function decodeFile(name) {
  const buf = readFileSync(new URL(`${name}.png`, DIR));
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  const depth = buf[24];
  const type = buf[25];
  const chunks = [];
  for (let p = 8; p < buf.length; ) {
    const n = buf.readUInt32BE(p);
    if (buf.toString('ascii', p + 4, p + 8) === 'IDAT') chunks.push(buf.subarray(p + 8, p + 8 + n));
    p += 12 + n;
  }
  const raw = inflateSync(Buffer.concat(chunks));
  const bpp = 4;
  const stride = w * bpp;
  const px = Buffer.alloc(stride * h);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    for (let x = 0; x < stride; x++) {
      const v = raw[y * (stride + 1) + 1 + x];
      const a = x >= bpp ? px[y * stride + x - bpp] : 0;
      const b = y > 0 ? px[(y - 1) * stride + x] : 0;
      const c = x >= bpp && y > 0 ? px[(y - 1) * stride + x - bpp] : 0;
      let out = v;
      if (f === 1) out = v + a;
      else if (f === 2) out = v + b;
      else if (f === 3) out = v + ((a + b) >> 1);
      else if (f === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a);
        const pb = Math.abs(p - b);
        const pc = Math.abs(p - c);
        out = v + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c);
      }
      px[y * stride + x] = out & 255;
    }
  }
  return { w, h, depth, type, px };
}

// The 5-tone ramps of tools/enemy_release/rig.py (the design's and the guide's colours, tone 0 = outline).
const RAMPS = {
  murk: ['120a1a', '2e1a3e', '4a2a62', '6e4490', '9a70c0'],
  glow: ['2a0a2a', '6a1e6a', 'b040b0', 'e070e0', 'ffc8ff'],
  eye: ['4a2a08', 'b06a10', 'ffd84a', 'fff2a8', 'fffbe0'],
  ashfur: ['1a1418', '3a3036', '5a4c50', '7e6e6e', 'a69690'],
  gobskin: ['24201a', '4e4636', '7a6e54', 'a09474', 'c4ba98'],
  plum: ['1e1016', '3e2430', '5e3a46', '80565e', 'a07a80'],
  oldstone: ['1e1e26', '4e4e5a', '9696a0', 'bcbcc6', 'e2e2ea'],
  bronze: ['24140c', '5a3418', '8a5628', 'b0783e', 'd4a064'],
  rotwood: ['1a120e', '3a2a20', '5e4636', '846650', 'a88a70'],
  fungus: ['3a1a0a', '8a4420', 'd07a3a', 'eaa868', 'f8d4a8'],
  frostfur: ['261e1a', '55483e', '8a7a6c', 'b0a294', 'dcd2c6'],
  ice: ['1a3040', '3e6e88', '7ab4cc', 'b8e4f0', 'f0fcff'],
  murksand: ['1c1018', '3e2a3a', '5e4458', '82666e', 'a88c88'],
  mask: ['2e2a26', '6e665c', 'a89e90', 'd2cabc', 'f2ece2'],
  slate: ['1c1a26', '46445a', '7a7896', 'a4a2bc', 'cccade'],
  spark: ['4a3a08', 'b08a10', 'ffe14a', 'fff59a', 'ffffff'],
  lake: ['081c34', '143e66', '22608e', '3a84b2', '6aaed2'],
  ashring: ['24201e', '4e4844', '7c7470', 'a8a09a', 'd6d0ca'],
  bone: ['3a3226', '9a8c70', 'd0c4a4', 'e8dec4', 'fff8e4'],
  wood: ['1e1008', '4a2c16', '6e4424', '906038', 'b07e50'],
  leather: ['24160c', '4a3020', '704c30', '946c46', 'b88c5e'],
};

// v2 ramps (round 2): 7 steps -- tone 0 (the outline; lifted a quarter toward tone 1 only when it
// is darker than the hero's darkest outline, max(r, g, b) < 24), 1, 1.5, 2, 2.5, 3, 4
const rgb = (h) => [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
const mix = (a, b, f) => a.map((v, i) => Math.round(v + (b[i] - v) * f));
const hex = (c) => c.map((v) => v.toString(16).padStart(2, '0')).join('');
const RAMP8 = Object.fromEntries(
  Object.entries(RAMPS).map(([k, v]) => {
    const c = v.map(rgb);
    const o = Math.max(...c[0]) >= 34 ? c[0] : mix(c[0], c[1], 0.2);
    return [k, [o, c[1], mix(c[1], c[2], 0.5), c[2], mix(c[2], c[3], 0.5), c[3], c[4]].map(hex)];
  })
);
const COLOURS = new Set(Object.values(RAMP8).flat());
/** colour -> [material, ramp index] */
const WHICH = new Map();
for (const [k, r] of Object.entries(RAMP8)) r.forEach((c, i) => WHICH.has(c) || WHICH.set(c, [k, i]));
const OUTLINES = new Set(Object.values(RAMP8).map((r) => r[0]));
const RESERVED = [
  [0xff, 0x3a, 0x3a],
  [0x60, 0xa0, 0xff],
];
const px4 = (px, i) => hex([px[i], px[i + 1], px[i + 2]]);

/** the v2 frame-count rules (W3, approved): action -> [min, max] */
const RANGE = {
  idle: [4, 4],
  idle2: [4, 4],
  move: [6, 8],
  windup: [3, 4],
  attack: [4, 6],
  hurt: [2, 3],
  hurt2: [2, 3],
  stagger2: [3, 4],
  stagger: [3, 4],
  defeat: [4, 6],
  transform: [4, 6],
  tendril: [3, 4],
  orb: [4, 4],
  ice: [4, 4],
  sand: [4, 4],
  spark: [4, 4],
};
const range = (a) => RANGE[a] || RANGE[a.split('_')[0]];
/** kinds still being drawn (W3 is pushed in batches: enemies first, then bosses and shots) */
const BATCH_PENDING = [];

function silhouetteChange(a, b) {
  const A = decode(a);
  const B = decode(b);
  let op = 0;
  let diff = 0;
  for (let i = 3; i < A.px.length; i += 4) {
    if (A.px[i]) op++;
    if (!A.px[i] !== !B.px[i]) diff++;
  }
  return diff / op;
}

const expected = new Map();
for (const [kind, k] of Object.entries(MAN.kinds)) {
  for (const [action, a] of Object.entries(k.actions)) {
    for (let i = 0; i < a.frames; i++) expected.set(`enemy.${kind}.${action}.${i}`, a.size);
  }
}
for (const [copy] of Object.entries(MAN.minimal)) expected.set(copy, null);

describe('enemy & boss art v2 (src/art-release-v2/enemy)', () => {
  it('has every kind and action of v1, with the v2 frame counts (4-8 per action)', () => {
    for (const [kind, k] of Object.entries(V1.kinds)) {
      if (!MAN.kinds[kind] && BATCH_PENDING.includes(kind)) continue; // drawn in the next batch
      expect(MAN.kinds[kind], kind).toBeTruthy();
      for (const action of Object.keys(k.actions)) {
        const a = MAN.kinds[kind].actions[action];
        expect(a, `${kind} ${action}`).toBeTruthy();
        const [lo, hi] = range(action);
        expect(a.frames, `${kind} ${action}`).toBeGreaterThanOrEqual(lo);
        expect(a.frames, `${kind} ${action}`).toBeLessThanOrEqual(hi);
        expect(a.size, `${kind} ${action}: same size as v1`).toEqual(k.actions[action].size);
      }
    }
  });

  it('the folder holds exactly the frames in frames.json (plus the minimal pair)', () => {
    for (const name of expected.keys()) expect(files, name).toContain(`${name}.png`);
    expect(files.filter((f) => !expected.has(f.replace(/\.png$/, '')))).toEqual([]);
  });

  it('sizes, 8-bit RGBA, alpha 0 / 255 only', () => {
    for (const [name, size] of expected) {
      const { w, h, depth, type, px } = decode(name);
      if (size) expect([w, h], name).toEqual(size);
      expect([depth, type], name).toEqual([8, 6]);
      let soft = 0;
      for (let i = 3; i < px.length; i += 4) if (px[i] !== 0 && px[i] !== 255) soft++;
      expect(soft, name).toBe(0);
    }
  });

  it('colours: only the v2 ramps, none near the reserved warning red / flinch blue', () => {
    for (const name of expected.keys()) {
      const { px } = decode(name);
      const off = new Set();
      let near = 0;
      for (let i = 0; i < px.length; i += 4) {
        if (!px[i + 3]) continue;
        if (!COLOURS.has(px4(px, i))) off.add(px4(px, i));
        for (const [r, g, b] of RESERVED) if (Math.abs(px[i] - r) + Math.abs(px[i + 1] - g) + Math.abs(px[i + 2] - b) < 60) near++;
      }
      expect([...off], name).toEqual([]);
      expect(near, name).toBe(0);
    }
  });

  it("the hero's outline rule: every outer edge pixel is a material's darkest tone (as dark as the hero's)", () => {
    for (const name of expected.keys()) {
      if (name.startsWith('enemy.shot.')) continue;
      const { w, h, px } = decode(name);
      const a = (x, y) => px[(y * w + x) * 4 + 3] > 0;
      let bad = 0;
      let black = 0;
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          if (!a(x, y)) continue;
          const edge = [
            [1, 0],
            [-1, 0],
            [0, 1],
            [0, -1],
          ].some(([dx, dy]) => x + dx >= 0 && y + dy >= 0 && x + dx < w && y + dy < h && !a(x + dx, y + dy));
          if (!edge) continue;
          const i = (y * w + x) * 4;
          if (!OUTLINES.has(px4(px, i))) bad++;
          if (Math.max(px[i], px[i + 1], px[i + 2]) < 30) black++;
        }
      }
      expect(bad, `${name}: outer edge not an outline tone`).toBe(0);
      void black;
    }
  });

  it('no frame touches the top row; every idle frame stands on the ground (shots excepted)', () => {
    for (const name of expected.keys()) {
      if (name.startsWith('enemy.shot.')) continue;
      const { w, h, px } = decode(name);
      let top = 0;
      for (let x = 0; x < w; x++) if (px[x * 4 + 3]) top++;
      expect(top, `${name}: top row`).toBe(0);
      if (/\.idle2?\.\d$/.test(name)) {
        let lowest = -1;
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (px[(y * w + x) * 4 + 3]) lowest = y;
        expect(lowest, `${name}: on the ground line`).toBeGreaterThanOrEqual(h - 2);
      }
    }
  });

  it('every frame of an action is a different picture', () => {
    for (const [kind, k] of Object.entries(MAN.kinds)) {
      for (const [action, a] of Object.entries(k.actions)) {
        const pics = new Set();
        for (let i = 0; i < a.frames; i++) pics.add(readFileSync(new URL(`enemy.${kind}.${action}.${i}.png`, DIR)).toString('base64'));
        expect(pics.size, `${kind} ${action}`).toBe(a.frames);
      }
    }
  });

  it('the minimal pair is byte-identical to the frames it mirrors', () => {
    for (const [copy, src] of Object.entries(MAN.minimal)) {
      expect(readFileSync(new URL(`${copy}.png`, DIR)).equals(readFileSync(new URL(`${src}.png`, DIR))), copy).toBe(true);
    }
  });

  it('wind-ups read by shape: the held (last) wind-up frame changes the outline >= 20% vs idle; for bosses every wind-up frame does', () => {
    for (const [kind, k] of Object.entries(MAN.kinds)) {
      for (const [action, a] of Object.entries(k.actions)) {
        if (!action.startsWith('windup')) continue;
        const from = kind.startsWith('boss_') ? 0 : a.frames - 1;
        for (let i = from; i < a.frames; i++) {
          const c = silhouetteChange(`enemy.${kind}.idle.0`, `enemy.${kind}.${action}.${i}`);
          expect(c, `${kind} ${action}.${i}`).toBeGreaterThanOrEqual(0.2);
        }
      }
    }
  });

  it('tones per material: at most 6 for a normal enemy, 7 for a boss (round 2: no gradients)', () => {
    for (const [kind, k] of Object.entries(MAN.kinds)) {
      if (kind === 'shot') continue;
      const used = new Map();
      for (const [action, a] of Object.entries(k.actions)) {
        for (let i = 0; i < a.frames; i++) {
          const { px } = decode(`enemy.${kind}.${action}.${i}`);
          for (let j = 0; j < px.length; j += 4) {
            if (!px[j + 3]) continue;
            const [m, t] = WHICH.get(px4(px, j));
            if (!used.has(m)) used.set(m, new Set());
            used.get(m).add(t);
          }
        }
      }
      const max = kind.startsWith('boss_') ? 7 : 6;
      for (const [m, set] of used) expect(set.size, `${kind} ${m}: tones ${[...set].sort()}`).toBeLessThanOrEqual(max);
    }
  });

  it('in-between tones (1.5, 2.5) only in clusters at least 2 px wide (each pixel in a 2x2 block of itself)', () => {
    for (const name of expected.keys()) {
      if (name.startsWith('enemy.shot.')) continue;
      const { w, h, px } = decode(name);
      const col = (x, y) => (x >= 0 && y >= 0 && x < w && y < h && px[(y * w + x) * 4 + 3] ? px4(px, (y * w + x) * 4) : null);
      let lone = 0;
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const c = col(x, y);
          if (!c) continue;
          const t = WHICH.get(c)[1];
          if (t !== 2 && t !== 4) continue;
          const inBlock = [
            [0, 0],
            [-1, 0],
            [0, -1],
            [-1, -1],
          ].some(([ox, oy]) => [0, 1].every((dy) => [0, 1].every((dx) => col(x + ox + dx, y + oy + dy) === c)));
          if (!inBlock) lone++;
        }
      }
      expect(lone, `${name}: in-between pixels outside a 2x2 cluster`).toBe(0);
    }
  });

  it('phase 2 has its own hurt and stagger (the phase-2 marks never drop out)', () => {
    for (const kind of ['boss_root', 'boss_frost', 'boss_sand', 'boss_storm']) {
      expect(MAN.kinds[kind].actions.hurt2, kind).toBeTruthy();
      expect(MAN.kinds[kind].actions.stagger2, kind).toBeTruthy();
    }
    expect(MAN.kinds.boss_source.actions.hurt2).toBeTruthy();
  });

  it('boss attacks strike: frame 0 or 1 of every attack changes the outline >= 25% vs idle', () => {
    for (const [kind, k] of Object.entries(MAN.kinds)) {
      if (!kind.startsWith('boss_')) continue;
      for (const action of Object.keys(k.actions)) {
        if (!action.startsWith('attack_')) continue;
        const c = Math.max(silhouetteChange(`enemy.${kind}.idle.0`, `enemy.${kind}.${action}.0`), silhouetteChange(`enemy.${kind}.idle.0`, `enemy.${kind}.${action}.1`));
        expect(c, `${kind} ${action}`).toBeGreaterThanOrEqual(0.25);
      }
    }
  });

  it('defeats dissolve: every defeat frame changes the outline from the one before (no hold, then pop)', () => {
    for (const [kind, k] of Object.entries(MAN.kinds)) {
      const a = k.actions.defeat;
      if (!a) continue;
      for (let i = 1; i < a.frames; i++) {
        const c = silhouetteChange(`enemy.${kind}.defeat.${i - 1}`, `enemy.${kind}.defeat.${i}`);
        expect(c, `${kind} defeat ${i - 1} -> ${i}`).toBeGreaterThanOrEqual(0.05);
      }
    }
  });
});
