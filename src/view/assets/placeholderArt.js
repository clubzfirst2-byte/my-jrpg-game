// @ts-check
// Placeholder pixel art, drawn in code with one shared palette (DESIGN.md "ドット絵素材の方針").
// Pure data + pixel functions (no PixiJS, no DOM): unit-testable.
// Production art will replace these frames with the same logical names (see placeholderPack.js).

/** Shared palette. '.' = transparent. */
export const PALETTE = Object.freeze({
  k: '#1a1c2c', // outline
  g: '#3f8a46', // grass
  G: '#5fb455', // grass light
  d: '#2c6a3e', // grass dark
  p: '#c49a66', // path
  P: '#9c7448', // path dark
  q: '#dcbc8a', // path light
  w: '#3b74c4', // water
  W: '#7fb8ee', // water light
  b: '#2a4f96', // water deep
  r: '#8b9bb4', // rock
  R: '#c3cede', // rock light
  m: '#5a6988', // rock dark
  t: '#7a4a32', // trunk
  T: '#4e2f22', // trunk dark
  l: '#3c8f4a', // leaves
  L: '#2a6338', // leaves dark
  h: '#7fcc5e', // leaves light
  s: '#f2c49b', // skin
  e: '#1a1c2c', // eyes
  H: '#6b3d2a', // hair
  c: '#2f7fb8', // tunic
  C: '#1f5486', // tunic dark
  y: '#e8b84a', // belt
  n: '#5a4a3a', // trousers
  o: '#3a2a20', // boots
  E: '#8a5a3c', // earth (cliff face)
  F: '#5e3b28', // earth dark
  f: '#a8744c', // earth light
  B: '#9a9488', // ruin brick
  Q: '#5f5a52', // ruin grout / dark
  v: '#c4beb0', // ruin light
  X: '#ffffff', // white (tinted at runtime)
  z: '#6a4590', // murk (enemy body)
  Z: '#3a2552', // murk dark
  j: '#9b6fc4', // murk light
  i: '#ff5d5d', // enemy eyes
  O: '#c9a2f2', // orb glow
  a: '#d8d2c4', // steel (sword, arrow head)
  A: '#8a8270', // wood / shield rim
  u: '#e2cf94', // sand
  U: '#c4ac70', // sand dark
  V: '#f2e4ba', // sand light
  Y: '#ffd75e', // gold
  N: '#8a5a2c', // chest wood
  K: '#ff8a3c', // fire
  J: '#ffe27a', // fire light
  S: '#c8c8d0', // smoke
  D: '#0e0a12', // cave darkness
  I: '#7fe8ff', // rune glow
  // P10.2: the seasons.
  1: '#d9822b', // autumn leaves
  2: '#a5481f', // autumn leaves dark
  3: '#f0c04a', // autumn leaves light
  4: '#f4f8ff', // snow
  5: '#c9d6ea', // snow shade
  6: '#f6b8cf', // blossom
  7: '#d97ea4', // blossom dark
  8: '#b0a050', // dry grass
  9: '#857a3a', // dry grass dark
  M: '#cfc070', // dry grass light
});

// Player frames (16x16). Only down / up / right are drawn; left is right mirrored.
const PLAYER_HEAD_DOWN = [
  '................',
  '......kkkk......',
  '....kkHHHHkk....',
  '...kHHHHHHHHk...',
  '...kHHHHHHHHk...',
  '...kHssssssHk...',
  '...kssessessk...',
  '...kssssssssk...',
  '....kssssssk....',
];
const PLAYER_HEAD_UP = [
  '................',
  '......kkkk......',
  '....kkHHHHkk....',
  '...kHHHHHHHHk...',
  '...kHHHHHHHHk...',
  '...kHHHHHHHHk...',
  '...kHHHHHHHHk...',
  '...kHHHHHHHHk...',
  '....kssssssk....',
];
const PLAYER_BODY_FRONT = ['...kCccccccCk...', '..ksCccccccCsk..', '..ksCyyyyyyCsk..', '...kCccccccCk...'];
const LEGS_FRONT = [
  ['...knnnkknnnk...', '...knnk..knnk...', '...kook..kook...'],
  ['...knnnkknnnk...', '...knnk..kook...', '...kook.........'],
  ['...knnnkknnnk...', '...kook..knnk...', '.........kook...'],
];
const PLAYER_RIGHT_TOP = [
  '................',
  '.....kkkkk......',
  '....kHHHHHkk....',
  '...kHHHHHHHHk...',
  '...kHHHHHHHHk...',
  '...kHHHHsssk....',
  '...kHHHssesk....',
  '...kHHsssssk....',
  '....kssssk......',
  '....kCcccck.....',
  '....kCcscck.....',
  '....kyysyyk.....',
  '....kCcccck.....',
];
const LEGS_RIGHT = [
  ['....knnnnk......', '....knk.knk.....', '....kok.kok.....'],
  ['....knnnnk......', '.....knnk.......', '.....kook.......'],
  ['....knnnnk......', '...knk..knk.....', '...kok...kok....'],
];

/**
 * Player frames: 3 per direction (0 = stand, 1/2 = walk).
 * @returns {Record<string, string[]>}
 */
export function playerFrames() {
  /** @type {Record<string, string[]>} */
  const frames = {};
  for (let f = 0; f < 3; f++) {
    frames[`player.walk.down.${f}`] = [...PLAYER_HEAD_DOWN, ...PLAYER_BODY_FRONT, ...LEGS_FRONT[f]];
    frames[`player.walk.up.${f}`] = [...PLAYER_HEAD_UP, ...PLAYER_BODY_FRONT, ...LEGS_FRONT[f]];
    frames[`player.walk.right.${f}`] = [...PLAYER_RIGHT_TOP, ...LEGS_RIGHT[f]];
    frames[`player.walk.left.${f}`] = mirror(frames[`player.walk.right.${f}`]);
  }
  return frames;
}

/** @param {string[]} rows */
export function mirror(rows) {
  return rows.map((r) => [...r].reverse().join(''));
}

/** Small deterministic RNG (mulberry32) so placeholder art is identical on every run. @param {number} seed */
export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * @param {number} w @param {number} h @param {string} fill
 * @returns {string[][]}
 */
function grid(w, h, fill) {
  return Array.from({ length: h }, () => Array(w).fill(fill));
}

/** @param {string[][]} g */
const toRows = (g) => g.map((r) => r.join(''));

/** @param {number} seed */
export function grassTile(seed) {
  const g = grid(16, 16, 'g');
  const rand = rng(seed);
  for (let i = 0; i < 10; i++) {
    const x = Math.floor(rand() * 15);
    const y = Math.floor(rand() * 15) + 1;
    g[y][x] = 'd';
    if (rand() < 0.7) g[y - 1][x] = 'G'; // tuft: light tip above dark base
    if (rand() < 0.4 && x < 15) g[y][x + 1] = 'G';
  }
  return toRows(g);
}

export function pathTile() {
  const g = grid(16, 16, 'p');
  const rand = rng(11);
  for (let i = 0; i < 14; i++) {
    const x = Math.floor(rand() * 16);
    const y = Math.floor(rand() * 16);
    g[y][x] = rand() < 0.5 ? 'P' : 'q';
  }
  return toRows(g);
}

/** @param {number} frame 0..1 (wave offset) */
export function waterTile(frame) {
  const g = grid(16, 16, 'w');
  for (let y = 0; y < 16; y++) {
    for (let x = 0; x < 16; x++) {
      if ((x + y * 3) % 13 === 0) g[y][x] = 'b';
    }
  }
  const off = frame * 4;
  for (const [y, x0] of [[3, 2], [8, 9], [13, 4]]) {
    for (let i = 0; i < 4; i++) g[y][(x0 + off + i) % 16] = 'W';
  }
  return toRows(g);
}

