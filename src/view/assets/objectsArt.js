// @ts-check
// v1.0: the objects' release art (src/art-release/objects, docs/art-release/objects/PRODUCTION.md):
// buildings and furniture, chests, puzzle parts (sw.* and their map objects), item icons (icon.*),
// effects (fx.*) and the off-screen marker (ui.marker). 62 sprites named after the game's own keys,
// at 2 art pixels per game pixel, with the placeholders' anchors and frame counts (the house alone
// is taller: 96×112, approved). So no renaming is needed: once the group is loaded its frames replace
// the placeholders of the same names in every bundle (the base one and the region ones), and the
// existing view code (open / closed, on / off, the 2-frame fires, the effects' scale and alpha) draws
// them unchanged. The beach ring (obj.star_ring.off / .on, 48×52) is in the set too (base bundle).
//
//   normal play       loaded with the release hero (like the villagers and the enemies)
//   ?objects=placeholder   left out (before / after comparison); also left out with ?hd=0,
//                     ?hero=placeholder / ?hero=test and the prototype views (?…=proto)
//   ?objects=release  loaded even without the release hero
//
// Item icons are also shown in the HTML menus (inventory, shop): installItemIcons writes one CSS rule
// per icon that points into the build's packed sheet (or the dev server's own PNG), so nothing is
// copied into public/. Without the release art the rule holds the placeholder icon (a data URL).
import { iconFor } from '../itemView.js';
import { PALETTE, itemIcons } from './placeholderArt.js';

/** The release art group (folder under src/art-release). */
export const OBJECTS_GROUP = 'objects';

/**
 * Sprite keys of objects / effects / icons that the objects art deliberately does not draw:
 * the terrain producer's (src/art-release/terrain) and the ones still waiting for art.
 */
export const TERRAIN_OBJECT_KEYS = Object.freeze(['obj.tree', 'obj.rock', 'obj.bramble', 'obj.stump', 'obj.cactus']);
/**
 * Keys with no release art yet: they keep the placeholder (drawn at 1 art pixel per game pixel).
 * None now (the beach ring's art landed). A key's art is picked up by name once its file
 * src/art-release/objects/<key>.png is there; until then list it here, with the reason.
 * @type {Readonly<Record<string, string>>}
 */
export const PLACEHOLDER_FALLBACK_KEYS = Object.freeze({});

/**
 * Whether this view loads the objects' release art (see the top of the file).
 * @param {URLSearchParams} params
 * @param {{ releaseHero: boolean, protoGroups: readonly string[] }} art what else is loaded
 */
export function wantsObjectsArt(params, { releaseHero, protoGroups }) {
  const mode = params.get('objects');
  if (params.get('hd') === '0' || mode === 'placeholder' || protoGroups.length > 0) return false;
  return releaseHero || mode === 'release';
}

/** The release groups to load for the objects (none or [OBJECTS_GROUP]). @param {URLSearchParams} params @param {{ releaseHero: boolean, protoGroups: readonly string[] }} art */
export const objectsReleaseGroups = (params, art) => (wantsObjectsArt(params, art) ? [OBJECTS_GROUP] : []);

/** The item icon keys the game draws (icon.*). */
export const ICON_KEYS = Object.freeze(Object.keys(itemIcons()));

/** Icon size in the menus, CSS px (the art's own 20×20: crisp at any device pixel ratio). */
const ICON_CSS_PX = 20;

/** @param {string[]} rows @returns {string} a PNG data URL of a placeholder sprite (1 px per cell) */
function placeholderDataUrl(rows) {
  const c = document.createElement('canvas');
  c.width = rows[0].length;
  c.height = rows.length;
  const ctx = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
  rows.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      const color = PALETTE[/** @type {keyof typeof PALETTE} */ (row[x])];
      if (row[x] === '.' || !color) continue;
      ctx.fillStyle = color;
      ctx.fillRect(x, y, 1, 1);
    }
  });
  return c.toDataURL();
}

/**
 * The CSS background of one icon: its release art (its own PNG, or its place on the packed sheet),
 * else the placeholder.
 * @param {string} key @param {import('./placeholderPack.js').ArtSource | undefined} src @param {string[]} rows the placeholder
 */
export function iconBackground(key, src, rows) {
  if (typeof src === 'string') return `url("${src}") 0 0 / ${ICON_CSS_PX}px ${ICON_CSS_PX}px no-repeat`;
  if (src && 'src' in src.sheet && typeof src.sheet.src === 'string') {
    const img = /** @type {HTMLImageElement} */ (src.sheet);
    const k = ICON_CSS_PX / src.w;
    return `url("${img.src}") ${-src.x * k}px ${-src.y * k}px / ${img.naturalWidth * k}px ${img.naturalHeight * k}px no-repeat`;
  }
  return `url("${placeholderDataUrl(rows)}") 0 0 / ${ICON_CSS_PX}px ${ICON_CSS_PX}px no-repeat`;
}

