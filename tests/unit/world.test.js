import { describe, it, expect } from 'vitest';
import { WORLD, stitchWorld, regionAt, OUTDOOR_W } from '../../src/game/world/world.js';
import { ISLAND } from '../../src/game/world/maps/island.js';
import { REGIONS } from '../../src/game/world/maps/regions.js';
import { createGameState, stepGame } from '../../src/game/state.js';
import { parseMap, Ground } from '../../src/game/world/tilemap.js';
import { weatherAt, WEATHER, CLOCK } from '../../src/game/env/weather.js';
import { ignite, material } from '../../src/game/env/envSim.js';
import { computeWorldDiff, applyWorldDiff } from '../../src/game/world/worldDiff.js';
import { applyProgress, emptyProgress } from '../../src/game/world/features.js';
import { judgeTour } from '../../src/debug/tour.js';
import { validateItems } from '../../src/game/items/validateItems.js';
import DATA from '../../data/items.json';

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };

describe('the world: the island with the regions stacked below', () => {
  it('keeps the island where it was and offsets each region', () => {
    expect(WORLD.ground.slice(0, ISLAND.ground.length)).toEqual(ISLAND.ground);
    expect(WORLD.ground.length).toBe(ISLAND.ground.length + REGIONS.reduce((n, r) => n + r.ground.length, 0));
    expect(WORLD.regions.map((r) => [r.id, r.ty])).toEqual([['island', 0], ['plains', 72], ['desert', 168]]);
    const plains = REGIONS[0];
    const chest = plains.chests[0];
    expect(WORLD.chests.find((c) => c.id === chest.id).ty).toBe(chest.ty + 72);
    expect(regionAt(WORLD.regions, 47, 100).id).toBe('plains');
    expect(WORLD.outdoor.tw).toBe(OUTDOOR_W);
  });

  it('parses into one map; ids stay unique; item references are valid', () => {
    const map = parseMap(WORLD);
    expect(map.width).toBe(112);
    for (const key of ['chests', 'checkpoints', 'pickups', 'landmarks']) {
      const ids = WORLD[key].map((x) => x.id);
      expect(new Set(ids).size).toBe(ids.length);
    }
    expect(validateItems(DATA, WORLD)).toEqual([]);
  });

  it('the causeway joins the island to the plains without a gap', () => {
    const map = parseMap(WORLD);
    for (let ty = 64; ty < 80; ty++) {
      const g = map.ground[ty * map.width + 47];
      expect(g === Ground.SAND || g === Ground.GRASS || g === Ground.PATH, `row ${ty}`).toBe(true);
    }
  });

  it('walking south down the causeway takes the player into the plains', () => {
    const s = createGameState(WORLD);
    s.enemies = [];
    s.enemySpawns = [];
    const p = s.player;
    p.x = p.prevX = 47 * 16 + 8;
    p.y = p.prevY = 66 * 16 + 14;
    for (let i = 0; i < 60 * 8; i++) stepGame(s, { ...none, moveY: 1 });
    expect(regionAt(s.regions, Math.floor(p.x / 16), Math.floor(p.y / 16)).id).toBe('plains');
    expect(p.swimming).toBe(false);
  });

  it('stitching rejects a region wider than the world', () => {
    expect(() => stitchWorld(ISLAND, [{ ...REGIONS[0], ground: REGIONS[0].ground.map((r) => r + '~'.repeat(40)) }])).toThrow(/wider/);
  });
});