export function rockSprite() {
  // 16x14 boulder, lit from the top-left.
  const w = 16;
  const h = 14;
  const g = grid(w, h, '.');
  const cx = 7.5;
  const cy = 8;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const dx = (x - cx) / 7.2;
      const dy = (y - cy) / 6;
      const d = dx * dx + dy * dy;
      if (d > 1) continue;
      if (d > 0.78) g[y][x] = 'k';
      else if (dx + dy < -0.6) g[y][x] = 'R';
      else if (dx + dy > 0.5 || y > 11) g[y][x] = 'm';
      else g[y][x] = 'r';
    }
  }
  return toRows(g);
}

export function treeSprite() {
  // 16x28: round canopy over a short trunk. Anchored at the trunk base.
  const w = 16;
  const h = 28;
  const g = grid(w, h, '.');
  const rand = rng(5);
  for (let y = 0; y < 20; y++) {
    for (let x = 0; x < w; x++) {
      const dx = (x - 7.5) / 7.6;
      const dy = (y - 9.5) / 9.6;
      const d = dx * dx + dy * dy;
      if (d > 1) continue;
      if (d > 0.84) g[y][x] = 'k';
      else if (dx + dy < -0.55) g[y][x] = 'h';
      else if (dx + dy > 0.45) g[y][x] = 'L';
      else g[y][x] = rand() < 0.12 ? 'L' : 'l';
    }
  }
  for (let y = 19; y < h; y++) {
    for (let x = 6; x <= 9; x++) {
      if (y >= 26 && (x === 6 || x === 9)) continue;
      g[y][x] = x === 6 ? 'k' : x === 9 ? 'k' : x === 8 ? 'T' : 't';
    }
  }
  g[h - 1][5] = 'k';
  g[h - 1][10] = 'k';
  for (let x = 6; x <= 9; x++) g[h - 1][x] = 'k';
  return toRows(g);
}

/**
 * Earth cliff face segment, 16 x h (h = 4 or 8). Faces are stacked from segments:
 * `top` adds the grass lip hanging over the edge, `bottom` adds the dark base where it meets the ground.
 */
export function earthFace(h, top, bottom = false) {
  const g = grid(16, h, 'E');
  const rand = rng(31 + h * 3 + (top ? 1 : 0) + (bottom ? 2 : 0));
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < 16; x++) {
      const r = rand();
      if (r < 0.12) g[y][x] = 'f';
      else if (r < 0.24) g[y][x] = 'F';
    }
  }
  // Strata line every 8px for a layered look.
  if (h >= 8) for (let x = 0; x < 16; x++) if ((x + 1) % 5 !== 0) g[5][x] = 'F';
  if (top) {
    for (let x = 0; x < 16; x++) {
      g[0][x] = 'G';
      g[1][x] = x % 3 === 0 ? 'E' : 'd';
    }
  }
  if (bottom) {
    for (let x = 0; x < 16; x++) {
      g[h - 1][x] = 'k';
      if (h > 2) g[h - 2][x] = 'F';
    }
  }
  return toRows(g);
}

/** Ruin wall face (bricks), 16 x h. `top` adds a light capstone row. */
export function ruinFace(h, top, bottom = false) {
  const g = grid(16, h, 'B');
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < 16; x++) {
      if (y % 4 === 3) g[y][x] = 'Q';
      else if ((x + (Math.floor(y / 4) % 2) * 4) % 8 === 7) g[y][x] = 'Q';
    }
  }
  if (top) for (let x = 0; x < 16; x++) g[0][x] = 'v';
  if (bottom) for (let x = 0; x < 16; x++) g[h - 1][x] = 'k';
  return toRows(g);
}

export function ruinFloorTile() {
  const g = grid(16, 16, 'v');
  for (let y = 0; y < 16; y++) {
    for (let x = 0; x < 16; x++) {
      if (y % 8 === 7) g[y][x] = 'Q';
      else if ((x + (Math.floor(y / 8) % 2) * 8) % 16 === 15) g[y][x] = 'Q';
      else if ((x * 7 + y * 3) % 23 === 0) g[y][x] = 'B';
    }
  }
  return toRows(g);
}

/**
 * Stone stairs for a north-rising ramp: 16 wide, 16 + rise tall.
 * @param {number} rise height gained across the tile (one level)
 */
export function rampSprite(rise) {
  const h = 16 + rise;
  const g = grid(16, h, 'r');
  for (let y = 0; y < h; y++) {
    const inStep = y % 6;
    for (let x = 0; x < 16; x++) {
      if (inStep < 2) g[y][x] = 'R'; // tread edge (lit)
      else if (inStep === 5) g[y][x] = 'm'; // riser shadow
      if (x === 0 || x === 15) g[y][x] = 'k';
      else if (x === 1 || x === 14) g[y][x] = 'm';
    }
  }
  return toRows(g);
}

/** Soft oval shadow, drawn with low alpha under characters. */
export function shadowSprite() {
  const g = grid(12, 5, '.');
  for (let y = 0; y < 5; y++) {
    for (let x = 0; x < 12; x++) {
      const dx = (x - 5.5) / 6;
      const dy = (y - 2) / 2.6;
      if (dx * dx + dy * dy <= 1) g[y][x] = 'k';
    }
  }
  return toRows(g);
}

/** Glider: a striped cloth canopy with two cords down to the player's shoulders. 22 x 10. */
export function gliderSprite() {
  const w = 22;
  const h = 10;
  const g = grid(w, h, '.');
  // Canopy: upper half-ellipse, rows 0..4.
  for (let y = 0; y < 5; y++) {
    for (let x = 0; x < w; x++) {
      const dx = (x - 10.5) / 11;
      const dy = (y - 5) / 5.2;
      const d = dx * dx + dy * dy;
      if (d > 1) continue;
      if (d > 0.72 || y === 4) g[y][x] = 'k';
      else g[y][x] = Math.floor((x + 1) / 4) % 2 === 0 ? 'y' : 'c';
    }
  }
  // Cords from the canopy edges to the shoulders.
  const cords = [
    [3, 5], [4, 6], [5, 7], [6, 8], [7, 9],
    [18, 5], [17, 6], [16, 7], [15, 8], [14, 9],
  ];
  for (const [x, y] of cords) g[y][x] = 'k';
  return toRows(g);
}

/**
 * Swimming frames: the walk frame's head and shoulders (top 11 rows) above two ripple rows.
 * 16 x 13, anchored at the water line. 2 frames per direction (ripples shift).
 * @returns {Record<string, string[]>}
 */
export function swimFrames() {
  const walk = playerFrames();
  /** @type {Record<string, string[]>} */
  const frames = {};
  for (const dir of ['down', 'up', 'left', 'right']) {
    for (let f = 0; f < 2; f++) {
      const top = walk[`player.walk.${dir}.0`].slice(0, 11);
      const ripple = f === 0 ? ['..WW.wwwwww.WW..', '.W..........W...'] : ['.WW.wwwwww.WW...', '..W..........W..'];
      frames[`player.swim.${dir}.${f}`] = [...top, ...ripple];
    }
  }
  return frames;
}

// ---------------------------------------------------------------- P3 combat placeholder art

/** Murk beast: a low, hunched blob with red eyes. 16 x 13, 2 frames. */
export function beastFrames() {
  const f0 = [
    '................',
    '.....kkkkkk.....',
    '...kkzzzzzzkk...',
    '..kzzjjzzjjzzk..',
    '.kzzjzzzzzzjzzk.',
    '.kzzziikkiizzzk.',
    'kzzzziikkiizzzzk',
    'kzzzzzzzzzzzzzzk',
    'kZzzzzzzzzzzzzZk',
    'kZZzzzzzzzzzzZZk',
    '.kZZZZZZZZZZZZk.',
    '..kZk.kZZk.kZk..',
    '..kk...kk...kk..',
  ];
  const f1 = [...f0.slice(0, 11), '.kZk..kZZk..kZk.', '.kk....kk....kk.'];
  return { 'enemy.beast.0': f0, 'enemy.beast.1': f1 };
}

