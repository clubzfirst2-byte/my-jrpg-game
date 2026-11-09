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
    expect(ART.size).toBe(62);
    for (const k of ART) expect(KEYS.has(k), k).toBe(true);
  });

  it('every object / switch / effect / icon / UI key of the game has release art or a deliberate fallback', () => {
    const missing = [...KEYS].filter((k) => OBJECT_LIKE.test(k) && !covered(k));
    expect(missing).toEqual([]);
    // the fallbacks are exactly what the art does not hold (terrain's, the beach ring)
    for (const k of fallback) expect(ART.has(k), k).toBe(false);
    expect(Object.keys(PLACEHOLDER_FALLBACK_KEYS).sort()).toEqual(['obj.star_ring.off', 'obj.star_ring.on']);
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
    expect(ICON_KEYS).toHaveLength(12);
    for (const k of ICON_KEYS) expect(ART.has(k), k).toBe(true);
    for (const it of items) expect(ART.has(iconFor(it.id)), it.id).toBe(true);
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
