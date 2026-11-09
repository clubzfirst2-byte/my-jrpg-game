// @ts-check
// v1.0 (C5-C7): placeholder art (仮) for 淀みの源 (the final boss) and the small 星環 on the beach,
// drawn with the placeholder palette until the release art (art/enemy-release: enemy.boss_source.*,
// 128×128 art pixels = 64×64 game pixels, front-facing) replaces it under the same names.
// Pure: rows of palette keys, like placeholderArt.js.

/** @param {number} w @param {number} h @param {string} fill */
const grid = (w, h, fill) => Array.from({ length: h }, () => Array(w).fill(fill));
/** @param {string[][]} g */
const toRows = (g) => g.map((r) => r.join(''));

/** The release art's actions for the source (docs/art-release/enemy/frames.json, kind boss_source). */
export const SOURCE_ACTIONS = Object.freeze({
  idle: 2,
  idle2: 2,
  windup_volley: 2,
  attack_volley: 2,
  windup_ring: 2,
  attack_ring: 2,
  windup_slam: 2,
  attack_slam: 2,
  windup_charge: 2,
  attack_charge: 2,
  hurt: 1,
  transform: 4,
  defeat: 6,
});

/**
 * @typedef {object} SourcePose
 * @property {'open' | 'narrow' | 'wide' | 'closed'} eye
 * @property {number} holes   seats (holes in the ring) shown open / lit: 0..4
 * @property {boolean} [turned]  the ring turned back the right way (staggered): the holes glow cyan
 * @property {boolean} [cracked] phase 2: cracks with light leaking through
 * @property {number} [fade]    0..1 purified away
 * @property {number} [bob]     0 / 1 px
 * @property {boolean} [flash]  an attack going off: bright rim
 */

/**
 * The inverted ring: a 64 × 64 frame, the ring floating above tendrils that reach the ground (feet
 * at the bottom middle). Grey faded stone (褪せた星環) around murk, one great eye in the middle,
 * four holes (the seats) at north, east, south, west.
 * @param {SourcePose} pose
 */
export function sourceSprite(pose) {
  const W = 64;
  const H = 64;
  const g = grid(W, H, '.');
  const bob = pose.bob ?? 0;
  const cx = 31.5;
  const cy = 27.5 + bob;
  const fade = pose.fade ?? 0;
  const keep = (/** @type {number} */ x, /** @type {number} */ y) => fade === 0 || ((x * 7 + y * 13) % 10) / 10 >= fade;
  // Tendrils of murk from the ring down to the ground.
  for (const [x0, sway] of [[22, -1], [31, 1], [41, 1]]) {
    for (let y = 46 + bob; y < H; y++) {
      const x = Math.round(x0 + sway * Math.sin((y + bob * 3) / 4) * 1.5);
      if (!keep(x, y)) continue;
      g[y][x] = 'Z';
      if (y < H - 4) g[y][x + 1] = 'z';
    }
  }
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const d = Math.hypot(x - cx, (y - cy) * 1.08);
      if (d > 22.5 || !keep(x, y)) continue;
      if (d > 21.5) g[y][x] = 'k';
      else if (d > 15.5) {
        // The stone of the ring: light from the upper left.
        const light = x - cx + (y - cy) < -10;
        g[y][x] = light ? 'v' : (x * 3 + y * 5) % 9 === 0 ? 'Q' : 'B';
        if (pose.flash && d > 20.5) g[y][x] = 'O';
      } else if (d > 14.5) g[y][x] = 'k';
      else g[y][x] = (x + y * 2) % 7 === 0 ? 'z' : 'Z'; // murk inside
    }
  }
  // Cracks (phase 2).
  if (pose.cracked) {
    for (const [x0, y0, dx, dy] of [[14, 18, 1, 1], [46, 34, 1, -1], [40, 10, -1, 1]]) {
      for (let k = 0; k < 6; k++) {
        const x = x0 + dx * k;
        const y = y0 + bob + dy * Math.floor(k / 2);
        if (g[y]?.[x] && g[y][x] !== '.' && keep(x, y)) g[y][x] = k % 2 ? 'O' : 'j';
      }
    }
  }
  // The four seats: holes in the ring (N, E, S, W). Open ones are dark pits; lit ones glow.
  const seats = [[cx, cy - 18.5], [cx + 18.5, cy], [cx, cy + 18.5], [cx - 18.5, cy]];
  seats.forEach(([sx, sy], k) => {
    for (let y = Math.floor(sy - 3); y <= Math.ceil(sy + 3); y++) {
      for (let x = Math.floor(sx - 3); x <= Math.ceil(sx + 3); x++) {
        const d = Math.hypot(x - sx, y - sy);
        if (d > 3 || !g[y] || !keep(x, y)) continue;
        if (d > 2.2) g[y][x] = 'k';
        else g[y][x] = pose.turned ? (d < 1.2 ? 'X' : 'I') : k < pose.holes ? (d < 1.2 ? 'O' : 'j') : 'D';
      }
    }
  });
  // The eye.
  const eh = { open: 5, narrow: 2, wide: 7, closed: 0 }[pose.eye];
  for (let y = Math.floor(cy - 8); y <= Math.ceil(cy + 8); y++) {
    for (let x = Math.floor(cx - 11); x <= Math.ceil(cx + 11); x++) {
      if (!keep(x, y)) continue;
      const nx = (x - cx) / 10.5;
      const ny = (y - cy) / Math.max(0.6, eh);
      if (eh === 0) {
        if (Math.abs(y - cy) < 0.6 && Math.abs(nx) < 1) g[y][x] = 'k';
        continue;
      }
      const d = nx * nx + ny * ny;
      if (d > 1) continue;
      g[y][x] = d > 0.75 ? 'k' : 'O';
      const p = Math.hypot(x - cx, y - cy);
      if (p < Math.min(4, eh)) g[y][x] = pose.turned ? 'I' : p < 1.5 ? 'X' : 'j';
    }
  }
  return toRows(g);
}