/** Murk archer: a hooded figure holding a glowing focus. 14 x 16, 2 frames. */
export function archerFrames() {
  const f0 = [
    '.....kkkk.....',
    '....kzzzzk....',
    '...kzZZZZzk...',
    '...kZiZZiZk...',
    '...kZZZZZZk...',
    '....kzzzzk....',
    '...kzjzzjzk...',
    '..kzzjzzjzzk..',
    '..kzzzzzzzzkOk',
    '..kzzzzzzzzkOk',
    '..kZzzzzzzZk..',
    '..kZzzzzzzZk..',
    '..kZZzzzzZZk..',
    '...kZZZZZZk...',
    '...kZk..kZk...',
    '...kk....kk...',
  ];
  const f1 = [...f0.slice(0, 14), '..kZk....kZk..', '..kk......kk..'];
  return { 'enemy.archer.0': f0, 'enemy.archer.1': f1 };
}

/**
 * v1.0 澱だまり (slime): a murk jelly mound with a glowing core and two eyes. 16 x 14 (the release
 * art's 32 x 28 at 2 art pixels per game pixel), 2 frames: resting, and stretched mid-hop.
 */
export function slimeFrames() {
  /** @param {number} rx @param {number} ry @param {number} cy */
  const blob = (rx, ry, cy) => {
    const g = grid(16, 14, '.');
    for (let y = 0; y < 14; y++) {
      for (let x = 0; x < 16; x++) {
        const dx = (x - 7.5) / rx;
        const dy = (y - cy) / ry;
        const d = dx * dx + dy * dy;
        if (d > 1 || y > 12) continue;
        g[y][x] = d > 0.7 ? 'k' : dy < -0.3 && dx < 0 ? 'j' : y >= cy + ry * 0.4 ? 'Z' : 'z';
      }
    }
    const top = Math.round(cy - ry * 0.3);
    g[top][5] = g[top][10] = 'i';
    g[top + 2][7] = g[top + 2][8] = 'O';
    for (let x = 1; x < 15; x++) if (g[13][x] === '.' && x % 3 === 0) g[13][x] = 'Z'; // the murk seeping out
    return toRows(g);
  };
  return { 'enemy.slime.0': blob(7.5, 6, 8.5), 'enemy.slime.1': blob(6, 7, 7) };
}

/**
 * v1.0 遺跡の番兵 (sentinel): a squared stone body with a bronze band, a domed head with a glowing
 * slit, one big stone fist. 20 x 28 (the release art's 40 x 56), 2 frames: standing, and a step.
 */
export function sentinelFrames() {
  /** @param {number} step */
  const make = (step) => {
    const g = grid(20, 28, '.');
    const fill = (/** @type {number} */ x0, /** @type {number} */ y0, /** @type {number} */ x1, /** @type {number} */ y1, /** @type {string} */ c) => {
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) g[y][x] = x === x0 || x === x1 || y === y0 || y === y1 ? 'k' : c;
    };
    fill(5, 1, 13, 7, 'R'); // domed head
    g[1][5] = g[1][13] = '.';
    for (let x = 7; x <= 11; x++) g[4][x] = 'O'; // the eye slit
    fill(3, 7, 15, 18, 'r'); // body
    for (let x = 4; x <= 14; x++) g[12][x] = 'N'; // bronze band
    for (let y = 9; y <= 16; y++) g[y][4] = 'R';
    fill(14, 9, 19, 19, 'm'); // the big fist arm
    for (let y = 10; y <= 18; y++) g[y][15] = 'r';
    fill(5, 18, 8, 27 - step, 'm'); // legs (one lifted in the step)
    fill(10, 18, 13, 26 + step, 'm');
    return toRows(g);
  };
  return { 'enemy.sentinel.0': make(0), 'enemy.sentinel.1': make(1) };
}

/** Sword slash: a white crescent pointing right (+x); rotated at runtime. 16 x 20. */
export function slashSprite() {
  const w = 16;
  const h = 20;
  const g = grid(w, h, '.');
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const d1 = Math.hypot(x - 2, y - 9.5);
      const d2 = Math.hypot(x + 2, y - 9.5);
      if (d1 < 13 && d2 > 13.5) g[y][x] = d1 > 11 ? 'X' : 'a';
    }
  }
  return toRows(g);
}

/** Arrow pointing right. 10 x 3. */
export function arrowSprite() {
  return ['.........k', 'AAAAAAAaak', '.........k'].map((r, i) => (i === 1 ? 'kAAAAAAaak' : r));
}

/** Enemy orb. 6 x 6. */
export function orbSprite() {
  return ['..kk..', '.kOOk.', 'kOXXOk', 'kOXXOk', '.kOOk.', '..kk..'];
}

/** Shield seen from the front. 8 x 9. */
export function shieldSprite() {
  return ['.kkkkkk.', 'kAAAAAAk', 'kAccccAk', 'kAcyycAk', 'kAcyycAk', 'kAccccAk', '.kAccAk.', '..kAAk..', '...kk...'];
}

/** Bow, vertical (string on the left). 5 x 12. */
export function bowSprite() {
  return ['..kk.', '.kAk.', 'k.kAk', 'k..kA', 'k..kA', 'k..kA', 'k..kA', 'k..kA', 'k..kA', 'k.kAk', '.kAk.', '..kk.'];
}

// ---- P3.5 island features ----

export function sandTile() {
  const g = grid(16, 16, 'u');
  const rand = rng(23);
  for (let i = 0; i < 16; i++) {
    const x = Math.floor(rand() * 16);
    const y = Math.floor(rand() * 16);
    g[y][x] = rand() < 0.5 ? 'U' : 'V';
  }
  return toRows(g);
}

/** 16x14 chest, closed or open (lid up, gold inside). @param {boolean} open */
export function chestSprite(open) {
  if (open) {
    return [
      '..kkkkkkkkkkkk..',
      '..kNNNNNNNNNNk..',
      '..kTTTTTTTTTTk..',
      '..kkkkkkkkkkkk..',
      '.kDDDDDDDDDDDDk.',
      '.kNNNNNNNNNNNNk.',
      '.kNNNNNNNNNNNNk.',
      '.kYYYYYYYYYYYYk.',
      '.kNNNNNkkNNNNNk.',
      '.kNNNNNkkNNNNNk.',
      '.kNNNNNNNNNNNNk.',
      '.kTTTTTTTTTTTTk.',
      '.kkkkkkkkkkkkkk.',
      '................',
    ];
  }
  return [
    '................',
    '................',
    '...kkkkkkkkkk...',
    '..kNNNNNNNNNNk..',
    '.kNNNNNNNNNNNNk.',
    '.kYYYYYYYYYYYYk.',
    '.kNNNNNkkNNNNNk.',
    '.kNNNNkYYkNNNNk.',
    '.kNNNNNkkNNNNNk.',
    '.kNNNNNNNNNNNNk.',
    '.kNNNNNNNNNNNNk.',
    '.kTTTTTTTTTTTTk.',
    '.kkkkkkkkkkkkkk.',
    '................',
  ];
}

/** 12x20 standing stone with a rune; lit (glowing) once activated. @param {boolean} lit */
export function checkpointSprite(lit) {
  const rune = lit ? 'I' : 'Q';
  return [
    '....kkkk....',
    '...kRRRrk...',
    '..kRRrrrmk..',
    '..kRrrrrmk..',
    `..kRr${rune}${rune}rmk..`,
    `..kr${rune}rr${rune}mk..`,
    `..kr${rune}rr${rune}mk..`,
    `..krr${rune}${rune}rmk..`,
    '..krrrrrmk..',
    `..krr${rune}rrmk..`,
    `..krr${rune}rrmk..`,
    '..krrrrrmk..',
    '..krrrrmmk..',
    '..krrrrmmk..',
    '..krrrrmmk..',
    '.kmrrrrmmmk.',
    '.kmmmmmmmmk.',
    'kkmmmmmmmmkk',
    'kmmmmmmmmmmk',
    'kkkkkkkkkkkk',
  ];
}

