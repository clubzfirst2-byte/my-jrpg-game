import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';

// Enemy & boss release art (src/art-release/enemy, under review; drawn by tools/enemy_release).
// Names: the minimal set the current code draws (enemy.<kind>.0 / .1) and the full set by action
// (enemy.<kind>.<action>.<n>), as in docs/art-release/enemy/PRODUCTION.md.
const DIR = new URL('../../src/art-release/enemy/', import.meta.url);
const files = readdirSync(DIR);

const MOB = { idle: 2, move: 4, windup: 2, attack: 2, hurt: 1, defeat: 3 };
const core = (patterns) => ({
  idle: 2,
  move: 2,
  ...Object.fromEntries(patterns.flatMap((p) => [[`windup_${p}`, 2], [`attack_${p}`, 2]])),
  hurt: 1,
  stagger: 2,
  idle2: 2,
  defeat: 4,
});
/** kind -> { size, actions: action -> frames, sizes?: action -> size } */
const KINDS = {
  beast: { size: [44, 32], actions: MOB },
  archer: { size: [32, 56], actions: MOB },
  slime: { size: [32, 28], actions: MOB },
  sentinel: { size: [40, 56], actions: MOB },
  boss_root: { size: [96, 80], actions: core(['charge', 'slam', 'volley']) },
  boss_frost: { size: [96, 88], actions: core(['slam', 'ring', 'charge']) },
  boss_sand: { size: [80, 96], actions: core(['volley', 'charge', 'ring']) },
  boss_storm: { size: [88, 96], actions: core(['ring', 'volley', 'slam']) },
  boss_source: {
    size: [128, 128],
    actions: {
      idle: 2,
      idle2: 2,
      ...Object.fromEntries(['volley', 'ring', 'slam', 'charge'].flatMap((p) => [[`windup_${p}`, 2], [`attack_${p}`, 2]])),
      hurt: 1,
      transform: 4,
      defeat: 6,
      tendril: 3,
    },
    sizes: { tendril: [32, 48] },
  },
  shot: { size: [12, 12], actions: { orb: 2, ice: 2, sand: 2, spark: 2 } },
};
const MINIMAL = ['beast', 'archer', 'boss_root', 'boss_frost', 'boss_sand', 'boss_storm'];
const SIZE_OF = Object.fromEntries(Object.entries(KINDS).map(([k, v]) => [k, v.size]));

const expected = new Map();
for (const [kind, k] of Object.entries(KINDS)) {
  for (const [action, n] of Object.entries(k.actions)) {
    for (let i = 0; i < n; i++) expected.set(`enemy.${kind}.${action}.${i}`, (k.sizes && k.sizes[action]) || k.size);
  }
}
for (const kind of MINIMAL) for (const i of [0, 1]) expected.set(`enemy.${kind}.${i}`, SIZE_OF[kind]);