/**
 * Writes (or rewrites) the menus' icon styles: `.item-icon[data-icon="icon.sword"]` … from the art in use.
 * @param {Map<string, import('./placeholderPack.js').ArtSource>} overrides the art in use, by sprite name
 * @param {Document} [doc]
 * @returns {{ key: string, release: boolean }[]} what each icon is drawn from
 */
export function installItemIcons(overrides, doc = document) {
  const icons = itemIcons();
  const rules = [`.item-icon{display:inline-block;flex:none;width:${ICON_CSS_PX}px;height:${ICON_CSS_PX}px;vertical-align:middle;image-rendering:pixelated;}`];
  const used = [];
  for (const key of ICON_KEYS) {
    const src = overrides.get(key);
    rules.push(`.item-icon[data-icon="${key}"]{background:${iconBackground(key, src, icons[key])};image-rendering:pixelated;}`);
    used.push({ key, release: !!src });
  }
  let style = /** @type {HTMLStyleElement | null} */ (doc.getElementById('item-icons'));
  if (!style) {
    style = doc.createElement('style');
    style.id = 'item-icons';
    doc.head.append(style);
  }
  style.textContent = rules.join('\n');
  return used;
}

/** A menu icon for an item (the same icon as the item lying on the ground). @param {string} itemId */
export function itemIconElement(itemId) {
  const el = document.createElement('span');
  el.className = 'item-icon';
  el.dataset.icon = iconFor(itemId);
  el.setAttribute('aria-hidden', 'true');
  return el;
}

/**
 * Test / check helpers (?debug API): the objects' art as drawn, and items put down for looking at.
 * @param {any} state the game state
 * @param {import('../gameView.js').GameView} view
 * @param {import('./assetManager.js').AssetManager} assets
 */
export function objectsDebugApi(state, view, assets) {
  /** @param {import('pixi.js').Texture} t */
  const art = (t) => ({ w: t.width, h: t.height, res: t.source.resolution });
  return {
    /** A sprite key's texture now: its size in game px and its art pixels per game pixel (2 = release art). */
    objectTexture: (/** @type {string} */ key) => (assets.hasTexture(key) ? { key, ...art(assets.texture(key)) } : null),
    /** The map objects, chests, checkpoints, fires, switches and pickups on screen now, with their texture. */
    objectSprites: () => {
      /** @param {import('pixi.js').Sprite} s */
      const find = (s) => {
        for (const { bundle } of assets.loaded.values()) for (const [k, t] of bundle.textures) if (t === s.texture) return k;
        return null;
      };
      /** @type {{ kind: string, key: string | null, w: number, h: number, res: number, visible: boolean, alpha: number, scale: number }[]} */
      const out = [];
      /** @param {string} kind @param {import('pixi.js').Sprite} s */
      const add = (kind, s) => out.push({ kind, key: find(s), ...art(s.texture), visible: s.visible, alpha: s.alpha, scale: s.scale.x });
      for (const { o, sprite } of view.objectSprites.values()) add(o.type, sprite);
      for (const c of view.features.chests) add('chest', c.sprite);
      for (const c of view.features.checkpoints) add('checkpoint', c.sprite);
      for (const f of view.features.fires) add('campfire', f.sprite);
      for (const s of view.puzzles.switches) add(s.kind, s.sprite);
      for (const s of view.items.sprites.values()) add('pickup', s);
      return out;
    },
    /** Puts an item down on a tile (it can be picked up as usual). */
    dropPickup: (/** @type {string} */ item, /** @type {number} */ tx, /** @type {number} */ ty) => {
      const ts = state.map.tileSize;
      state.pickups.push({ key: `debug${state.nextId++}`, item, count: 1, x: tx * ts + ts / 2, y: ty * ts + ts - 3, z: state.map.elev[ty * state.map.width + tx] });
    },
    /** The icon keys shown in the open menus now. */
    menuIcons: () => [...document.querySelectorAll('.item-icon')].map((el) => /** @type {HTMLElement} */ (el).dataset.icon),
    /**
     * For looking at both states of everything (use while paused: the next logic step recomputes the
     * switches): every switch, receiver and sconce on / off, every chest open, every checkpoint
     * touched, the beach ring open and the elder's charm home — or all of that back off.
     */
    forceObjectStates: (on = true) => {
      for (const s of state.switches) state.switchActive[s.id] = on;
      for (const o of state.map.objects) {
        if (o.type === 'receiver') o.on = on;
        if (o.type === 'sconce') o.lit = on;
      }
      const pr = state.progress;
      pr.openedChests = on ? state.chests.map((/** @type {any} */ c) => c.id) : [];
      pr.checkpoints = on ? state.checkpointDefs.map((/** @type {any} */ c) => c.id) : [];
      if (on) pr.flags.source_open = true;
      else delete pr.flags.source_open;
      if (on) pr.quests.lost_charm = 'done';
      else delete pr.quests.lost_charm;
      state.env.version++;
    },
  };
}