/** 16x14 campfire frames (logs + flame). */
export function campfireFrames() {
  const flame = [
    ['......kk........', '.....kKk........', '....kKJKk.......', '....kKJJKk......', '...kKJJJKk......', '...kKJJJJKk.....'],
    ['.......kk.......', '.......kKk......', '......kKJKk.....', '.....kKJJKk.....', '.....kKJJJKk....', '....kKJJJJKk....'],
  ];
  const logs = [
    '...kKJJJJJKk....',
    '..kkKKJJJKKkk...',
    '.kNNkKKKKKkNNk..',
    'kNNNNkkkkkNNNNk.',
    'kTNNNNNNNNNNNTk.',
    '.kkTTNNNNNTTkk..',
    '...kkkkkkkkk....',
    '................',
  ];
  return { 'obj.campfire.0': [...flame[0], ...logs], 'obj.campfire.1': [...flame[1], ...logs] };
}

/** 6x6 smoke puff (tinted / faded at runtime). */
export function smokeSprite() {
  return ['..SS..', '.SSSS.', 'SSSSSS', 'SSSSSS', '.SSSS.', '..SS..'];
}

/** 16x14 cave mouth drawn on a cliff face. */
export function caveSprite() {
  return [
    '....kkkkkkkk....',
    '...kFDDDDDDFk...',
    '..kFDDDDDDDDFk..',
    '.kFDDDDDDDDDDFk.',
    '.kFDDDDDDDDDDFk.',
    'kFDDDDDDDDDDDDFk',
    'kFDDDDDDDDDDDDFk',
    'kFDDDDDDDDDDDDFk',
    'kFDDDDDDDDDDDDFk',
    'kFDDDDDDDDDDDDFk',
    'kFDDDDDDDDDDDDFk',
    'kFDDDDDDDDDDDDFk',
    'kFDDDDDDDDDDDDFk',
    'kFDDDDDDDDDDDDFk',
  ];
}

/** 7x7 arrow marker pointing right (rotated at runtime) for landmarks off-screen. */
export function markerSprite() {
  return ['kk.....', 'kYkk...', 'kYYYkk.', 'kYYYYYk', 'kYYYkk.', 'kYkk...', 'kk.....'];
}

// ---- P4 environment ----

export function metalTile() {
  const g = grid(16, 16, 'r');
  for (let y = 0; y < 16; y++) {
    for (let x = 0; x < 16; x++) {
      if (x % 8 === 0 || y % 8 === 0) g[y][x] = 'm';
      else if ((x + y) % 8 === 2) g[y][x] = 'R';
    }
  }
  for (const [x, y] of [[2, 2], [10, 2], [2, 10], [10, 10]]) g[y][x] = 'k';
  return toRows(g);
}

/** 12x14 flame frames. */
export function fireFrames() {
  return {
    'fx.fire.0': [
      '.....kk.....',
      '....kKk.....',
      '....kKKk..k.',
      '...kKJKk.kKk',
      '..kKJJKkkKKk',
      '..kKJJJKKJKk',
      '.kKJJXJJJJKk',
      '.kKJXXXJJJKk',
      'kKJJXXXXJJKk',
      'kKJJXXXXJJKk',
      'kKKJJXXJJKKk',
      '.kKKJJJJKKk.',
      '..kkKKKKkk..',
      '....kkkk....',
    ],
    'fx.fire.1': [
      '......kk....',
      '.k...kKk....',
      'kKk..kKKk...',
      'kKk.kKJKk...',
      'kKKkKJJKKk..',
      'kKJKKJJJKk..',
      'kKJJJJXJJKk.',
      'kKJJJXXXJKk.',
      'kKJJXXXXJJKk',
      'kKJJXXXXJJKk',
      'kKKJJXXJJKKk',
      '.kKKJJJJKKk.',
      '..kkKKKKkk..',
      '....kkkk....',
    ],
  };
}

/** 16x12 thorny bush. */
export function brambleSprite() {
  return [
    '....k..kk..k....',
    '...kLk.kLk.kLk..',
    '..kLdLkLhLkLdLk.',
    '.kLLdLLLhLLLdLLk',
    'kLtLLhLkLLtLhLLk',
    'kLLLtLLLLtLLLLkk',
    'kLhLLLtLLLLhtLLk',
    'kLLtLhLLtLLLLtLk',
    '.kLLLLtLLLhLLLk.',
    '.kLtLLLLtLLLtLk.',
    '..kkLLkkkLLkkk..',
    '....kk...kk.....',
  ];
}

/** 12x18 shock crystal (glows). */
export function crystalSprite() {
  return [
    '.....kk.....',
    '....kIIk....',
    '....kIXk....',
    '...kIIXIk...',
    '...kIXXIk...',
    '..kIIXXIIk..',
    '..kIXXIIIk..',
    '..kIXIIIbk..',
    '..kIIIIIbk..',
    '..kIIIIbbk..',
    '..kIIIbbbk..',
    '...kIIbbk...',
    '...kIbbbk...',
    '..kmrrrrmk..',
    '.kmrRRRrrmk.',
    '.kmrrrrrmmk.',
    'kmmmmmmmmmmk',
    'kkkkkkkkkkkk',
  ];
}

/** 10x12 water jar. */
export function jarSprite() {
  return [
    '...kkkk...',
    '..kWWWWk..',
    '...kNNk...',
    '..kNNNNk..',
    '.kNfNNNNk.',
    'kNffNNNNNk',
    'kNfNWWNNNk',
    'kNNWbbWNNk',
    'kNNNWWNNNk',
    '.kNNNNNNk.',
    '..kTTTTk..',
    '...kkkk...',
  ];
}

/** 12x16 receiver pillar: dark rune, or lit when powered. @param {boolean} on */
export function receiverSprite(on) {
  const r = on ? 'I' : 'Q';
  return [
    '...kkkkkk...',
    '..kaaaaaak..',
    '..kmmmmmmk..',
    `..km${r}${r}${r}${r}mk..`,
    `..km${r}mm${r}mk..`,
    `..km${r}${r}${r}${r}mk..`,
    '..kmmmmmmk..',
    '..kmrrrrmk..',
    '..kmrRrrmk..',
    '..kmrrrrmk..',
    '..kmrrrrmk..',
    '..kmrrrrmk..',
    '.kmmrrrrmmk.',
    'kmmmmmmmmmmk',
    'kmmmmmmmmmmk',
    'kkkkkkkkkkkk',
  ];
}

/** 16x20 rune door stone. */
export function doorSprite() {
  return [
    '..kkkkkkkkkkkk..',
    '.kvvvvvvvvvvvvk.',
    'kvBBBBBBBBBBBBQk',
    'kvBBBBBQQBBBBBQk',
    'kvBBBBQIIQBBBBQk',
    'kvBBBQIBBIQBBBQk',
    'kvBBBQIBBIQBBBQk',
    'kvBBBBQIIQBBBBQk',
    'kvBBBBBQQBBBBBQk',
    'kvBBBBBBBBBBBBQk',
    'kvBBBBBBBBBBBBQk',
    'kvBBBBBQQBBBBBQk',
    'kvBBBBQIIQBBBBQk',
    'kvBBBBBQQBBBBBQk',
    'kvBBBBBBBBBBBBQk',
    'kvBBBBBBBBBBBBQk',
    'kvBBBBBBBBBBBBQk',
    'kQQQQQQQQQQQQQQk',
    'kQQQQQQQQQQQQQQk',
    'kkkkkkkkkkkkkkkk',
  ];
}

/** 12x16 brazier (stone bowl with a flame) frames. */
export function brazierFrames() {
  const base = [
    'kkkkkkkkkkkk',
    'kvBBBBBBBBQk',
    '.kBBBBBBBQk.',
    '..kBBBBBQk..',
    '...kBBBQk...',
    '...kBBBQk...',
    '..kvBBBBQk..',
    '..kkkkkkkk..',
  ];
  return {
    'obj.brazier.0': ['....kk......', '...kKk......', '...kKJk..k..', '..kKJJkkKk..', '..kKJXJKKk..', '.kKJXXJJKk..', '.kKJXXXJKk..', '.kKJJJJJKk..', ...base],
    'obj.brazier.1': ['......kk....', '......kKk...', '..k..kJKk...', '..kKkkJJKk..', '..kKKJXJKk..', '..kKJJXXJKk.', '..kKJXXXJKk.', '..kKJJJJJKk.', ...base],
  };
}