const decoded = new Map();
/** Decode an 8-bit RGBA PNG (any filter); cached. */
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
const RAMP_COLOURS = new Set(Object.values(RAMPS).flat());
const OUTLINE_COLOURS = new Set(Object.values(RAMPS).map((r) => r[0]));
// reserved for the program's cues (ART_STYLE_GUIDE 2.6): the wind-up warning red and the flinch blue
const RESERVED = [
  [0xff, 0x3a, 0x3a],
  [0x60, 0xa0, 0xff],
];
const hex = (px, i) => [px[i], px[i + 1], px[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('');
/** share of pixels whose opacity differs between two frames, over the opaque pixels of the first */
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

describe('enemy & boss release art (src/art-release/enemy)', () => {
  it('the minimal set keeps the names the current code draws (enemy.<kind>.0 / .1)', () => {
    for (const kind of MINIMAL) {
      for (const i of [0, 1]) expect(files, `enemy.${kind}.${i}`).toContain(`enemy.${kind}.${i}.png`);
    }
  });

  it('every expected frame exists, and nothing else is in the folder', () => {
    for (const name of expected.keys()) expect(files, name).toContain(`${name}.png`);
    const extra = files.filter((f) => !expected.has(f.replace(/\.png$/, '')));
    expect(extra).toEqual([]);
    expect(files.length).toBe(expected.size);
  });

  it('sizes: one frame size per character (the tendril is its own 32×48 sprite)', () => {
    for (const [name, size] of expected) {
      const { w, h } = decode(name);
      expect([w, h], name).toEqual(size);
    }
  });

  it('8-bit RGBA, alpha only 0 or 255 (no soft edges), and never empty', () => {
    for (const name of expected.keys()) {
      const { w, h, depth, type, px } = decode(name);
      expect([depth, type], name).toEqual([8, 6]);
      let solid = 0;
      let soft = 0;
      for (let i = 3; i < w * h * 4; i += 4) {
        if (px[i] !== 0 && px[i] !== 255) soft++;
        if (px[i]) solid++;
      }
      expect(soft, `${name}: half-transparent pixels`).toBe(0);
      expect(solid, name).toBeGreaterThan(20);
    }
  });

  it('frames of the same action differ from one another (every action moves)', () => {
    for (const [kind, k] of Object.entries(KINDS)) {
      for (const [action, n] of Object.entries(k.actions)) {
        if (n < 2) continue;
        const pics = new Set();
        for (let i = 0; i < n; i++) pics.add(readFileSync(new URL(`enemy.${kind}.${action}.${i}.png`, DIR)).toString('base64'));
        expect(pics.size, `${kind} ${action}`).toBe(n);
      }
      // the minimal pair alternates: standing and moving must differ
      if (MINIMAL.includes(kind)) {
        expect(readFileSync(new URL(`enemy.${kind}.0.png`, DIR)).equals(readFileSync(new URL(`enemy.${kind}.1.png`, DIR))), kind).toBe(false);
      }
    }
  });

  it('feet at the bottom: every standing frame touches the bottom two rows (shots excepted)', () => {
    for (const name of expected.keys()) {
      if (name.startsWith('enemy.shot.')) continue;
      // in the air on purpose: the beast's leap, the slime's hop and lunge; the final boss hovers
      // (its tendrils lift off the ground while it winds up a slam, reach out sideways for a volley,
      // tuck up under the ring for a charge, transform, or fall apart)
      if (/^enemy\.(beast\.attack\.0|slime\.(move\.[12]|attack\.0)|boss_source\.(windup_(slam|volley|charge)\.\d|transform\.[12]|defeat\.3))$/.test(name)) continue;
      const { w, h, px } = decode(name);
      let lowest = -1;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (px[(y * w + x) * 4 + 3]) lowest = y;
      expect(lowest, `${name}: on the ground line`).toBeGreaterThanOrEqual(h - 2);
    }
  });

  it('colours: only the ramps of the design (no colour outside them), none near the reserved cue colours', () => {
    for (const c of RESERVED) expect(RAMP_COLOURS.has(c.map((v) => v.toString(16).padStart(2, '0')).join(''))).toBe(false);
    for (const name of expected.keys()) {
      const { px } = decode(name);
      const off = new Set();
      let near = 0;
      for (let i = 0; i < px.length; i += 4) {
        if (!px[i + 3]) continue;
        const h = hex(px, i);
        if (!RAMP_COLOURS.has(h)) off.add(h);
        for (const [r, g, b] of RESERVED) if (Math.abs(px[i] - r) + Math.abs(px[i + 1] - g) + Math.abs(px[i + 2] - b) < 60) near++;
      }
      expect([...off], `${name}: colours outside the ramps`).toEqual([]);
      expect(near, `${name}: pixels close to the warning red / flinch blue`).toBe(0);
    }
  });

  it('outline: every outer edge pixel is a tone-0 colour (shots excepted: their glow rims are lit)', () => {
    for (const name of expected.keys()) {
      if (name.startsWith('enemy.shot.')) continue;
      const { w, h, px } = decode(name);
      const a = (x, y) => px[(y * w + x) * 4 + 3] > 0;
      let bad = 0;
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          if (!a(x, y)) continue;
          const edge = [
            [1, 0],
            [-1, 0],
            [0, 1],
            [0, -1],
          ].some(([dx, dy]) => {
            const X = x + dx;
            const Y = y + dy;
            return X >= 0 && Y >= 0 && X < w && Y < h && !a(X, Y);
          });
          if (edge && !OUTLINE_COLOURS.has(hex(px, (y * w + x) * 4))) bad++;
        }
      }
      expect(bad, `${name}: outer edge pixels that are not tone 0`).toBe(0);
    }
  });

  it('the minimal set is byte-identical to the frames it mirrors (frames.json "minimal")', () => {
    const fj = JSON.parse(readFileSync(new URL('../../docs/art-release/enemy/frames.json', import.meta.url), 'utf8'));
    expect(Object.keys(fj.minimal).length).toBe(MINIMAL.length * 2);
    for (const [copy, src] of Object.entries(fj.minimal)) {
      expect(readFileSync(new URL(`${copy}.png`, DIR)).equals(readFileSync(new URL(`${src}.png`, DIR))), `${copy} = ${src}`).toBe(true);
    }
  });

  it('boss wind-ups show by pose: every wind-up frame changes the silhouette by 20% or more vs idle', () => {
    for (const [kind, k] of Object.entries(KINDS)) {
      if (!kind.startsWith('boss_')) continue;
      for (const [action, n] of Object.entries(k.actions)) {
        if (!action.startsWith('windup_')) continue;
        for (let i = 0; i < n; i++) {
          const c = silhouetteChange(`enemy.${kind}.idle.0`, `enemy.${kind}.${action}.${i}`);
          expect(c, `${kind} ${action}.${i}: silhouette change vs idle.0`).toBeGreaterThanOrEqual(0.2);
        }
      }
    }
  });

  it('wind-ups of different patterns are different poses (no frame reused between patterns)', () => {
    for (const [kind, k] of Object.entries(KINDS)) {
      if (!kind.startsWith('boss_')) continue;
      const wind = Object.keys(k.actions).filter((a) => a.startsWith('windup_'));
      const atk = Object.keys(k.actions).filter((a) => a.startsWith('attack_'));
      for (const a of wind) {
        for (const b of [...wind, ...atk]) {
          if (b === a || b === a.replace('windup_', 'attack_')) continue;
          for (let i = 0; i < 2; i++) {
            for (let j = 0; j < 2; j++) {
              const c = silhouetteChange(`enemy.${kind}.${a}.${i}`, `enemy.${kind}.${b}.${j}`);
              expect(c, `${kind} ${a}.${i} vs ${b}.${j}`).toBeGreaterThanOrEqual(0.08);
            }
          }
        }
      }
    }
  });
});
