// Draws the app icons (P11.1, PWA: home screen / app switcher) as PNG files, from a small pixel
// emblem — a ring of starlight (星環) around a glowing core on the night sky — scaled up with hard
// edges. No image tools needed: a tiny PNG encoder (zlib from Node).
//
//   node tools/gen_icons.mjs   ->   public/icons/*.png
import { deflateSync } from 'node:zlib';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const COLORS = { '.': [22, 32, 44], k: [12, 16, 26], r: [127, 232, 255], R: [201, 246, 255], g: [255, 215, 94], G: [255, 242, 180], s: [63, 138, 70], S: [95, 180, 85], w: [255, 255, 255] };

/** The 32 x 32 emblem: hills at the bottom, the star ring and its core above. */
function emblem() {
  const g = Array.from({ length: 32 }, () => Array(32).fill('.'));
  for (let y = 0; y < 32; y++) {
    for (let x = 0; x < 32; x++) {
      const dx = x - 15.5;
      const dy = y - 13.5;
      const d = Math.hypot(dx, dy);
      if (d > 8.2 && d < 10.6) g[y][x] = (Math.atan2(dy, dx) * 6) % 2 > 1 ? 'R' : 'r';
      if (d < 3.6) g[y][x] = d < 1.8 ? 'G' : 'g';
      // Rolling hills.
      const hill = 25 + Math.round(2 * Math.sin(x / 4));
      if (y >= hill) g[y][x] = y === hill ? 'S' : 's';
    }
  }
  for (const [x, y] of [[4, 4], [27, 6], [6, 20], [26, 21], [15, 1]]) g[y][x] = 'w';
  return g;
}

/** @param {number} size @param {number} pad empty border (a maskable icon keeps its art in the middle) */
function render(size, pad = 0) {
  const g = emblem();
  const inner = size - pad * 2;
  const px = Buffer.alloc(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const ix = Math.floor(((x - pad) / inner) * 32);
      const iy = Math.floor(((y - pad) / inner) * 32);
      const c = COLORS[ix >= 0 && ix < 32 && iy >= 0 && iy < 32 ? g[iy][ix] : '.'];
      px.set([...c, 255], (y * size + x) * 4);
    }
  }
  return png(size, size, px);
}

const CRC = new Int32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c;
});
const crc32 = (/** @type {Buffer} */ b) => {
  let c = -1;
  for (const v of b) c = CRC[(c ^ v) & 0xff] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
};
const chunk = (/** @type {string} */ type, /** @type {Buffer} */ data) => {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([len, body, crc]);
};
/** @param {number} w @param {number} h @param {Buffer} rgba */
export function png(w, h, rgba) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // RGBA
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) rgba.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4);
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const dir = join(root, 'public', 'icons');
  mkdirSync(dir, { recursive: true });
  const files = { 'icon-192.png': render(192), 'icon-512.png': render(512), 'icon-maskable-512.png': render(512, 64), 'apple-touch-icon.png': render(180) };
  for (const [name, data] of Object.entries(files)) {
    writeFileSync(join(dir, name), data);
    console.log('wrote', name, data.length, 'bytes');
  }
}