/** 14x8 burnt tree stump. */
export function stumpSprite() {
  return [
    '...kkkkkkkk...',
    '..kFFFFFFFFk..',
    '..kTFkFFkFTk..',
    '..kTTFFFFTTk..',
    '..kTTTkTTTTk..',
    '.kkTTTTTTTTkk.',
    'kTTkkTTTTkkTTk',
    '.kk..kkkk..kk.',
  ];
}

// ---- P6 items ----

/** 16x12 anvil. */
export function anvilSprite() {
  return [
    '.kkkkkkkkkkkkkk.',
    'kmRRRRRRRRRRRRmk',
    '.kmmrrrrrrrrrmk.',
    '...kkmrrrrmkk...',
    '.....kmrrmk.....',
    '.....kmrrmk.....',
    '....kmrrrrmk....',
    '...kmrrrrrrmk...',
    '..kTTTTTTTTTTk..',
    '..kTNNNNNNNNTk..',
    '..kTTTTTTTTTTk..',
    '..kkkkkkkkkkkk..',
  ];
}

/** 10x10 item icons lying on the ground. */
export function itemIcons() {
  return {
    'icon.sword': ['.......kk.', '......kak.', '.....kak..', '....kak...', '...kak....', 'k.kak.....', 'kkak......', '.kyk......', 'kyk.k.....', 'kk........'],
    'icon.bow': ['...kkk....', '..kAAk....', '.kAk.kX...', '.kAk..kX..', 'kAk....kX.', 'kAk....kX.', '.kAk..kX..', '.kAk.kX...', '..kAAk....', '...kkk....'],
    'icon.armor': ['.kk....kk.', 'kNNk..kNNk', 'kNNNkkNNNk', '.kNNNNNNk.', '.kNfNNNNk.', '.kNNNNNNk.', '.kNNfNNNk.', '.kNNNNNNk.', '.kTTTTTTk.', '..kkkkkk..'],
    'icon.mushroom': ['..kkkkkk..', '.kiiXiiik.', 'kiXiiiXiik', 'kiiiiiiiik', '.kkkkkkkk.', '...kssk...', '...kssk...', '...kssk...', '..kssssk..', '..kkkkkk..'],
    'icon.berry': ['....kk....', '...kLk....', '..kkLkk...', '.kiikiik..', 'kiXiikXiik', 'kiiikiiiik', 'kiiik.kiik', '.kiik..kk.', '..kk......', '..........'],
    'icon.herb': ['....k.....', '...khk..k.', '..khLk.khk', '..khLkkhLk', '.k.kLkhLk.', 'khk.kLLk..', 'khLkkLk...', '.kLLLk....', '...kLk....', '...kkk....'],
    'icon.pepper': ['.....kk...', '....kLk...', '...kkkk...', '..kKKKKk..', '.kKJKKKKk.', '.kKJKKKKk.', '.kKKKKKKk.', '..kKKKKk..', '...kKKk...', '....kk....'],
    'icon.meat': ['..kkkkk...', '.kiiiiik..', 'kiiXiiiik.', 'kiiiiiiik.', 'kiiiiiiikk', '.kiiiiikXk', '..kkkkkkXk', '.......kXk', '........kk', '..........'],
    'icon.fang': ['k.........', 'kXk.......', 'kXXk......', '.kXXk.....', '.kXXXk....', '..kXXXk...', '..kXXXXk..', '...kXXXXk.', '....kkkkk.', '..........'],
    'icon.shard': ['....kk....', '...kjjk...', '..kjXjjk..', '..kjXjjk..', '.kjjjjzjk.', '.kjjjzzjk.', '..kjjzjk..', '..kjzzjk..', '...kzzk...', '....kk....'],
    'icon.arrows': ['k.........', '.kak......', '.kaak.....', '..kAk.....', '...kAk.k..', '....kAkak.', '.....kAak.', '.....kAAk.', '......kXXk', '.......kkk'],
    'icon.food': ['..........', '..k.k.k...', '..........', '.kkkkkkkk.', 'kvvvvvvvvk', 'kKyKyKyKvk', 'kvyKyKyvvk', '.kvvvvvvk.', '..kkkkkk..', '..........'],
  };
}

// ---- P7 puzzles ----

export function pitTile() {
  const g = grid(16, 16, 'D');
  for (let x = 0; x < 16; x++) {
    g[0][x] = 'F';
    g[1][x] = x % 3 === 0 ? 'F' : 'k';
    g[2][x] = 'k';
  }
  const rand = rng(77);
  for (let i = 0; i < 6; i++) g[4 + Math.floor(rand() * 11)][Math.floor(rand() * 16)] = 'Z';
  return toRows(g);
}

/** Vine platform drawn over water / a pit. */
export function vineTile() {
  return [
    '..kk......kk....',
    '.kLLk..kkkLLk...',
    'kLhLLkkLLhLLLk..',
    'kLLLLLLLLLLLLLk.',
    '.kLLhLLLLLhLLLLk',
    '.kLLLLtttLLLLLk.',
    'kLLhLttTttLLhLLk',
    'kLLLttTTTttLLLLk',
    'kLLLLttTttLLLLk.',
    '.kLLhLtttLLhLLk.',
    'kLLLLLLLLLLLLLLk',
    'kLhLLLLhLLLLLhLk',
    '.kLLLkkLLLLkLLk.',
    '..kLk..kLLk.kk..',
    '...k....kk......',
    '................',
  ];
}

/** 12x24 glowing pillar (trial entrance). */
export function pillarSprite() {
  const rows = [
    '...kkkkkk...',
    '..kvvvvvvk..',
    '..kBIBBIBk..',
    '..kBBBBBBk..',
  ];
  for (let i = 0; i < 16; i++) rows.push(i % 5 === 2 ? '..kBBIIBBk..' : i % 5 === 3 ? '..kBIBBIBk..' : '..kBBBBBQk..');
  rows.push('.kvvvvvvvvk.', 'kBBBBBBBBBBk', 'kQQQQQQQQQQk', 'kkkkkkkkkkkk');
  return rows;
}

/** 16x14 星環 altar. */
export function altarSprite() {
  return [
    '.....kkkkkk.....',
    '....kIIIIIIk....',
    '...kIkkkkkkIk...',
    '...kIk....kIk...',
    '...kIkkkkkkIk...',
    '....kIIIIIIk....',
    '.....kkkkkk.....',
    '..kkkkkkkkkkkk..',
    '.kvvvvvvvvvvvvk.',
    'kBBBBBBBBBBBBBBk',
    'kBBQBBBBBBBBQBBk',
    'kBBBBBBBBBBBBBBk',
    'kQQQQQQQQQQQQQQk',
    'kkkkkkkkkkkkkkkk',
  ];
}

/** 16x16 iron crate. */
export function crateSprite() {
  return [
    'kkkkkkkkkkkkkkkk',
    'kRRRRRRRRRRRRRRk',
    'kRmmmmmmmmmmmmRk',
    'kRmrrrrrrrrrrmRk',
    'kRmrkrrrrrrkrmRk',
    'kRmrrkrrrrkrrmRk',
    'kRmrrrkrrkrrrmRk',
    'kRmrrrrkkrrrrmRk',
    'kRmrrrrkkrrrrmRk',
    'kRmrrrkrrkrrrmRk',
    'kRmrrkrrrrkrrmRk',
    'kRmrkrrrrrrkrmRk',
    'kRmrrrrrrrrrrmRk',
    'kRmmmmmmmmmmmmRk',
    'kmmmmmmmmmmmmmmk',
    'kkkkkkkkkkkkkkkk',
  ];
}

