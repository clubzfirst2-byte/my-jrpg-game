// @ts-check
// Release art packing (docs/perf/release-art-packing.md). The release art stays one PNG per frame
// under src/art-release/<group>/ (the source of truth, never changed by this). At BUILD time,
// vite.config.js (releaseArt plugin) packs each group into ONE sheet PNG + ONE frame table JSON, so
// the game loads 2 files per group instead of one module per frame. Nothing is written into src/:
// the sheet and the table are emitted straight into dist/assets by the plugin.
//
// Only plain 8-bit-per-channel, non-interlaced PNGs without colour-space chunks (gAMA, iCCP, cHRM, cICP, mDCV, cLLI)
// are accepted, so the browser draws the sheet's pixels exactly as it drew each frame file; anything
// else stops the build with the file's name rather than risk a different picture.
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { deflateSync, inflateSync } from 'node:zlib';

const SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const CRC = new Int32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c;
});
/** @param {Uint8Array} buf */
const crc32 = (buf) => {
  let c = -1;
  for (const b of buf) c = CRC[(c ^ b) & 255] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
};

/** Chunks that tell the browser to change colours; a frame with one is refused (see the top). */
export const COLOUR_SPACE_CHUNKS = ['gAMA', 'iCCP', 'cHRM', 'cICP', 'mDCV', 'cLLI'];

/** @typedef {{ width: number, height: number, data: Uint8Array }} RgbaImage RGBA, 4 bytes per pixel, rows top to bottom */
/** @typedef {{ x: number, y: number, w: number, h: number }} FrameRect */

/**
 * Decodes a PNG to RGBA. Supports 8-bit grey, grey+alpha, RGB, RGBA and 1/2/4/8-bit palette or grey.
 * @param {Uint8Array} file
 * @param {string} [name] for error messages
 * @returns {RgbaImage}
 */
export function decodePng(file, name = 'PNG') {
  const buf = Buffer.from(file.buffer, file.byteOffset, file.byteLength);
  if (!buf.subarray(0, 8).equals(SIGNATURE)) throw new Error(`${name}: not a PNG`);
  let width = 0;
  let height = 0;
  let depth = 0;
  let type = 0;
  /** @type {Uint8Array | null} */
  let palette = null;
  /** @type {Uint8Array | null} */
  let trns = null;
  /** @type {Buffer[]} */
  const idat = [];
  for (let i = 8; i < buf.length; ) {
    const len = buf.readUInt32BE(i);
    const kind = buf.toString('latin1', i + 4, i + 8);
    const data = buf.subarray(i + 8, i + 8 + len);
    i += 12 + len;
    if (kind === 'IHDR') {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      depth = data[8];
      type = data[9];
      if (data[12] !== 0) throw new Error(`${name}: interlaced PNGs are not supported`);
    } else if (kind === 'PLTE') palette = data;
    else if (kind === 'tRNS') trns = data;
    else if (kind === 'IDAT') idat.push(data);
    else if (COLOUR_SPACE_CHUNKS.includes(kind)) {
      throw new Error(`${name}: colour-space chunk ${kind} is not supported (the browser could draw the packed sheet differently); save the PNG without it`);
    } else if (kind === 'IEND') break;
  }
  if (!width || !height) throw new Error(`${name}: PNG without a valid IHDR`);
  const channels = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 }[type];
  if (!channels) throw new Error(`${name}: unknown PNG colour type ${type}`);
  if (depth === 16 || (depth !== 8 && type !== 0 && type !== 3)) throw new Error(`${name}: ${depth}-bit PNGs of colour type ${type} are not supported`);
  if (type === 3 && !palette) throw new Error(`${name}: palette PNG without PLTE`);

  const raw = inflateSync(Buffer.concat(idat));
  const bpp = Math.max(1, (channels * depth) >> 3); // bytes per pixel for the filters
  const stride = Math.ceil((width * channels * depth) / 8);
  // height × (filter byte + one row); for 8-bit RGBA that is height × (1 + width × 4)
  if (raw.length !== (stride + 1) * height) throw new Error(`${name}: broken PNG (pixel data is ${raw.length} bytes, expected ${(stride + 1) * height})`);
  const lines = new Uint8Array(stride * height);
  let prev = new Uint8Array(stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    const src = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    const out = lines.subarray(y * stride, (y + 1) * stride);
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? out[x - bpp] : 0;
      const b = prev[x];
      const c = x >= bpp ? prev[x - bpp] : 0;
      let v = src[x];
      if (filter === 1) v += a;
      else if (filter === 2) v += b;
      else if (filter === 3) v += (a + b) >> 1;
      else if (filter === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a);
        const pb = Math.abs(p - b);
        const pc = Math.abs(p - c);
        v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
      } else if (filter !== 0) throw new Error(`${name}: bad PNG filter ${filter}`);
      out[x] = v & 255;
    }
    prev = out;
  }

  const data = new Uint8Array(width * height * 4);
  const max = (1 << depth) - 1;
  for (let y = 0; y < height; y++) {
    const line = lines.subarray(y * stride, (y + 1) * stride);
    for (let x = 0; x < width; x++) {
      const o = (y * width + x) * 4;
      if (type === 6) data.set(line.subarray(x * 4, x * 4 + 4), o);
      else if (type === 2) {
        data.set(line.subarray(x * 3, x * 3 + 3), o);
        const t = trns && trns.length >= 6 && line[x * 3] === trns[1] && line[x * 3 + 1] === trns[3] && line[x * 3 + 2] === trns[5];
        data[o + 3] = t ? 0 : 255;
      } else if (type === 4) {
        data[o] = data[o + 1] = data[o + 2] = line[x * 2];
        data[o + 3] = line[x * 2 + 1];
      } else {
        // grey or palette, 1..8 bits per pixel
        const bit = x * depth;
        const v = (line[bit >> 3] >> (8 - depth - (bit & 7))) & max;
        if (type === 3) {
          const p = /** @type {Uint8Array} */ (palette);
          data[o] = p[v * 3];
          data[o + 1] = p[v * 3 + 1];
          data[o + 2] = p[v * 3 + 2];
          data[o + 3] = trns && v < trns.length ? trns[v] : 255;
        } else {
          const g = Math.round((v * 255) / max);
          data[o] = data[o + 1] = data[o + 2] = g;
          data[o + 3] = trns && trns.length >= 2 && v === ((trns[0] << 8) | trns[1]) ? 0 : 255;
        }
      }
    }
  }
  return { width, height, data };
}

