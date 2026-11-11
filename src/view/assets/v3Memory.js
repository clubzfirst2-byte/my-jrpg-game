// @ts-check
// Graphics v3 (?v3=1): the memory measures of STYLE.md 10.1 that the game side can take now —
//   (3) left frames that are their right frame mirrored are not packed (placeholderPack.mirroredFrames;
//       sameMirrored tells them apart here)
//   (6) the CPU-side copies of the art are let go once on the GPU: each atlas's canvas (freeAtlasCanvases)
//       and each packed release sheet's decoded image (releaseSheetsLazily: kept only while a bundle is
//       cut from it, placeholderPack.SheetRef)
//   (1) a region's v3 art is in its region's bundle (placeholderPack.releaseV3RegionEntries), and
//   (5) the chunks' ground is not cached at 4 texture px per game px (gameView.buildChunkInner).
// cpuImageBytes is what the page itself keeps of the art in CPU memory (the measurement for ?debug and
// the E2E): the decoded sheets held, the atlas canvases not freed.
import { SheetRef } from './placeholderPack.js';

/** @type {SheetRef[]} */
const refs = [];

/**
 * Turns the packed sheets of the art sources into SheetRefs (one per sheet), so their decoded images
 * are let go between bundle builds. The sources are changed in place. Every ref still holds its image
 * until its first build, or until dropIdleSheets.
 * @param {Map<string, import('./placeholderPack.js').ArtSource>} overrides
 */
export function releaseSheetsLazily(overrides) {
  /** @type {Map<any, SheetRef>} */
  const byImage = new Map();
  for (const [k, v] of overrides) {
    if (typeof v !== 'object' || !('sheet' in v) || v.sheet instanceof SheetRef || !(v.sheet instanceof HTMLImageElement)) continue;
    let ref = byImage.get(v.sheet);
    if (!ref) {
      ref = new SheetRef(v.sheet);
      byImage.set(v.sheet, ref);
      refs.push(ref);
    }
    overrides.set(k, { ...v, sheet: ref });
  }
}

/** Lets go the decoded images of sheets no bundle is being cut from (after the first bundles are built). */
export function dropIdleSheets() {
  for (const r of refs) if (r.users === 0) r.image = null;
}

/**
 * Uploads a bundle's atlases to the GPU now and frees their CPU-side canvases (the GPU copy is all that
 * is drawn; a lost WebGL context then reloads the page: main.js).
 * @param {any} renderer PixiJS renderer @param {import('./assetManager.js').BuiltBundle} bundle
 */
export function freeAtlasCanvases(renderer, bundle) {
  for (const { canvas, source } of bundle.canvases ?? []) {
    renderer.texture.initSource(source);
    canvas.width = 0;
    canvas.height = 0;
  }
}

/** @type {HTMLCanvasElement | null} */
let scratch = null;

/**
 * Whether `left` is `right` mirrored left to right, pixel for pixel.
 * @param {CanvasImageSource & { width: number, height: number }} left @param {CanvasImageSource & { width: number, height: number }} right
 */
export function sameMirrored(left, right) {
  const w = left.width;
  const h = left.height;
  if (w !== right.width || h !== right.height || !w || !h) return false;
  scratch ??= document.createElement('canvas');
  scratch.width = w * 2;
  scratch.height = h;
  const ctx = /** @type {CanvasRenderingContext2D} */ (scratch.getContext('2d', { willReadFrequently: true }));
  ctx.clearRect(0, 0, w * 2, h);
  ctx.drawImage(left, 0, 0);
  ctx.save();
  ctx.translate(w * 2, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(right, 0, 0);
  ctx.restore();
  const a = ctx.getImageData(0, 0, w, h).data;
  const b = ctx.getImageData(w, 0, w, h).data;
  let same = a.length === b.length;
  for (let i = 0; same && i < a.length; i++) if (a[i] !== b[i]) same = false;
  scratch.width = scratch.height = 0;
  return same;
}

/**
 * The art the page keeps in CPU memory, bytes (RGBA): the decoded release sheets still referenced, and
 * the atlas canvases of the loaded bundles not freed.
 * @param {Map<string, import('./placeholderPack.js').ArtSource>} overrides
 * @param {import('./assetManager.js').AssetManager} assets
 */
export function cpuImageBytes(overrides, assets) {
  const sheets = new Set();
  let sheetBytes = 0;
  for (const v of overrides.values()) {
    if (typeof v !== 'object' || !('sheet' in v) || sheets.has(v.sheet)) continue;
    sheets.add(v.sheet);
    const img = v.sheet instanceof SheetRef ? v.sheet.image : /** @type {HTMLImageElement} */ (v.sheet);
    if (img) sheetBytes += img.naturalWidth * img.naturalHeight * 4;
  }
  let atlasBytes = 0;
  for (const { bundle } of assets.loaded.values()) for (const { canvas } of bundle.canvases ?? []) atlasBytes += canvas.width * canvas.height * 4;
  return { total: sheetBytes + atlasBytes, sheets: sheetBytes, atlases: atlasBytes, sheetCount: sheets.size };
}