/** 10x18 sconce (torch stand), unlit or burning. @param {boolean} lit */
export function sconceSprite(lit) {
  const top = lit
    ? ['...kk.....', '..kKk..k..', '..kKJk.kk.', '.kKJJkkKk.', '.kKJXJKKk.', '.kKJXXJKk.']
    : ['..........', '..........', '..........', '..........', '..........', '..........'];
  return [
    ...top,
    'kkkkkkkkkk',
    'kAAAAAAAAk',
    '.kAAAAAAk.',
    '..kmrrmk..',
    '...kmrk...',
    '...kmrk...',
    '...kmrk...',
    '...kmrk...',
    '...kmrk...',
    '..kmmrrk..',
    '.kmmmrrrk.',
    'kkkkkkkkkk',
  ];
}

/** 12x16 resonance stone (glows while active). @param {boolean} on */
export function stoneSprite(on) {
  const r = on ? 'I' : 'Q';
  return [
    '....kkkk....',
    '..kkRRRRkk..',
    '.kRRrrrrrmk.',
    '.kRr' + r + r + r + r + 'rmk.',
    'kRr' + r + 'rrrr' + r + 'rmk',
    'kRr' + r + 'r' + r + r + 'r' + r + 'rmk',
    'kRr' + r + 'r' + r + r + 'r' + r + 'rmk',
    'kRr' + r + 'rrrr' + r + 'rmk',
    '.kr' + r + r + r + r + 'rrmk.',
    '.krrrrrrrmk.',
    '.krrrrrrmmk.',
    'kkmrrrrrmmkk',
    'kmmmmmmmmmmk',
    'kmmmmmmmmmmk',
    'kkkkkkkkkkkk',
    '............',
  ];
}

/** 14x10 pressure plate, raised or pressed. @param {boolean} down */
export function plateSprite(down) {
  return down
    ? ['..............', '..............', '..............', '.kkkkkkkkkkkk.', 'kQBBBBBBBBBBQk', 'kQBBIIIIIIBBQk', 'kQBBBBBBBBBBQk', 'kQQQQQQQQQQQQk', 'kkkkkkkkkkkkkk', '..............']
    : ['..............', '.kkkkkkkkkkkk.', 'kvvvvvvvvvvvvk', 'kBBBBBBBBBBBBk', 'kBBBQQQQQQBBBk', 'kBBBBBBBBBBBBk', 'kQQQQQQQQQQQQk', 'kQQQQQQQQQQQQk', 'kkkkkkkkkkkkkk', '..............'];
}

/** 12x14 light sensor (an eye in a stone). @param {boolean} on */
export function sensorSprite(on) {
  const e = on ? 'Y' : 'Q';
  return [
    '...kkkkkk...',
    '..kvvvvvvk..',
    '.kBBBBBBBBk.',
    '.kBBkkkkBBk.',
    '.kBk' + e + e + e + e + 'kBk.',
    '.kBk' + e + 'XX' + e + 'kBk.',
    '.kBk' + e + e + e + e + 'kBk.',
    '.kBBkkkkBBk.',
    '.kBBBBBBBBk.',
    '.kBBBBBBBQk.',
    'kBBBBBBBBBQk',
    'kQQQQQQQQQQk',
    'kQQQQQQQQQQk',
    'kkkkkkkkkkkk',
  ];
}

/** 8x8 light orb. */
export function lightOrbSprite() {
  return ['..kkkk..', '.kYYYYk.', 'kYXXXXYk', 'kYXXXXYk', 'kYXXXXYk', 'kYXXXXYk', '.kYYYYk.', '..kkkk..'];
}

// ---- P8 region bundles ----

/** Red desert sand. @param {number} seed */
export function desertSandTile(seed) {
  const g = grid(16, 16, 'q');
  const rand = rng(300 + seed);
  // Wind ripples.
  for (let y = 2 + seed; y < 16; y += 5) {
    for (let x = 0; x < 16; x++) if ((x + y * 2 + seed) % 7 < 4) g[y][x] = 'p';
  }
  for (let i = 0; i < 8; i++) g[Math.floor(rand() * 16)][Math.floor(rand() * 16)] = rand() < 0.5 ? 'P' : 'V';
  return toRows(g);
}

/** Plains grass with flowers. @param {number} seed */
export function plainsGrassTile(seed) {
  const g = grid(16, 16, 'G');
  const rand = rng(400 + seed);
  for (let i = 0; i < 12; i++) {
    const x = Math.floor(rand() * 15);
    const y = Math.floor(rand() * 15) + 1;
    g[y][x] = 'g';
    if (rand() < 0.6) g[y - 1][x] = 'h';
  }
  for (let i = 0; i < seed; i++) {
    const x = 1 + Math.floor(rand() * 14);
    const y = 1 + Math.floor(rand() * 14);
    g[y][x] = ['i', 'Y', 'X'][i % 3];
  }
  return toRows(g);
}

/** 12x20 cactus. */
export function cactusSprite() {
  return [
    '....kkk.....',
    '...kdGdk....',
    '...kdGdk.kk.',
    '.kkkdGdk.kGk',
    'kGdkdGdk.kGk',
    'kGdkdGdkkkGk',
    'kGdddGdddGdk',
    '.kkddGddddk.',
    '...kdGdkkk..',
    '...kdGdk....',
    '...kdGdk....',
    '...kdGdk....',
    '...kdGdk....',
    '...kdGdk....',
    '...kdGdk....',
    '..kkdGdkk...',
    '.kPPPPPPPk..',
    'kPqqqqqqqPk.',
    'kkkkkkkkkkk.',
    '............',
  ];
}

// ---- P9 villagers ----

/** Outfits: [tunic, tunic dark, hair] palette letters per look. */
const LOOKS = [
  ['c', 'C', 'H'], // 0: like the player
  ['B', 'Q', 'v'], // 1: elder (grey robe, white hair)
  ['X', 'B', 'T'], // 2: cook (white apron)
  ['i', 'Z', 'k'], // 3: guard (red coat)
  ['g', 'd', 'N'], // 4: merchant (green)
  ['y', 'A', 'f'], // 5: child (yellow)
];

/** Villager walk frames (same shapes as the player, another outfit). @param {number} look */
export function villagerFrames(look) {
  const [t, td, hair] = LOOKS[look] ?? LOOKS[0];
  /** @type {Record<string, string[]>} */
  const out = {};
  for (const [key, rows] of Object.entries(playerFrames())) {
    const name = key.replace('player.', `npc.${look}.`);
    const swap = /** @type {Record<string, string>} */ ({ c: t, C: td, H: hair });
    out[name] = rows.map((r) => [...r].map((ch) => swap[ch] ?? ch).join(''));
  }
  return out;
}

/** 48x40 village house (3 tiles wide; the door is on the bottom middle tile). */
export function houseSprite() {
  const roof = [];
  for (let y = 0; y < 18; y++) {
    const inset = Math.max(0, 8 - y);
    let row = '.'.repeat(inset);
    for (let x = inset; x < 48 - inset; x++) {
      const edge = x === inset || x === 47 - inset || y === 0 || y === 17;
      row += edge ? 'k' : (x + y) % 6 === 0 ? 'F' : y % 3 === 0 ? 'E' : 'f';
    }
    row += '.'.repeat(inset);
    roof.push(row);
  }
  const wall = [];
  for (let y = 0; y < 22; y++) {
    let row = '';
    for (let x = 0; x < 48; x++) {
      const door = x >= 19 && x <= 28 && y >= 8;
      const window1 = (x >= 6 && x <= 12) || (x >= 35 && x <= 41);
      if (x === 0 || x === 47 || y === 21) row += 'k';
      else if (door) row += x === 19 || x === 28 || y === 8 ? 'k' : x === 26 && y === 15 ? 'Y' : 'T';
      else if (window1 && y >= 5 && y <= 10) row += y === 5 || y === 10 || x === 6 || x === 12 || x === 35 || x === 41 ? 'k' : 'J';
      else row += y % 5 === 4 ? 'A' : 'v';
    }
    wall.push(row);
  }
  return [...roof, ...wall];
}

// --- P10.1: inside the houses ---

