// @ts-check
// Loads / releases textures in bundles and resolves them by logical name (DESIGN.md 2.2, 7.5).
// Game code never refers to file paths: swapping the placeholder pack for production art only
// changes which pack is registered.

/**
 * @typedef {object} SpriteMeta
 * @property {[number, number]} anchor  0..1, usually feet = [0.5, 1]
 * @property {boolean} [flipX]  graphics v3: the texture is the right-facing frame, drawn mirrored
 */

/**
 * @typedef {object} BuiltBundle
 * @property {Map<string, import('pixi.js').Texture>} textures
 * @property {Map<string, SpriteMeta>} meta
 * @property {() => void} destroy  releases GPU memory
 * @property {{ canvas: HTMLCanvasElement, source: import('pixi.js').TextureSource }[]} [canvases] the atlases' CPU-side
 *   canvases (graphics v3: freed once on the GPU, AssetManager.onBuilt)
 */

/** @typedef {() => Promise<BuiltBundle> | BuiltBundle} BundleBuilder */

export class AssetManager {
  constructor() {
    /** @type {Map<string, BundleBuilder>} */
    this.builders = new Map();
    /** @type {Map<string, { refs: number, bundle: BuiltBundle }>} */
    this.loaded = new Map();
    /** Goes up whenever a bundle comes or goes (what hasTexture answers may have changed). */
    this.version = 0;
    /**
     * Called with each bundle once it is built, before it is used (graphics v3: upload its atlases to
     * the GPU and free their CPU-side canvases; main.js). @type {((bundle: BuiltBundle) => void) | null}
     */
    this.onBuilt = null;
  }

  /** @param {string} name @param {BundleBuilder} builder */
  register(name, builder) {
    this.builders.set(name, builder);
  }

  /** Loads a bundle (reference counted). @param {string} name */
  async load(name) {
    const existing = this.loaded.get(name);
    if (existing) {
      existing.refs++;
      return;
    }
    const builder = this.builders.get(name);
    if (!builder) throw new Error(`Unknown asset bundle "${name}"`);
    const bundle = await builder();
    this.onBuilt?.(bundle);
    this.loaded.set(name, { refs: 1, bundle });
    this.version++;
  }

  /** Releases one reference; destroys the textures when nobody uses the bundle. @param {string} name */
  unload(name) {
    const entry = this.loaded.get(name);
    if (!entry) return;
    entry.refs--;
    if (entry.refs <= 0) {
      entry.bundle.destroy();
      this.loaded.delete(name);
      this.version++;
    }
  }

  /** @param {string} name */
  isLoaded(name) {
    return this.loaded.has(name);
  }

  /** One more reference to an already loaded bundle (P8: a chunk using its art). @param {string} name */
  retain(name) {
    const entry = this.loaded.get(name);
    if (!entry) throw new Error(`Asset bundle "${name}" is not loaded`);
    entry.refs++;
  }

  /** Whether a texture is loaded right now (P10.4: bosses are drawn by their region's bundle). @param {string} key */
  hasTexture(key) {
    for (const { bundle } of this.loaded.values()) if (bundle.textures.has(key)) return true;
    return false;
  }

  /** @param {string} key logical name, e.g. "player.walk.down.0" */
  texture(key) {
    for (const { bundle } of this.loaded.values()) {
      const t = bundle.textures.get(key);
      if (t) return t;
    }
    throw new Error(`Texture "${key}" is not loaded`);
  }

  /** @param {string} key @returns {SpriteMeta} */
  meta(key) {
    for (const { bundle } of this.loaded.values()) {
      const m = bundle.meta.get(key);
      if (m) return m;
    }
    return { anchor: [0, 0] };
  }

  stats() {
    let textures = 0;
    for (const { bundle } of this.loaded.values()) textures += bundle.textures.size;
    return { bundles: this.loaded.size, textures };
  }
}
