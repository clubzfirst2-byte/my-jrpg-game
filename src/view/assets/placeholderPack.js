// @ts-check
// Builds the placeholder art into ONE atlas texture so everything batches into few draw calls.
// A production pack must provide the same logical names and anchors (DESIGN.md 7.5).
import { Rectangle, Texture } from 'pixi.js';
import { LEVEL_PX } from '../../game/world/tilemap.js';
import {
  PALETTE,
  archerFrames,
  arrowSprite,
  beastFrames,
  bowSprite,
  orbSprite,
  shieldSprite,
  slashSprite,
  earthFace,
  grassTile,
  pathTile,
  playerFrames,
  gliderSprite,
  rampSprite,
  rockSprite,
  ruinFace,
  ruinFloorTile,
  shadowSprite,
  swimFrames,
  treeSprite,
  waterTile,
  sandTile,
  chestSprite,
  checkpointSprite,
  campfireFrames,
  smokeSprite,
  caveSprite,
  markerSprite,
  metalTile,
  fireFrames,
  brambleSprite,
  crystalSprite,
  jarSprite,
  receiverSprite,
  doorSprite,
  brazierFrames,
  stumpSprite,
} from './placeholderArt.js';

const FEET = /** @type {[number, number]} */ ([0.5, 1]);
const TOP_LEFT = /** @type {[number, number]} */ ([0, 0]);

/** @returns {{ key: string, rows: string[], anchor: [number, number] }[]} */
export function placeholderEntries() {
  const entries = [];
  for (const [key, rows] of Object.entries(playerFrames())) entries.push({ key, rows, anchor: FEET });
  for (const [key, rows] of Object.entries(swimFrames())) entries.push({ key, rows, anchor: FEET });
  for (let i = 0; i < 3; i++) entries.push({ key: `tile.grass.${i}`, rows: grassTile(100 + i), anchor: TOP_LEFT });
  entries.push({ key: 'tile.path', rows: pathTile(), anchor: TOP_LEFT });
  for (let i = 0; i < 2; i++) entries.push({ key: `tile.water.${i}`, rows: waterTile(i), anchor: TOP_LEFT });
  entries.push({ key: 'tile.ruin', rows: ruinFloorTile(), anchor: TOP_LEFT });
  entries.push({ key: 'tile.ramp', rows: rampSprite(LEVEL_PX), anchor: TOP_LEFT });
  // Cliff face segments: face.<material>.<top|mid><bottom?>.<4|8>
  for (const [mat, face] of /** @type {const} */ ([['earth', earthFace], ['ruin', ruinFace]])) {
    for (const h of [4, 8]) {
      for (const top of [true, false]) {
        for (const bottom of [true, false]) {
          const key = `face.${mat}.${top ? 'top' : 'mid'}${bottom ? '-base' : ''}.${h}`;
          entries.push({ key, rows: face(h, top, bottom), anchor: TOP_LEFT });
        }
      }
    }
  }
  entries.push({ key: 'fx.glider', rows: gliderSprite(), anchor: FEET });
  entries.push({ key: 'fx.shadow', rows: shadowSprite(), anchor: /** @type {[number, number]} */ ([0.5, 0.5]) });
  entries.push({ key: 'px', rows: ['XX', 'XX'], anchor: TOP_LEFT });
  entries.push({ key: 'obj.rock', rows: rockSprite(), anchor: FEET });
  const CENTER = /** @type {[number, number]} */ ([0.5, 0.5]);
  for (const [key, rows] of Object.entries({ ...beastFrames(), ...archerFrames() })) entries.push({ key, rows, anchor: FEET });
  entries.push({ key: 'fx.slash', rows: slashSprite(), anchor: CENTER });
  entries.push({ key: 'fx.arrow', rows: arrowSprite(), anchor: CENTER });
  entries.push({ key: 'fx.orb', rows: orbSprite(), anchor: CENTER });
  entries.push({ key: 'fx.shield', rows: shieldSprite(), anchor: CENTER });
  entries.push({ key: 'fx.bow', rows: bowSprite(), anchor: CENTER });
  entries.push({ key: 'obj.tree', rows: treeSprite(), anchor: FEET });
  // P3.5 island features.
  entries.push({ key: 'tile.sand', rows: sandTile(), anchor: TOP_LEFT });
  entries.push({ key: 'obj.chest.closed', rows: chestSprite(false), anchor: FEET });
  entries.push({ key: 'obj.chest.open', rows: chestSprite(true), anchor: FEET });
  entries.push({ key: 'obj.checkpoint.off', rows: checkpointSprite(false), anchor: FEET });
  entries.push({ key: 'obj.checkpoint.on', rows: checkpointSprite(true), anchor: FEET });
  for (const [key, rows] of Object.entries(campfireFrames())) entries.push({ key, rows, anchor: FEET });
  entries.push({ key: 'fx.smoke', rows: smokeSprite(), anchor: CENTER });
  entries.push({ key: 'obj.cave', rows: caveSprite(), anchor: FEET });
  entries.push({ key: 'ui.marker', rows: markerSprite(), anchor: CENTER });
  // P4 environment.
  entries.push({ key: 'tile.metal', rows: metalTile(), anchor: TOP_LEFT });
  for (const [key, rows] of Object.entries(fireFrames())) entries.push({ key, rows, anchor: FEET });
  for (const [key, rows] of Object.entries(brazierFrames())) entries.push({ key, rows, anchor: FEET });
  entries.push({ key: 'obj.bramble', rows: brambleSprite(), anchor: FEET });
  entries.push({ key: 'obj.crystal', rows: crystalSprite(), anchor: FEET });
  entries.push({ key: 'obj.jar', rows: jarSprite(), anchor: FEET });
  entries.push({ key: 'obj.receiver.off', rows: receiverSprite(false), anchor: FEET });
  entries.push({ key: 'obj.receiver.on', rows: receiverSprite(true), anchor: FEET });
  entries.push({ key: 'obj.door', rows: doorSprite(), anchor: FEET });
  entries.push({ key: 'obj.stump', rows: stumpSprite(), anchor: FEET });
  return entries;
}

