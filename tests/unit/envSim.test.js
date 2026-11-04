import { describe, it, expect } from 'vitest';
import { parseMap } from '../../src/game/world/tilemap.js';
import { createEnv, stepEnv, ignite, wet, material, ENV, envSummary } from '../../src/game/env/envSim.js';

/** A w x h map of grass (with optional rows replaced). */
function field(w, h, rows = {}) {
  const ground = [];
  for (let y = 0; y < h; y++) ground.push(rows[y] ?? '.'.repeat(w));
  const map = parseMap(ground);
  return map;
}
const at = (map, tx, ty) => ty * map.width + tx;
const px = (tx, ty) => ({ x: tx * 16 + 8, y: ty * 16 + 14 });
/** Runs the env for ms of game time in 1/60 s steps. */
function run(env, map, player, ms, budget) {
  const n = Math.round(ms / (1000 / 60));
  for (let k = 0; k < n; k++) stepEnv(env, map, player, 1000 / 60, budget);
}
/** Snapshot of everything the rules decide. */
const snapshot = (env) =>
  JSON.stringify([...env.cells.entries()].sort((a, b) => a[0] - b[0]).map(([i, c]) => [i, Math.max(0, Math.round(c.burnMs)), c.ashUntil, c.wetUntil, env.burning.has(i)]));

describe('fire', () => {
  it('spreads through grass, burns out to ash, and the grass grows back later', () => {
    const map = field(12, 12);
    const env = createEnv(map, map.objects);
    const me = px(1, 1);
    expect(ignite(env, map, at(map, 6, 6))).toBe(true);
    run(env, map, me, 2000);
    expect(env.burning.size).toBeGreaterThan(1); // it spread
    run(env, map, me, 30_000);
    expect(env.burning.size).toBe(0); // all burnt out
    expect(material(env, map, at(map, 6, 6))).toBe('ash');
    expect(envSummary(env).ash).toBeGreaterThan(20);
    run(env, map, me, ENV.regrowMs);
    expect(material(env, map, at(map, 6, 6))).toBe('grass');
  });

  it('does not cross water or sand, and does not burn them', () => {
    const map = field(9, 5, { 0: '....~....', 1: '....~....', 2: '....s....', 3: '....~....', 4: '....~....' });
    const env = createEnv(map, map.objects);
    expect(ignite(env, map, at(map, 4, 0))).toBe(false);
    ignite(env, map, at(map, 1, 2));
    run(env, map, px(0, 0), 40_000);
    for (let y = 0; y < 5; y++) for (let x = 5; x < 9; x++) expect(material(env, map, at(map, x, y))).toBe('grass');
  });

  it('a wet tile does not catch fire until it dries', () => {
    const map = field(5, 1);
    const env = createEnv(map, map.objects);
    wet(env, map, at(map, 2, 0));
    expect(ignite(env, map, at(map, 2, 0))).toBe(false);
    run(env, map, px(0, 0), ENV.wetMs + 100);
    expect(ignite(env, map, at(map, 2, 0))).toBe(true);
  });

  it('wetting a burning tile puts it out', () => {
    const map = field(5, 1);
    const env = createEnv(map, map.objects);
    ignite(env, map, at(map, 2, 0));
    wet(env, map, at(map, 2, 0));
    expect(env.burning.size).toBe(0);
  });

  it('a burnt tree leaves a stump you can walk past; burnt brambles disappear', () => {
    const map = field(5, 1, { 0: '..T..' });
    const objs = [...map.objects, { type: 'bramble', tx: 3, ty: 0 }];
    map.solid[at(map, 3, 0)] = 1;
    const env = createEnv(map, objs);
    ignite(env, map, at(map, 2, 0));
    ignite(env, map, at(map, 3, 0));
    run(env, map, px(0, 0), 20_000);
    expect(material(env, map, at(map, 2, 0))).toBe('stump');
    expect(map.solid[at(map, 2, 0)]).toBe(0);
    expect(objs[1].gone).toBe(true);
    expect(map.solid[at(map, 3, 0)]).toBe(0);
  });

  it('never computes more than the per-tick cap, even in a huge fire', () => {
    const map = field(64, 64);
    const env = createEnv(map, map.objects);
    for (let i = 0; i < 64 * 64; i += 2) ignite(env, map, i);
    run(env, map, px(32, 32), 1000);
    expect(env.stats.maxTickCells).toBe(ENV.maxCellsPerTick);
    expect(env.stats.deferred).toBeGreaterThan(0);
  });
});

describe('far away: freeze and fast-forward (DESIGN.md 4.4)', () => {
  // 80 x 16 tiles = 5 regions in a row. The fire is in region 4; the player stands in region 0.
  function scenario(seed, budget, awayMs = 60_000) {
    const map = field(80, 16);
    const env = createEnv(map, map.objects, seed);
    const far = px(2, 8);
    run(env, map, far, 100);
    ignite(env, map, at(map, 70, 8));
    run(env, map, far, awayMs);
    const frozen = snapshot(env);
    // Come back: region 4 wakes and is fast-forwarded. Snapshot the moment it is done.
    const back = px(66, 8);
    stepEnv(env, map, back, 1000 / 60, budget);
    let guard = 0;
    while (envSummary(env).pendingRegions > 0 && guard++ < 10_000) stepEnv(env, map, back, 1000 / 60, budget);
    const region4 = snapshot({ ...env, cells: new Map([...env.cells].filter(([i]) => i % 80 >= 64)) });
    run(env, map, back, 5000, budget);
    return { env, map, frozen, region4, after: snapshot(env) };
  }

  it('nothing is computed while frozen', () => {
    const { env, map } = (() => {
      const map = field(80, 16);
      const env = createEnv(map, map.objects, 7);
      run(env, map, px(2, 8), 100);
      return { env, map };
    })();
    ignite(env, map, at(map, 70, 8));
    const before = snapshot(env);
    run(env, map, px(2, 8), 30_000);
    expect(snapshot(env)).toBe(before);
    expect(envSummary(env).awakeRegions).toBe(2);
  });

  it('coming back fast-forwards the fire by the time that passed', () => {
    const { env, map, frozen, after } = scenario(7, ENV.catchUpBudget);
    expect(after).not.toBe(frozen);
    expect(env.burning.size + envSummary(env).ash).toBeGreaterThan(10); // it spread while away
    expect(env.stats.catchUpSteps).toBeGreaterThanOrEqual(55);
    expect(envSummary(env).pendingRegions).toBe(0);
    void map;
  });

  it('the same seed and the same play give the same island', () => {
    expect(scenario(7, ENV.catchUpBudget).after).toBe(scenario(7, ENV.catchUpBudget).after);
  });

  it('the fast-forward result does not depend on how it is split across frames', () => {
    const a = scenario(7, ENV.catchUpBudget).region4;
    expect(scenario(7, 1).region4).toBe(a); // one coarse step per frame
    expect(scenario(7, 1e9).region4).toBe(a); // everything in one frame
  });

  it('a different seed gives a different fire', () => {
    expect(scenario(8, ENV.catchUpBudget).after).not.toBe(scenario(7, ENV.catchUpBudget).after);
  });

  it('a very long absence is fast-forwarded over a bounded window', () => {
    const { env, region4 } = scenario(7, 1e9, 3_600_000);
    expect(env.stats.catchUpSteps).toBeLessThanOrEqual(ENV.maxCatchUpMs / ENV.stepMs + 1);
    // The fire there is long out when the fast-forward ends (it may still have reached the next
    // region, which then burns on in front of the player).
    expect(region4).not.toContain('true');
  });
});
