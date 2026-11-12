import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { createGameState, MAPS } from '../../src/game/state.js';
import { villageProps, addVillageProps, VILLAGE_PROP_TYPES } from '../../src/game/world/villageProps.js';
import { computeWorldDiff, objectBaseline } from '../../src/game/world/worldDiff.js';
import { V3_VILLAGE_KEYS, V3_VILLAGE_TYPES, V3_WINTER_OBJECTS, villageSources, winterObjectKeys, v3VillageBundle } from '../../src/view/assets/villageV3.js';
import { atlasSizeFor } from '../../src/view/assets/placeholderPack.js';
import { decodePng } from '../../tools/release-art-pack.mjs';

// Graphics v3: the village (VILLAGE.md): its new things placed by rules read off the map, solid where
// drawn and never in a save; its art in bundles of its own per season (measures 1 + 2, 0.90 MB).

const OBJ = readdirSync(new URL('../../src/art-release-v3/objects/', import.meta.url)).map((f) => f.slice(0, -4));
const OVERRIDES = new Map(OBJ.map((k) => [k, k]));

describe('village props (fences, well, signposts)', () => {
  const state = createGameState(MAPS.world);
  const props = villageProps(state.map, state.npcs);
  it('fences between the houses of a row (a gate in the middle), a well near the middle, a sign where the road leaves', () => {
    const kinds = props.map((p) => p.type);
    expect(kinds.filter((k) => k === 'fence').length).toBeGreaterThanOrEqual(4);
    expect(kinds.filter((k) => k === 'well').length).toBe(1);
    expect(kinds.filter((k) => k === 'signpost').length).toBeGreaterThanOrEqual(1);
    for (const p of props) expect(VILLAGE_PROP_TYPES).toContain(p.type);
    // each fence run starts with "l" and ends with "r"
    const fences = props.filter((p) => p.type === 'fence').sort((a, b) => a.ty - b.ty || a.tx - b.tx);
    for (let n = 0; n < fences.length; n++) {
      const f = fences[n];
      const left = fences.some((g) => g.ty === f.ty && g.tx === f.tx - 1);
      const right = fences.some((g) => g.ty === f.ty && g.tx === f.tx + 1);
      expect(f.kind).toBe(left && right ? 'h' : left ? 'r' : right ? 'l' : 'post');
    }
  });
  it('only on free grass: never on a path, a door\'s front, a house, a tree or next to a villager; solid where drawn', () => {
    const m = state.map;
    const houses = m.objects.filter((o) => o.type === 'house');
    for (const p of props) {
      for (const [x, y] of p.solid) {
        const i = y * m.width + x;
        expect(m.solid[i], `${p.type} ${x},${y}`).toBe(0);
        expect(m.objects.some((o) => o.tx === x && o.ty === y)).toBe(false);
        expect(houses.some((h) => h.tx === x && h.ty + 1 === y)).toBe(false);
        for (const n of state.npcs) expect(Math.max(Math.abs(Math.floor(n.x / 16) - x), Math.abs(Math.floor(n.y / 16) - y))).toBeGreaterThanOrEqual(2);
      }
    }
    const s2 = createGameState(MAPS.world);
    const before = s2.map.solid.reduce((a, b) => a + b, 0);
    const n = addVillageProps(s2);
    expect(n).toBe(props.length);
    expect(s2.map.solid.reduce((a, b) => a + b, 0) - before).toBe(props.reduce((a, p) => a + p.solid.length, 0));
    // the well's bottom row (2 tiles) is solid, its roof row is walked behind
    const well = props.find((p) => p.type === 'well');
    expect(well.solid).toEqual([[well.tx - 1, well.ty], [well.tx, well.ty]]);
  });
  it('never in a save: they come after the baseline, and the world diff stays empty', () => {
    const s = createGameState(MAPS.world);
    const base = objectBaseline(s.map.objects).length;
    addVillageProps(s);
    expect(s.objectBaseline.length).toBe(base);
    expect(computeWorldDiff(s)).toEqual({});
  });
});

describe('village art bundles (VILLAGE.md 4.0: measures 1 + 2)', () => {
  it('the village bundle holds the village\'s house kinds, fences, well and signposts — not the common objects', () => {
    for (const s of ['summer', 'autumn', 'winter']) {
      const src = villageSources(s, OVERRIDES);
      expect([...src.keys()].sort()).toEqual([...V3_VILLAGE_KEYS].sort());
      // a season's own file where it has one, else summer's
      expect(src.get('obj.house')).toBe(s === 'summer' ? 'obj.house' : `${s}.obj.house`);
      expect(src.get('obj.v3.well')).toBe(s === 'winter' ? 'winter.obj.v3.well' : 'obj.v3.well');
      for (const k of V3_WINTER_OBJECTS) expect(src.has(k)).toBe(false);
    }
    expect(v3VillageBundle('spring')).toBe('v3:village:summer');
    expect(V3_VILLAGE_TYPES).toEqual(['house', 'fence', 'well', 'signpost']);
  });
  it('a season of the village bundle is 0.90 MB or less (atlas, RGBA)', () => {
    for (const s of ['summer', 'autumn', 'winter']) {
      const entries = [...villageSources(s, OVERRIDES).values()].map((k) => {
        const img = decodePng(readFileSync(new URL(`../../src/art-release-v3/objects/${k}.png`, import.meta.url)));
        return { rows: [], image: { width: img.width, height: img.height } };
      });
      entries.sort((a, b) => b.image.height - a.image.height);
      const { width, height } = atlasSizeFor(entries, { exactHeight: true });
      expect(width * height * 4, s).toBeLessThanOrEqual(0.9e6);
    }
  });
  it('the winter look of the common objects: every one with a winter file, never the open chest', () => {
    const keys = winterObjectKeys(OVERRIDES);
    expect(keys.length).toBe(V3_WINTER_OBJECTS.length);
    expect(keys).not.toContain('winter.obj.chest.open');
    expect(V3_WINTER_OBJECTS).not.toContain('obj.chest.open');
    expect(OBJ).not.toContain('winter.obj.chest.open');
  });
  it('VILLAGE.md lists the keys this uses', () => {
    const doc = readFileSync(new URL('../../docs/art-release-v3/VILLAGE.md', import.meta.url), 'utf8');
    for (const k of [...V3_VILLAGE_KEYS, ...V3_WINTER_OBJECTS]) expect(doc.includes(k.replace(/\.(?:[01]|off|on|closed|h|l|r|post)$/, '')), k).toBe(true);
  });
});
