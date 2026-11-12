// @ts-check
// gfx W5: one shared texture for the small masks the effects draw in code — the cast shadows' steps,
// the hit rings' frames, the mist bands. Each was its own canvas texture (about 15 more textures on a
// village screen), and sprites on different textures batch less well (a draw call breaks every 16
// textures, and each texture switch costs the renderer CPU time). Now each mask is a frame on one
// canvas 512 texels wide (one texel per game px, nearest-neighbour), packed in shelves and drawn once,
// when first asked for. If the canvas is ever full (512 rows), a mask gets a canvas of its own (as before).
// gfx v2 integration: the canvas is only as tall as its shelves (it grows when a shelf is added; the
// frames keep their place), so ~15 masks cost 512×41 texels (80 KB) instead of 512×512 (1 MB): the
// 35 MB image guide with the ground v2 and the enemy v2.
import { Rectangle, Texture } from 'pixi.js';

export const ATLAS_SIZE = 512;

/** The rows a sheet needs for what is packed on it (its shelves, gap included), at least 1. @param {{ y: number, shelf: number }} at */
export const sheetRows = (at) => Math.max(1, Math.min(ATLAS_SIZE, at.y + at.shelf));
/** Empty texels between frames (nearest-neighbour sampling never reaches a neighbour, but a margin is free). */
const GAP = 1;

/**
 * Where the next frame of w×h goes on a shelf-packed sheet, or null when it is full. Pure.
 * @param {{ x: number, y: number, shelf: number }} at the packer's state (changed)
 * @param {number} w @param {number} h @param {number} [size]
 * @returns {{ x: number, y: number } | null}
 */
export function packShelf(at, w, h, size = ATLAS_SIZE) {
  if (w + GAP > size || h + GAP > size) return null;
  if (at.x + w + GAP > size) {
    at.y += at.shelf;
    at.x = 0;
    at.shelf = 0;
  }
  if (at.y + h + GAP > size) return null;
  const spot = { x: at.x, y: at.y };
  at.x += w + GAP;
  at.shelf = Math.max(at.shelf, h + GAP);
  return spot;
}

/** @type {{ canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, source: import('pixi.js').TextureSource, at: { x: number, y: number, shelf: number } } | null} */
let sheet = null;
/** @type {Map<string, Texture>} */
const frames = new Map();

/** A canvas of w×h with the RGBA data on it. @param {Uint8ClampedArray} rgba @param {number} w @param {number} h */
function canvasOf(rgba, w, h) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const g = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
  const img = g.createImageData(w, h);
  img.data.set(rgba);
  g.putImageData(img, 0, 0);
  return c;
}

/**
 * The frame for `key` (made once): `paint()` gives its RGBA pixels, w×h. Texture.WHITE without a
 * canvas (unit tests).
 * @param {string} key @param {number} w @param {number} h @param {() => Uint8ClampedArray} paint
 * @returns {Texture}
 */
export function atlasFrame(key, w, h, paint) {
  const had = frames.get(key);
  if (had && !had.destroyed) return had;
  if (typeof document === 'undefined' || typeof document.createElement !== 'function') return Texture.WHITE;
  if (!sheet || sheet.source.destroyed) {
    const canvas = document.createElement('canvas');
    canvas.width = ATLAS_SIZE;
    canvas.height = 1; // (grows with its shelves: below)
    const ctx = /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d'));
    const source = Texture.from(canvas).source;
    source.scaleMode = 'nearest';
    sheet = { canvas, ctx, source, at: { x: 0, y: 0, shelf: 0 } };
    frames.clear();
  }
  const spot = packShelf(sheet.at, w, h);
  /** @type {Texture} */
  let tex;
  if (spot) {
    const rows = sheetRows(sheet.at);
    if (rows > sheet.canvas.height) {
      // a taller canvas, the frames drawn so far kept where they are (the textures' UVs follow the resize)
      const old = canvasOf(sheet.ctx.getImageData(0, 0, sheet.canvas.width, sheet.canvas.height).data, sheet.canvas.width, sheet.canvas.height);
      sheet.source.resize(ATLAS_SIZE, rows);
      sheet.ctx.drawImage(old, 0, 0);
    }
    sheet.ctx.drawImage(canvasOf(paint(), w, h), spot.x, spot.y);
    sheet.source.update();
    tex = new Texture({ source: sheet.source, frame: new Rectangle(spot.x, spot.y, w, h) });
  } else {
    tex = Texture.from(canvasOf(paint(), w, h)); // (full: one of its own)
    tex.source.scaleMode = 'nearest';
  }
  frames.set(key, tex);
  return tex;
}

/**
 * White pixels with the given opacity per texel (0..255): the masks are white and tinted where drawn.
 * @param {ArrayLike<number>} alpha @param {number} n texels
 */
export function whiteRGBA(alpha, n) {
  const out = new Uint8ClampedArray(n * 4);
  for (let i = 0; i < n; i++) {
    out[i * 4] = out[i * 4 + 1] = out[i * 4 + 2] = 255;
    out[i * 4 + 3] = alpha[i];
  }
  return out;
}

/** Frames made so far (tests, measuring). */
export const atlasStats = () => ({ frames: frames.size, shelfY: sheet?.at.y ?? 0, shelf: sheet?.at.shelf ?? 0, x: sheet?.at.x ?? 0, size: sheet ? [sheet.canvas.width, sheet.canvas.height] : null });
