// @ts-check
// gfx W1 (inspection fix, perf): the v2 water as a layer of its own, under the chunks' cached ground.
// The water keys (shallow / deep water, the deep-edge and shore-foam overlays: 32 tiles, 4 frames
// each) are drawn into ONE small shared texture, the water atlas (WaterAtlas), at the current frame;
// each chunk's water is one static mesh of quads (waterQuads) whose texture coordinates point into that
// atlas. When the water frame changes, only the atlas is drawn again (32 tiles, once for every chunk):
// no chunk cache is redrawn, and the meshes do not change. The land above the water (its overlays over
// water included) stays in the chunk's cache, transparent where the water shows.

import { Container, Mesh, MeshGeometry, RenderTexture, Sprite } from 'pixi.js';

/** The water keys (without the frame), in the atlas's slot order. */
export const WATER_KEYS = Object.freeze([
  'tile.water',
  'tile.water.v1',
  'tile.water.deep',
  'tile.water.deep.v1',
  ...Array.from({ length: 14 }, (_, m) => `tile.water.deep.edge.${m + 1}`),
  ...Array.from({ length: 14 }, (_, m) => `tile.water.foam.${m + 1}`),
]);

/** A tile's size and its slot's (1 px of room on each side) in game px; slots per atlas row. */
const TILE = 16;
const SLOT = TILE + 2;
const PER_ROW = 8;
export const ATLAS_W = PER_ROW * SLOT;
export const ATLAS_H = Math.ceil(WATER_KEYS.length / PER_ROW) * SLOT;

/** The top-left of a water key's tile in the atlas, in game px, or null for a key it does not hold. @param {string} key @returns {[number, number] | null} */
export function waterSlot(key) {
  const n = WATER_KEYS.indexOf(key);
  if (n < 0) return null;
  return [(n % PER_ROW) * SLOT + 1, Math.floor(n / PER_ROW) * SLOT + 1];
}

/**
 * The quads of a chunk's water: one per piece (a display tile's water layer, or a quarter of a cell's
 * water tile), clipped to the chunk's area (its cache's area: the display tiles on its border are drawn
 * by both chunks, each its own part). Bottom first, as the pieces come.
 * @param {{ key: string, x: number, y: number, quarter: string | null }[]} pieces x, y: the piece's top-left in game px;
 *   quarter: "<n|s><e|w>", the quarter of the tile drawn there (8 × 8 px), or null for the whole tile
 * @param {{ x: number, y: number, width: number, height: number }} area
 * @returns {{ positions: Float32Array, uvs: Float32Array, indices: Uint32Array, keys: string[], skipped: string[] }}
 *   keys: the pieces' keys drawn; skipped: the keys the atlas does not hold
 */
export function waterQuads(pieces, area) {
  /** @type {number[]} */
  const pos = [];
  /** @type {number[]} */
  const uv = [];
  /** @type {number[]} */
  const idx = [];
  /** @type {string[]} */
  const keys = [];
  /** @type {string[]} */
  const skipped = [];
  for (const p of pieces) {
    const slot = waterSlot(p.key);
    if (!slot) {
      skipped.push(p.key);
      continue;
    }
    const size = p.quarter ? TILE / 2 : TILE;
    const qx = p.quarter?.endsWith('e') ? TILE / 2 : 0;
    const qy = p.quarter?.startsWith('s') ? TILE / 2 : 0;
    const x0 = Math.max(p.x, area.x);
    const y0 = Math.max(p.y, area.y);
    const x1 = Math.min(p.x + size, area.x + area.width);
    const y1 = Math.min(p.y + size, area.y + area.height);
    if (x1 <= x0 || y1 <= y0) continue;
    // the clipped quad's corners in the tile (game px), then in the atlas (0..1)
    const u0 = (slot[0] + qx + (x0 - p.x)) / ATLAS_W;
    const u1 = (slot[0] + qx + (x1 - p.x)) / ATLAS_W;
    const v0 = (slot[1] + qy + (y0 - p.y)) / ATLAS_H;
    const v1 = (slot[1] + qy + (y1 - p.y)) / ATLAS_H;
    const n = pos.length / 2;
    pos.push(x0, y0, x1, y0, x1, y1, x0, y1);
    uv.push(u0, v0, u1, v0, u1, v1, u0, v1);
    idx.push(n, n + 1, n + 2, n, n + 2, n + 3);
    keys.push(p.quarter ? `${p.key}#${p.quarter}` : p.key);
  }
  return { positions: new Float32Array(pos), uvs: new Float32Array(uv), indices: new Uint32Array(idx), keys, skipped };
}

/** The shared water atlas: the 32 water tiles at the current frame, drawn again when the frame changes. */
export class WaterAtlas {
  /**
   * @param {{ render: (options: { container: Container, target: RenderTexture, clear: boolean }) => void }} renderer
   * @param {(key: string) => import('pixi.js').Texture | null} textureOf the texture of "<key>.<frame>", or null when not loaded
   */
  constructor(renderer, textureOf) {
    this.renderer = renderer;
    this.textureOf = textureOf;
    this.texture = RenderTexture.create({ width: ATLAS_W, height: ATLAS_H, resolution: 2, antialias: false });
    this.texture.source.scaleMode = 'nearest';
    this.scene = new Container();
    /** @type {Sprite[]} */
    this.sprites = WATER_KEYS.map((key) => {
      const s = new Sprite();
      const [x, y] = /** @type {[number, number]} */ (waterSlot(key));
      s.position.set(x, y);
      this.scene.addChild(s);
      return s;
    });
    this.frame = -1;
    /** How many times the atlas was drawn (one per water frame shown). */
    this.renders = 0;
  }

  /** Draws the atlas at a frame (nothing when it already shows it). @param {number} frame */
  setFrame(frame) {
    if (frame === this.frame) return;
    this.frame = frame;
    WATER_KEYS.forEach((key, n) => {
      const tex = this.textureOf(`${key}.${frame}`);
      this.sprites[n].visible = !!tex;
      if (tex) this.sprites[n].texture = tex;
    });
    this.renderer.render({ container: this.scene, target: this.texture, clear: true });
    this.renders++;
  }

  /** A chunk's water mesh over this atlas. @param {ReturnType<typeof waterQuads>} quads */
  mesh(quads) {
    const geometry = new MeshGeometry({ positions: quads.positions, uvs: quads.uvs, indices: quads.indices });
    return new Mesh({ geometry, texture: this.texture });
  }

  destroy() {
    this.scene.destroy({ children: true });
    this.texture.destroy(true);
  }
}
