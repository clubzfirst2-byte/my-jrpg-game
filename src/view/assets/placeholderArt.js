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