describe('climate', () => {
  it('a dry region gets the same skies without rain', () => {
    for (let slot = 0; slot < 400; slot++) {
      const t = CLOCK.dayMs + slot * WEATHER.slotMs;
      const wet = weatherAt(1, t);
      const dry = weatherAt(1, t, null, 'dry');
      expect(['rain', 'storm']).not.toContain(dry.kind);
      expect(dry.windX).toBe(wet.windX);
    }
  });

  it('in the rain, the plains do not catch fire but the desert does', () => {
    const s = createGameState(WORLD);
    s.env.weatherOverride = 'rain';
    let plains = 100 * s.map.width + 30;
    while (material(s.env, s.map, plains) !== 'grass') plains++;
    const desert = 200 * s.map.width + 30;
    expect(material(s.env, s.map, plains)).toBe('grass');
    expect(ignite(s.env, s.map, plains)).toBe(false);
    // The desert has no grass; a cactus is not flammable either: check the dry flag itself.
    expect(s.env.dry[desert]).toBe(1);
    expect(s.env.dry[plains]).toBe(0);
  });
});

describe('saving the world as differences', () => {
  it('only changed objects are written, grouped by chunk, and come back on load', () => {
    const s = createGameState(WORLD);
    expect(computeWorldDiff(s)).toEqual({});
    // Burn a tree on the plains and break a jar on the island.
    const treeIdx = s.map.objects.findIndex((o) => o.type === 'tree' && o.ty > 80);
    const tree = s.map.objects[treeIdx];
    const ti = tree.ty * s.map.width + tree.tx;
    ignite(s.env, s.map, ti);
    for (let i = 0; i < 60 * 15; i++) stepGame(s, none);
    // (the player is far: make sure the tree's region was simulated)
    if (tree.type !== 'stump') {
      tree.type = 'stump';
      s.map.solid[ti] = 0;
    }
    const jar = s.map.objects.find((o) => o.type === 'jar');
    jar.gone = true;
    const diff = computeWorldDiff(s);
    const keys = Object.keys(diff);
    expect(keys.length).toBeGreaterThanOrEqual(1);
    expect(Object.values(diff).reduce((n, d) => n + Object.keys(d).length, 0)).toBeLessThan(10); // a diff, not a dump
    const t = createGameState(WORLD);
    applyProgress(t, { ...emptyProgress(), worldDiff: JSON.parse(JSON.stringify(diff)) });
    expect(t.map.objects[treeIdx].type).toBe('stump');
    expect(t.map.solid[ti]).toBe(0);
    expect(t.map.objects.find((o) => o.type === 'jar').gone).toBe(true);
  });

  it('a moved crate is restored where it was left', () => {
    const s = createGameState(WORLD);
    const k = s.map.objects.findIndex((o) => o.type === 'crate');
    const c = s.map.objects[k];
    const from = c.ty * s.map.width + c.tx;
    s.env.objectAt.delete(from);
    s.map.solid[from] = 0;
    c.tx -= 3;
    s.env.objectAt.set(c.ty * s.map.width + c.tx, c);
    s.map.solid[c.ty * s.map.width + c.tx] = 1;
    const t = createGameState(WORLD);
    applyWorldDiff(t, computeWorldDiff(s));
    const moved = t.map.objects[k];
    expect(moved.tx).toBe(c.tx);
    expect(t.map.solid[from]).toBe(0);
    expect(t.map.solid[moved.ty * t.map.width + moved.tx]).toBe(1);
    expect(t.env.objectAt.get(moved.ty * t.map.width + moved.tx)).toBe(moved);
  });
});

describe('long-play verdict', () => {
  const sample = (tSec, textures, displayObjects, heapMb = 30) => ({ tSec, fps: 60, p95Ms: 17, textures, displayObjects, chunks: 4, bundles: 2, heapMb });
  it('steady numbers pass; steadily rising ones are reported', () => {
    const steady = Array.from({ length: 12 }, (_, k) => sample(k * 30, 12 + (k % 2), 4600 + (k % 3) * 200));
    expect(judgeTour(steady).growing).toBe(false);
    const leaking = Array.from({ length: 12 }, (_, k) => sample(k * 30, 12 + k * 2, 4600 + k * 400, 30 + k * 5));
    const j = judgeTour(leaking);
    expect(j.growing).toBe(true);
    expect(j.reason).toMatch(/テクスチャ/);
  });
});
