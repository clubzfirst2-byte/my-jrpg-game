import { describe, it, expect, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';

// v1.0: the objects' release art in normal play (src/view/assets/objectsArt.js). The art files are
// named after the game's keys, so the mapping is the identity: these tests pin that every object,
// switch, icon, effect and UI key the game draws has release art or a deliberate fallback.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { REGION_ENTRIES, placeholderEntries } = await import('../../src/view/assets/placeholderPack.js');
const { OBJECTS_GROUP, TERRAIN_OBJECT_KEYS, PLACEHOLDER_FALLBACK_KEYS, ICON_KEYS, wantsObjectsArt, objectsReleaseGroups } = await import('../../src/view/assets/objectsArt.js');
const { iconFor } = await import('../../src/view/itemView.js');
const { createGameState, MAPS } = await import('../../src/game/state.js');
const { onDemandReleaseGroup } = await import('../../tools/precache.mjs');

const ART = new Set(readdirSync(new URL(`../../src/art-release/${OBJECTS_GROUP}/`, import.meta.url)).map((f) => f.replace(/\.png$/, '')));
const SEASONS = ['spring.', 'summer.', 'autumn.', 'winter.'];
const KEYS = new Set([...placeholderEntries(), ...Object.values(REGION_ENTRIES).flatMap((f) => f())].map((e) => e.key).filter((k) => !SEASONS.some((s) => k.startsWith(s))));
const OBJECT_LIKE = /^(obj|sw|fx|icon|ui)\./;
const fallback = new Set([...TERRAIN_OBJECT_KEYS, ...Object.keys(PLACEHOLDER_FALLBACK_KEYS)]);
/** release art, or a deliberate fallback */
const covered = (k) => ART.has(k) || fallback.has(k);

describe('objects release art: names → the game keys', () => {
  it('every release sprite is a key the game draws (no renaming needed)', () => {
    expect(ART.size).toBe(80); // 62 + the beach ring's 2 + the v1.0 icons (star shard, charm) + the v1.0.1 icons (6) + dishes (8)
    // v1.0.1 weapon / armour icons: drawn, not wired yet (itemView.js ICON_BY_ID + placeholder keys come next)
    const notYet = new Set(['icon.spear', 'icon.greatsword', 'icon.ember_sword', 'icon.star_sword', 'icon.cap', 'icon.boots',
      ...['grilled_meat', 'mushroom_skewer', 'berry_jam', 'hunter_stew', 'ember_soup', 'hearty_skewer', 'mixed_stew', 'dubious_food'].map((n) => `icon.dish.${n}`)]);
    for (const k of ART) if (!notYet.has(k)) expect(KEYS.has(k), k).toBe(true);
  });

  it('every object / switch / effect / icon / UI key of the game has release art or a deliberate fallback', () => {
    const missing = [...KEYS].filter((k) => OBJECT_LIKE.test(k) && !covered(k));
    expect(missing).toEqual([]);
    // terrain's keys are never in the objects art; nothing else falls back now — the beach ring has its art
    for (const k of TERRAIN_OBJECT_KEYS) expect(ART.has(k), k).toBe(false);
    expect(PLACEHOLDER_FALLBACK_KEYS).toEqual({});
    for (const k of ['obj.star_ring.off', 'obj.star_ring.on']) expect(ART.has(k), k).toBe(true);
  });

  it('every map object and switch of the world maps to a covered key, in each of its states', () => {
    const state = createGameState(MAPS.world);
    const STATES = { receiver: ['on', 'off'], sconce: ['on', 'off'], stone: ['on', 'off'], brazier: ['0', '1'], star_ring: ['on', 'off'], charm_shelf: ['', 'on'] };
    const types = new Set(state.map.objects.map((o) => o.type));
    for (const t of types) {
      if (t === 'tree') continue; // terrain (obj.tree / <region>.pine)
      const keys = (STATES[t] ?? ['']).map((s) => (s ? `obj.${t}.${s}` : `obj.${t}`));
      for (const k of keys) {
        expect(KEYS.has(k), k).toBe(true);
        expect(covered(k), k).toBe(true);
      }
    }
    for (const s of state.switches.filter((x) => x.kind === 'plate' || x.kind === 'sensor')) for (const st of ['on', 'off']) expect(ART.has(`sw.${s.kind}.${st}`), s.id).toBe(true);
    // chests, checkpoints and campfires (featureView), the fires and effects (envView, gameView)
    for (const k of ['obj.chest.open', 'obj.chest.closed', 'obj.checkpoint.on', 'obj.checkpoint.off', 'obj.campfire.0', 'obj.campfire.1', 'obj.cave', 'fx.fire.0', 'fx.fire.1', 'fx.smoke', 'fx.slash', 'fx.shield', 'fx.bow', 'fx.arrow', 'fx.orb', 'fx.shadow', 'fx.glider', 'fx.light', 'ui.marker']) {
      expect(ART.has(k), k).toBe(true);
    }
  });

  it('every item has an icon with release art (on the ground and in the menus)', () => {
    const items = JSON.parse(readFileSync(new URL('../../data/items.json', import.meta.url), 'utf8')).items;
    expect(ICON_KEYS).toHaveLength(14);
    for (const k of ICON_KEYS) expect(ART.has(k), k).toBe(true);
    for (const it of items) expect(ART.has(iconFor(it.id)), it.id).toBe(true);
    // key items have their own icons (v1.0), on the ground and in the menus
    expect(iconFor('star_shard')).toBe('icon.star_shard');
    expect(iconFor('lost_charm')).toBe('icon.charm');
    // the star's drawing ends higher (row 14): its feet sit at row 16 like the other icons' (row 18 + 1 empty row)
    const icons = placeholderEntries().filter((e) => e.key.startsWith('icon.'));
    expect(icons).toHaveLength(14);
    expect(icons.find((e) => e.key === 'icon.star_shard').anchor).toEqual([0.5, 0.8]);
    for (const e of icons.filter((x) => x.key !== 'icon.star_shard')) expect(e.anchor, e.key).toEqual([0.5, 1]);
  });
});

describe('objects release art: when it is loaded', () => {
  const p = (q) => new URLSearchParams(q);
  const normal = { releaseHero: true, protoGroups: [] };
  it('in normal play (with the release hero), not with ?objects=placeholder, ?hd=0 or the prototype views', () => {
    expect(objectsReleaseGroups(p(''), normal)).toEqual(['objects']);
    expect(wantsObjectsArt(p('objects=placeholder'), normal)).toBe(false);
    expect(wantsObjectsArt(p('hd=0'), normal)).toBe(false);
    expect(wantsObjectsArt(p('enemy=proto'), { releaseHero: true, protoGroups: ['enemy'] })).toBe(false);
    expect(wantsObjectsArt(p(''), { releaseHero: false, protoGroups: [] })).toBe(false);
    expect(wantsObjectsArt(p('objects=release'), { releaseHero: false, protoGroups: [] })).toBe(true);
  });
  it('is kept for offline play (precached)', () => {
    expect(onDemandReleaseGroup(OBJECTS_GROUP)).toBe(false);
  });
});

describe('objects release art: whole art pixels', () => {
  it('a burning tree draws its flames at a whole scale with the release art (2x), 1.6x with the placeholder', async () => {
    const { bigFireScale } = await import('../../src/view/envView.js');
    expect(bigFireScale(/** @type {any} */ ({ source: { resolution: 2 } }))).toBe(2);
    expect(bigFireScale(/** @type {any} */ ({ source: { resolution: 1 } }))).toBe(1.6);
    // art 2 px per game px, canvas 2 px per game px: at scale s one art px is s canvas px, so s must be
    // a whole number (1.5 would give art pixels 1 and 2 canvas px wide in turn)
    expect(Number.isInteger(bigFireScale(/** @type {any} */ ({ source: { resolution: 2 } })))).toBe(true);
  });
  it('the shock crystal lights the night in its own pale yellow with the release art, cyan with the placeholder', async () => {
    const { crystalLightColor } = await import('../../src/view/weatherView.js');
    expect(crystalLightColor(/** @type {any} */ ({ source: { resolution: 2 } }))).toBe(0xeeea88);
    expect(crystalLightColor(/** @type {any} */ ({ source: { resolution: 1 } }))).toBe(0x60d8ff);
  });
});

describe('the beach ring at night', () => {
  it('is lit (a blue light) only while it is open', async () => {
    const { starRingOpen, STAR_RING_LIGHT } = await import('../../src/view/weatherView.js');
    const st = (flags) => ({ progress: { flags }, opening: null });
    expect(starRingOpen(st({}))).toBe(false);
    expect(starRingOpen(st({ source_open: true }))).toBe(true);
    expect(starRingOpen(st({ source_open: true, ending_seen: true }))).toBe(false);
    expect(starRingOpen({})).toBe(false); // a minimal state (no progress yet) is not an error
    expect(STAR_RING_LIGHT).toEqual({ radius: 40, color: 0x7fe8ff });
  });
});