/** @param {string} kind @param {Uint8Array} data */
function chunk(kind, data) {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  out.write(kind, 4, 'latin1');
  out.set(data, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}

/**
 * Encodes RGBA as an 8-bit RGBA PNG (no colour-space chunks, like the release frames). The same
 * pixels always give the same bytes.
 * @param {RgbaImage} img
 * @returns {Buffer}
 */
export function encodePng({ width, height, data }) {
  const head = Buffer.alloc(13);
  head.writeUInt32BE(width, 0);
  head.writeUInt32BE(height, 4);
  head[8] = 8; // bits per channel
  head[9] = 6; // RGBA
  const stride = width * 4;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y++) {
    // filter "Sub" per line: compresses pixel art well and is simple
    const o = y * (stride + 1);
    raw[o] = 1;
    for (let x = 0; x < stride; x++) raw[o + 1 + x] = (data[y * stride + x] - (x >= 4 ? data[y * stride + x - 4] : 0)) & 255;
  }
  return Buffer.concat([SIGNATURE, chunk('IHDR', head), chunk('IDAT', deflateSync(raw, { level: 9 })), chunk('IEND', new Uint8Array(0))]);
}

/** The largest sheet, in either direction (well within iPhone image limits). */
export const MAX_SHEET = 4096;

/** Empty pixels between frames, so a frame never picks up its neighbour's edge. */
export const SHEET_PAD = 1;

/**
 * Lays frames out on shelves (tallest first, then by name) in the narrowest power-of-two width
 * (64 .. 4096) whose sheet is no taller than wide; a group that would need more than 4096×4096
 * stops the build. Same frames → same layout.
 * @param {{ name: string, width: number, height: number }[]} frames
 * @returns {{ width: number, height: number, frames: Record<string, FrameRect> }}
 */
