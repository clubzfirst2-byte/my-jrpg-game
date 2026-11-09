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
      // (its tendrils lift off the ground while it winds up a slam, transforms, or falls apart)
      if (/^enemy\.(beast\.attack\.0|slime\.(move\.[12]|attack\.0)|boss_source\.(windup_slam\.\d|transform\.[12]|defeat\.3))$/.test(name)) continue;
      const { w, h, px } = decode(name);
      let lowest = -1;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (px[(y * w + x) * 4 + 3]) lowest = y;
      expect(lowest, `${name}: on the ground line`).toBeGreaterThanOrEqual(h - 2);
    }
  });
});