/** Wooden floor boards (16 x 16). */
export function woodFloorTile() {
  const g = grid(16, 16, 'f');
  for (let y = 0; y < 16; y++) {
    for (let x = 0; x < 16; x++) {
      if (y % 4 === 3) g[y][x] = 'F';
      else if ((x + (Math.floor(y / 4) % 2) * 8) % 16 === 0) g[y][x] = 'E';
      else if ((x * 5 + y * 3) % 17 === 0) g[y][x] = 'E';
    }
  }
  return toRows(g);
}

/** The top of a house wall seen from above: dark timber (16 x 16). */
export function wallTopTile() {
  const g = grid(16, 16, 'T');
  for (let x = 0; x < 16; x++) {
    g[0][x] = 'N';
    g[15][x] = 'k';
  }
  for (let y = 4; y < 16; y += 5) for (let x = 0; x < 16; x++) if (x % 7 !== 3) g[y][x] = 'F';
  return toRows(g);
}

/** Nothing (outside every room). */
export function darkTile() {
  return toRows(grid(16, 16, 'k'));
}

/** Plastered wall face with a timber beam on top and a skirting board at the base (16 x h). */
export function plasterFace(h, top, bottom = false) {
  const g = grid(16, h, 'v');
  for (let y = 0; y < h; y++) for (let x = 0; x < 16; x++) if ((x * 3 + y * 7) % 19 === 0) g[y][x] = 'B';
  if (top) for (let x = 0; x < 16; x++) g[0][x] = g[1][x] = 'T';
  if (bottom) {
    for (let x = 0; x < 16; x++) {
      g[h - 1][x] = 'k';
      if (h > 2) g[h - 2][x] = 'N';
    }
  }
  return toRows(g);
}

/** @param {string[]} rows @param {number} w */
const pad = (rows, w) => rows.map((r) => r.padEnd(w, '.'));

/** The low front wall of a room (16 x 12). */
export function lowWallSprite() {
  return [
    'kkkkkkkkkkkkkkkk',
    'NNNNNNNNNNNNNNNN',
    'AAAAAAAAAAAAAAAA',
    'kkkkkkkkkkkkkkkk',
    'TNTTTTTTNTTTTTTT',
    'TNTTTTTTNTTTTTTT',
    'TNTTTTTTNTTTTTTT',
    'TNTTTTTTNTTTTTTT',
    'TNTTTTTTNTTTTTTT',
    'TNTTTTTTNTTTTTTT',
    'FFFFFFFFFFFFFFFF',
    'kkkkkkkkkkkkkkkk',
  ];
}

/** A bed, head to the north (16 x 26). */
export function bedSprite() {
  const rows = ['.kkkkkkkkkkkkkk.', 'kNNNNNNNNNNNNNNk', 'kNTTTTTTTTTTTTNk', 'kNkkkkkkkkkkkkNk', 'kNkXXXXXXXXXXkNk', 'kNkXXXXXXXXXXkNk', 'kNkXXXXXXXXXXkNk', 'kNkkkkkkkkkkkkNk'];
  for (let y = 0; y < 14; y++) rows.push(y === 0 ? 'kNkCCCCCCCCCCkNk' : y === 13 ? 'kNkkkkkkkkkkkkNk' : y % 4 === 2 ? 'kNkcCccccccCckNk' : 'kNkccccccccccckNk'.slice(0, 16));
  rows.push('kNNNNNNNNNNNNNNk', 'kTTTTTTTTTTTTTTk', 'kTk..........kTk', 'kkk..........kkk');
  return pad(rows, 16);
}

/** A small table (16 x 14). */
export function tableSprite() {
  return [
    '.kkkkkkkkkkkkkk.',
    'kqqqqqqqqqqqqqqk',
    'kNNNNNNNNNNNNNNk',
    'kNNNNNNNNNNNNNNk',
    'kNNNNSNNNNNNNNNk',
    'kNNNNNNNNNNNNNNk',
    'kTTTTTTTTTTTTTTk',
    '.kTkkkkkkkkkkTk.',
    '.kTk........kTk.',
    '.kTk........kTk.',
    '.kTk........kTk.',
    '.kTk........kTk.',
    '.kTk........kTk.',
    '.kkk........kkk.',
  ];
}

/** A shelf against the wall, with jars and books; `charm` adds the elder's charm glowing on top. @param {boolean} [charm] */
export function shelfSprite(charm = false) {
  const rows = [
    charm ? '......kIIk......' : '................',
    charm ? '.....kIOOIk.....' : '................',
    charm ? '......kIIk......' : '................',
    'kkkkkkkkkkkkkkkk',
    'kTTTTTTTTTTTTTTk',
    'kTkkkkkkkkkkkkTk',
    'kTkYYkWWkKKkrrTk',
    'kTkYYkWWkKKkrrTk',
    'kTTTTTTTTTTTTTTk',
    'kTkcckhhkkRRkkTk',
    'kTkcckhhkkRRkkTk',
    'kTkcckhhkkRRkkTk',
    'kTTTTTTTTTTTTTTk',
    'kTkNNNNkkiiikkTk',
    'kTkNNNNkkiiikkTk',
    'kTTTTTTTTTTTTTTk',
    'kTk..........kTk',
    'kTk..........kTk',
    'kTTTTTTTTTTTTTTk',
    'kkkkkkkkkkkkkkkk',
  ];
  return rows;
}

/** One length of shop counter (16 x 16). */
export function counterSprite() {
  return [
    'kkkkkkkkkkkkkkkk',
    'qqqqqqqqqqqqqqqq',
    'vvvvvvvvvvvvvvvv',
    'kkkkkkkkkkkkkkkk',
    'NNNNNNNNNNNNNNNN',
    'NTTNNNNNNNNNNTTN',
    'NTTNNNNNNNNNNTTN',
    'NNNNNNNNNNNNNNNN',
    'NNNNNNNNNNNNNNNN',
    'NTTNNNNNNNNNNTTN',
    'NTTNNNNNNNNNNTTN',
    'NNNNNNNNNNNNNNNN',
    'NNNNNNNNNNNNNNNN',
    'TTTTTTTTTTTTTTTT',
    'FFFFFFFFFFFFFFFF',
    'kkkkkkkkkkkkkkkk',
  ];
}

/** A stone cooking stove with a fire inside (16 x 20). */
export function stoveSprite() {
  return [
    '....kkkkkkkk....',
    '....kmmmmmmk....',
    '....kmrrrrmk....',
    '..kkkmmmmmmkkk..',
    '.kRRRRRRRRRRRRk.',
    'kRrrrrrrrrrrrrRk',
    'krrrrrrrrrrrrrrk',
    'krmmmmmmmmmmmmrk',
    'krmkkkkkkkkkkmrk',
    'krmkDDDDDDDDkmrk',
    'krmkDDKKKKDDkmrk',
    'krmkDKJJJJKDkmrk',
    'krmkKJJJJJJKkmrk',
    'krmkKJJYYJJKkmrk',
    'krmkkkkkkkkkkmrk',
    'krrrrrrrrrrrrrrk',
    'krmrrmrrmrrmrrmk',
    'krrrrrrrrrrrrrrk',
    'kmmmmmmmmmmmmmmk',
    'kkkkkkkkkkkkkkkk',
  ];
}

/** A barrel (12 x 14). */
export function barrelSprite() {
  return [
    '..kkkkkkkk..',
    '.kNNNNNNNNk.',
    'kNTTTTTTTTNk',
    'kkkkkkkkkkkk',
    'kNNTNNNNTNNk',
    'kNNTNNNNTNNk',
    'kaaaaaaaaaak',
    'kNNTNNNNTNNk',
    'kNNTNNNNTNNk',
    'kNNTNNNNTNNk',
    'kaaaaaaaaaak',
    'kNNTNNNNTNNk',
    '.kNTNNNNTNk.',
    '..kkkkkkkk..',
  ];
}

/** The door mat: walk down onto it to go back outside (16 x 8). */
export function matSprite() {
  return [
    '.kkkkkkkkkkkkkk.',
    'kiiiiiiiiiiiiiik',
    'kiYYYYYYYYYYYYik',
    'kiYiiiiiiiiiiYik',
    'kiYiiiiiiiiiiYik',
    'kiYYYYYYYYYYYYik',
    'kiiiiiiiiiiiiiik',
    '.kkkkkkkkkkkkkk.',
  ];
}

