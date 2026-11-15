import { describe, it, expect } from 'vitest';
import { GameView } from '../../src/view/gameView.js';
import { createGameState, MAPS } from '../../src/game/state.js';
import { regionAt } from '../../src/game/world/world.js';
import { Ground } from '../../src/game/world/tilemap.js';
import { forestFootProp, forestOpenProp, forestTreeNudge, LOG_SPACING_TILES } from '../../src/view/v3Forest.js';
import { addVillageProps, standClearOfProps, villageProps } from '../../src/game/world/villageProps.js';
import { hash01 } from '../../src/view/placement.js';

// In-game inspection of df638e6 (gfx_r1/inspect_v3_ingame.md): the pure parts of the fixes.

/** A view of a real map with only what the tree looks need (as in v3Forest.test.js). */
function mapView(name) {
  const state = createGameState(MAPS[name]);
  const v = Object.create(GameView.prototype);
  Object.assign(v, {
    v3: true, map: state.map, regions: state.regions, season: null, groundV2: true, v2Tiles: new Map(), sandUnderTrees: new Set(), v3Looks: new WeakMap(), v3Trees: null, v3Others: null, v3PineBanned: null,
    assets: { builders: { has: () => true }, hasTexture: () => true },
  });
  return { v, state };
}

describe('P3: the forest props repeat less', () => {
  it('fallen logs: no two within LOG_SPACING_TILES on the world map; fewer than before, still some', () => {
    const { v } = mapView('world');
    const logs = v.map.objects.filter((o) => o.type === 'tree' && regionAt(v.regions, o.tx, o.ty)?.id === 'forest' && v.v3TreeLook(o).what === 'prop');
    expect(logs.length).toBeGreaterThan(0);
    for (const a of logs) for (const b of logs) if (a !== b) expect(Math.max(Math.abs(a.tx - b.tx), Math.abs(a.ty - b.ty)), `${a.tx},${a.ty} ${b.tx},${b.ty}`).toBeGreaterThan(LOG_SPACING_TILES);
  });
  it('toadstools: 1 foot prop in 14 or fewer, and near trees on open moss about 1 in 8 of the props there', () => {
    let foot = 0;
    let toad = 0;
    let open = 0;
    let openToad = 0;
    for (let i = 0; i < 40000; i++) {
      const f = forestFootProp(hash01(i, 0, 5) * 0.34, hash01(i, 0, 6));
      if (f) foot++;
      if (f === 'toadstool') toad++;
      const o = forestOpenProp(0.9, 0, hash01(i, 0, 4), true);
      if (o) open++;
      if (o === 'toadstool') openToad++;
    }
    expect(toad / foot).toBeLessThan(1 / 12);
    expect(toad).toBeGreaterThan(0);
    expect(openToad / open).toBeLessThan(0.15);
  });
  it('the nudge of a forest tree: x within ±2, y 0..-3 (on its tile), mirrored for about half', () => {
    let flips = 0;
    const rows = new Set();
    for (let tx = 0; tx < 400; tx++) {
      const n = forestTreeNudge(tx, 7);
      expect(Math.abs(n.dx)).toBeLessThanOrEqual(2);
      expect(n.dy).toBeLessThanOrEqual(0);
      expect(n.dy).toBeGreaterThanOrEqual(-3);
      if (n.flip) flips++;
      rows.add(n.dy);
    }
    // (a row of trees on one map row gets 4 different foot lines)
    expect(rows.size).toBe(4);
    expect(flips).toBeGreaterThan(120);
    expect(flips).toBeLessThan(280);
  });
});

describe('P2: never inside the well (a place saved under ?v3=0)', () => {
  it('standing on the well\'s solid ring: moved to the nearest open tile of the same height; elsewhere not moved', () => {
    const state = createGameState(MAPS.world);
    addVillageProps(state);
    const map = state.map;
    const well = map.objects.find((o) => o.type === 'well');
    expect(well).toBeTruthy();
    const solid = villageProps(createGameState(MAPS.world).map, createGameState(MAPS.world).npcs).find((p) => p.type === 'well').solid;
    for (const [sx, sy] of solid) {
      const p = state.player;
      p.x = p.prevX = sx * 16 + 8;
      p.y = p.prevY = sy * 16 + 14;
      expect(standClearOfProps(state), `${sx},${sy}`).toBe(true);
      const tx = Math.floor(p.x / 16);
      const ty = Math.floor((p.y - 1) / 16);
      const i = ty * map.width + tx;
      expect(map.solid[i]).toBe(0);
      expect(map.ground[i]).not.toBe(Ground.WATER);
      expect(Math.max(Math.abs(tx - sx), Math.abs(ty - sy))).toBeLessThanOrEqual(2);
      // once out, it stays put
      expect(standClearOfProps(state)).toBe(false);
    }
    // the village square, away from the props: not moved
    const p = state.player;
    p.x = 28 * 16 + 8;
    p.y = 89 * 16 + 14;
    const before = [p.x, p.y];
    expect(standClearOfProps(state)).toBe(false);
    expect([p.x, p.y]).toEqual(before);
  });
});