/** @returns {import('./assetManager.js').BuiltBundle} */
export function buildPlaceholderPack() {
  const entries = placeholderEntries();
  const ATLAS = 256;
  const PAD = 1;
  const canvas = document.createElement('canvas');
  canvas.width = ATLAS;
  canvas.height = ATLAS;
  const ctx = /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d'));

  /** @type {Map<string, { x: number, y: number, w: number, h: number }>} */
  const rects = new Map();
  let x = 0;
  let y = 0;
  let shelf = 0;
  for (const e of entries) {
    const w = e.rows[0].length;
    const h = e.rows.length;
    if (x + w > ATLAS) {
      x = 0;
      y += shelf + PAD;
      shelf = 0;
    }
    if (y + h > ATLAS) throw new Error('Placeholder atlas is full');
    for (let py = 0; py < h; py++) {
      for (let px = 0; px < w; px++) {
        const c = e.rows[py][px];
        if (c === '.') continue;
        const color = PALETTE[/** @type {keyof typeof PALETTE} */ (c)];
        if (!color) throw new Error(`Unknown palette key "${c}" in ${e.key}`);
        ctx.fillStyle = color;
        ctx.fillRect(x + px, y + py, 1, 1);
      }
    }
    rects.set(e.key, { x, y, w, h });
    x += w + PAD;
    shelf = Math.max(shelf, h);
  }

  const base = Texture.from(canvas);
  base.source.scaleMode = 'nearest';
  /** @type {Map<string, Texture>} */
  const textures = new Map();
  /** @type {Map<string, import('./assetManager.js').SpriteMeta>} */
  const meta = new Map();
  for (const e of entries) {
    const r = /** @type {{ x: number, y: number, w: number, h: number }} */ (rects.get(e.key));
    textures.set(e.key, new Texture({ source: base.source, frame: new Rectangle(r.x, r.y, r.w, r.h) }));
    meta.set(e.key, { anchor: e.anchor });
  }
  return {
    textures,
    meta,
    destroy() {
      for (const t of textures.values()) t.destroy(false);
      base.destroy(true);
    },
  };
}