/** Every placeholder frame of the source, by its release name (enemy.boss_source.<action>.<frame>). */
export function sourceFrames() {
  /** @type {Record<string, string[]>} */
  const out = {};
  const attackHoles = { volley: 1, ring: 2, slam: 3, charge: 4 };
  for (const [action, n] of Object.entries(SOURCE_ACTIONS)) {
    for (let f = 0; f < n; f++) {
      // As in the release art: idle / idle2 have the eye wide open (shown while staggered, the ring
      // turned back), hurt has it closed (shown while inverted, at rest).
      /** @type {SourcePose} */
      let pose = { eye: 'wide', holes: 4, turned: true, bob: f % 2 };
      if (action === 'idle2') pose = { ...pose, cracked: true };
      else if (action.startsWith('windup_')) pose = { eye: 'narrow', holes: attackHoles[/** @type {'volley'} */ (action.slice(7))], bob: 0 };
      else if (action.startsWith('attack_')) pose = { eye: 'wide', holes: attackHoles[/** @type {'volley'} */ (action.slice(7))], bob: 0, flash: f === 0 };
      else if (action === 'hurt') pose = { eye: 'closed', holes: 0 };
      else if (action === 'transform') pose = { eye: f % 2 ? 'narrow' : 'wide', holes: f, cracked: f >= 2, flash: f === 3 };
      else if (action === 'defeat') pose = { eye: f < 2 ? 'wide' : 'closed', holes: 4, turned: true, fade: f / 6 };
      out[`enemy.boss_source.${action}.${f}`] = sourceSprite(pose);
    }
  }
  return out;
}

/**
 * The small 星環 on the beach (C5): a ring of standing stones, 24 × 26. Lit (the gate is open): its
 * inside glows the blue of the hero's pendant.
 * @param {boolean} lit
 */
export function starRingSprite(lit) {
  const W = 24;
  const H = 26;
  const g = grid(W, H, '.');
  const cx = 11.5;
  const cy = 12;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const d = Math.hypot(x - cx, (y - cy) * 1.0);
      if (y >= H - 3) {
        // The foot stones in the sand.
        if (x >= 3 && x <= 20 && (y === H - 1 || x === 3 || x === 20)) g[y][x] = 'k';
        else if (x > 3 && x < 20) g[y][x] = y === H - 3 ? 'r' : 'm';
        continue;
      }
      if (d > 11.5) continue;
      if (d > 10.5) g[y][x] = 'k';
      else if (d > 7.5) g[y][x] = x - cx + (y - cy) < -6 ? 'R' : (x + y) % 5 === 0 ? 'm' : 'r';
      else if (d > 6.5) g[y][x] = 'k';
      else if (lit) g[y][x] = d < 2.5 ? 'X' : d < 4.5 ? 'W' : 'I';
    }
  }
  // Four small marks on the ring (the seats, in miniature).
  for (const [x, y] of [[11, 2], [21, 12], [11, 21], [2, 12]]) {
    g[y][x] = lit ? 'I' : 'Q';
    g[y][x + 1] = lit ? 'I' : 'Q';
  }
  return toRows(g);
}