export function layoutSheet(frames) {
  const order = [...frames].sort((a, b) => b.height - a.height || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
  /** @param {number} width */
  const place = (width) => {
    /** @type {Record<string, FrameRect>} */
    const rects = {};
    let x = 0;
    let y = 0;
    let shelf = 0;
    for (const f of order) {
      if (f.width > width) return null;
      if (x + f.width > width) {
        x = 0;
        y += shelf + SHEET_PAD;
        shelf = 0;
      }
      rects[f.name] = { x, y, w: f.width, h: f.height };
      x += f.width + SHEET_PAD;
      shelf = Math.max(shelf, f.height);
    }
    return { width, height: Math.max(1, y + shelf), frames: rects };
  };
  for (const width of [64, 128, 256, 512, 1024, 2048, MAX_SHEET]) {
    const r = place(width);
    if (r && r.height <= width) return r;
  }
  const r = place(MAX_SHEET);
  if (!r) throw new Error(`release art: a frame is wider than ${MAX_SHEET} px`);
  throw new Error(`release art: the frames need a ${MAX_SHEET}×${r.height} sheet, more than ${MAX_SHEET}×${MAX_SHEET}; split the group into more folders`);
}

/**
 * Packs named RGBA frames into one sheet.
 * @param {Map<string, RgbaImage>} frames sprite name → pixels
 * @returns {{ image: RgbaImage, frames: Record<string, FrameRect> }} the table lists names in sorted order
 */
export function packSheet(frames) {
  const layout = layoutSheet([...frames].map(([name, img]) => ({ name, width: img.width, height: img.height })));
  const data = new Uint8Array(layout.width * layout.height * 4);
  for (const [name, img] of frames) {
    const r = layout.frames[name];
    for (let y = 0; y < img.height; y++) data.set(img.data.subarray(y * img.width * 4, (y + 1) * img.width * 4), ((r.y + y) * layout.width + r.x) * 4);
  }
  /** @type {Record<string, FrameRect>} */
  const table = {};
  for (const name of [...frames.keys()].sort()) table[name] = layout.frames[name];
  return { image: { width: layout.width, height: layout.height, data }, frames: table };
}

/**
 * Cuts one frame back out of a sheet (for tests and checks).
 * @param {RgbaImage} sheet @param {FrameRect} r @returns {RgbaImage}
 */
export function cutFrame(sheet, r) {
  const data = new Uint8Array(r.w * r.h * 4);
  for (let y = 0; y < r.h; y++) data.set(sheet.data.subarray(((r.y + y) * sheet.width + r.x) * 4, ((r.y + y) * sheet.width + r.x + r.w) * 4), y * r.w * 4);
  return { width: r.w, height: r.h, data };
}

/** The release groups: the folders under `root` (src/art-release). @param {string} root */
export function releaseGroups(root) {
  try {
    return readdirSync(root, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name)
      .sort();
  } catch {
    return [];
  }
}

/**
 * Packs one group folder: every *.png in it (lowercase ".png" only — the dev server's glob is
 * case-sensitive too, so both see the same files), named by its file name without ".png" (the same names
 * releaseFrames gave before packing).
 * @param {string} dir @param {(name: string) => boolean} [keep] only these frames (seasonPartOf)
 * @returns {{ png: Buffer, table: { width: number, height: number, frames: Record<string, FrameRect> }, files: string[] }}
 */
export function packGroup(dir, keep = () => true) {
  const files = readdirSync(dir)
    .filter((f) => f.endsWith('.png')) // lowercase only, like the dev server's glob (*.png)
    .filter((f) => keep(f.slice(0, -'.png'.length)))
    .sort();
  /** @type {Map<string, RgbaImage>} */
  const frames = new Map();
  for (const f of files) frames.set(f.slice(0, -'.png'.length), decodePng(readFileSync(join(dir, f)), join(dir, f)));
  const { image, frames: rects } = packSheet(frames);
  return { png: encodePng(image), table: { width: image.width, height: image.height, frames: rects }, files: files.map((f) => join(dir, f)) };
}

/** Graphics v3: the season parts of a v3 group (its autumn / winter frames on sheets of their own). */
export const SEASON_PARTS = Object.freeze(['', 'autumn', 'winter']);

/**
 * Graphics v3 (memory, STYLE.md 10.1 (1) and (6)): a v3 group is packed as one sheet per season — its
 * "autumn." and "winter." frames apart ("v3/terrain.autumn", "v3/terrain.winter"), the rest as the group
 * ("v3/terrain") — so building one season's bundle decodes only that season's sheet. The part of a frame
 * name: "autumn", "winter" or "" (the rest). @param {string} name
 */
export const seasonPartOf = (name) => /^(autumn|winter)\./.exec(name)?.[1] ?? '';