// --- P10.2: the seasons (each season's art is its own bundle, loaded while it lasts) ---

/** Swaps palette letters. @param {string[]} rows @param {Record<string, string>} map */
export function recolor(rows, map) {
  return rows.map((r) => [...r].map((ch) => map[ch] ?? ch).join(''));
}

/** Spring: pink blossoms in the canopy. */
export function springTreeSprite() {
  return treeSprite().map((r, y) => [...r].map((ch, x) => (ch === 'h' ? '6' : ch === 'l' && (x * 3 + y * 5) % 7 === 0 ? '7' : ch === 'l' && (x + y * 2) % 5 === 0 ? '6' : ch)).join(''));
}

/** Autumn: orange and red leaves. */
export const autumnTreeSprite = () => recolor(treeSprite(), { l: '1', L: '2', h: '3' });
/** Autumn: grass gone dry and golden. @param {string[]} rows */
export const autumnGrass = (rows) => recolor(rows, { g: '8', G: 'M', d: '9', h: 'M' });

/** Winter: snow on the canopy. */
export const winterTreeSprite = () => recolor(treeSprite(), { h: '4', l: '5' });

/** Winter: the ground under snow (16 x 16). @param {number} seed */
export function snowTile(seed) {
  const g = grid(16, 16, '4');
  const rand = rng(700 + seed);
  for (let i = 0; i < 9; i++) {
    const x = Math.floor(rand() * 15);
    const y = Math.floor(rand() * 15);
    g[y][x] = '5';
    if (rand() < 0.5) g[y][x + 1] = '5';
  }
  return toRows(g);
}
/** Winter: snow on the lip of a cliff. @param {string[]} rows */
export const winterLip = (rows) => recolor(rows, { G: '4', d: '5' });
/** Autumn: a dry lip. @param {string[]} rows */
export const autumnLip = (rows) => recolor(rows, { G: 'M', d: '9' });

// --- P10.3: the remaining regions ---

/** 囁きの森: dark, mossy ground (16 x 16). @param {number} seed */
export function forestGrassTile(seed) {
  const g = grid(16, 16, 'd');
  const rand = rng(900 + seed);
  for (let i = 0; i < 14; i++) {
    const x = Math.floor(rand() * 15);
    const y = Math.floor(rand() * 15) + 1;
    g[y][x] = rand() < 0.5 ? 'L' : 'g';
    if (rand() < 0.3) g[y - 1][x] = 'l';
  }
  if (seed % 2 === 1) g[4 + seed][6] = 'O'; // a glowing spore here and there
  return toRows(g);
}

/** 囁きの森: a tall dark conifer (16 x 30). */
export function pineSprite() {
  const w = 16;
  const h = 30;
  const g = grid(w, h, '.');
  for (let y = 0; y < 24; y++) {
    const half = Math.min(7.5, 1 + y * 0.32 + (y % 6) * 0.35);
    for (let x = 0; x < w; x++) {
      const dx = Math.abs(x - 7.5);
      if (dx > half) continue;
      g[y][x] = dx > half - 1 || y === 23 ? 'k' : x < 7 && y % 6 < 3 ? 'l' : (x + y) % 5 === 0 ? 'd' : 'L';
    }
  }
  for (let y = 24; y < h; y++) for (let x = 6; x <= 9; x++) g[y][x] = x === 6 || x === 9 || y === h - 1 ? 'k' : 'T';
  return toRows(g);
}

/** 白嶺山脈: snow with rock showing through (16 x 16). @param {number} seed */
export function mountainSnowTile(seed) {
  const g = toRows(grid(16, 16, '4')).map((r) => [...r]);
  const rand = rng(950 + seed);
  for (let i = 0; i < 8; i++) {
    const x = Math.floor(rand() * 15);
    const y = Math.floor(rand() * 15);
    g[y][x] = i < 2 ? 'r' : '5';
    if (rand() < 0.5) g[y][x + 1] = '5';
  }
  return toRows(g);
}
/** 白嶺山脈: a conifer under snow. */
export const snowPineSprite = () => recolor(pineSprite(), { l: '4', L: '5', d: 'L' });
/** 白嶺山脈: grey rock cliffs with a snowy lip. @param {number} h @param {boolean} top @param {boolean} [bottom] */
export const stoneFace = (h, top, bottom = false) => recolor(earthFace(h, top, bottom), { E: 'r', F: 'm', f: 'R', G: '4', d: '5' });

/** 鏡湖と群島: bright lakeside grass (16 x 16). @param {number} seed */
export function lakeGrassTile(seed) {
  const g = grid(16, 16, 'G');
  const rand = rng(990 + seed);
  for (let i = 0; i < 10; i++) {
    const x = Math.floor(rand() * 15);
    const y = Math.floor(rand() * 15) + 1;
    g[y][x] = 'h';
    if (rand() < 0.5) g[y - 1][x] = 'g';
  }
  if (seed === 3) g[8][8] = 'X';
  return toRows(g);
}

// --- P10.4: the cores of the murk (bosses), 32 x 30, two frames ---

/**
 * A murk body with a glowing core and the region's mark (roots, ice horns, sand, sparks).
 * @param {'root' | 'frost' | 'sand' | 'storm'} kind @param {number} frame
 */
export function bossSprite(kind, frame) {
  const w = 32;
  const h = 30;
  const g = grid(w, h, '.');
  const bob = frame;
  const accent = { root: ['T', 't'], frost: ['4', '5'], sand: ['u', 'U'], storm: ['Y', 'J'] }[kind];
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const dx = (x - 15.5) / 13;
      const dy = (y - 17 - bob) / 11;
      const d = dx * dx + dy * dy;
      if (d > 1) continue;
      g[y][x] = d > 0.86 ? 'k' : dy < -0.4 && dx < 0 ? 'j' : (x * 3 + y * 5) % 11 === 0 ? 'Z' : 'z';
    }
  }
  // The core: a glowing heart in the middle.
  for (let y = 14; y < 21; y++) for (let x = 13; x < 19; x++) if (Math.abs(x - 15.5) + Math.abs(y - 17.5) < 4) g[y + bob][x] = Math.abs(x - 15.5) + Math.abs(y - 17.5) < 2 ? 'X' : 'O';
  // Eyes.
  g[11 + bob][10] = g[11 + bob][21] = 'i';
  g[11 + bob][11] = g[11 + bob][20] = 'i';
  // The region's mark.
  if (kind === 'frost') {
    for (let k = 0; k < 6; k++) {
      g[5 - k + bob + 3][7 - Math.floor(k / 2)] = k % 2 ? accent[1] : accent[0];
      g[5 - k + bob + 3][24 + Math.floor(k / 2)] = k % 2 ? accent[1] : accent[0];
    }
  } else if (kind === 'root') {
    for (let x = 2; x < 30; x += 4) for (let y = 25; y < 30; y++) if (g[y][x] === '.' || y > 27) g[y][x] = y % 2 ? accent[0] : accent[1];
  } else if (kind === 'sand') {
    for (let y = 22; y < 30; y++) for (let x = 3; x < 29; x++) if ((x + y * 3 + frame) % 7 === 0) g[y][x] = accent[(x + y) % 2];
  } else {
    for (const [x, y] of [[3, 8], [28, 10], [5, 22], [27, 24], [16, 2]]) {
      g[y][x] = accent[0];
      if (y + 1 < h) g[y + 1][x + (frame ? 1 : -1)] = accent[1];
    }
  }
  return toRows(g);
}

/** P10.5: stairs going down (16 x 16, flat on the floor). */
export function stairsSprite() {
  const rows = [];
  for (let y = 0; y < 16; y++) {
    const step = Math.floor(y / 4);
    const shade = ['Q', 'm', 'D', 'k'][step];
    rows.push(y % 4 === 0 ? 'kvvvvvvvvvvvvvvk' : `k${shade.repeat(14)}k`);
  }
  return rows;
}
