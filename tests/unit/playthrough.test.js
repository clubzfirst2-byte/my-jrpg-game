import { describe, it, expect } from 'vitest';
import { createGameState } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { Ground, Shape, LEVEL_PX } from '../../src/game/world/tilemap.js';

// P10.6 completion check (DESIGN.md roadmap): a playthrough of the whole world. From the start,
// moving the way the player can — walking, swimming, jumping up one level, climbing earth cliffs
// (not ruins or house walls), dropping down from anywhere, and every doorway, stair and pass — every chest, checkpoint,
// item, villager, core of the murk, trial and landmark can be reached. Doors opened by puzzles
// count as open (the puzzles themselves are solved in trials.test.js / trials2.test.js), and so do
// trees and brambles (they burn / are cut: the island's hidden forest chest is behind trees).

const s = createGameState(WORLD);
const map = s.map;
const W = map.width;
const doors = new Set([...s.env.objectAt].filter(([, o]) => ['door', 'tree', 'bramble'].includes(o.type)).map(([i]) => i));
for (const o of map.objects) if (o.type === 'tree') doors.add(o.ty * W + o.tx);
const passable = (i) => {
  const g = map.ground[i];
  if (g === Ground.DARK || g === Ground.PIT) return false;
  return !map.solid[i] || doors.has(i);
};
const climbable = (i) => map.ground[i] !== Ground.RUIN && map.ground[i] !== Ground.WALL && map.shape[i] !== Shape.RAMP_N;
/** One move between neighbours: level, down, a jump up one level (any wall), or up a climbable cliff. */
const canMove = (a, b) => {
  const up = map.elev[b] - map.elev[a];
  if (up <= LEVEL_PX) return true;
  return climbable(b);
};

const warpsFrom = new Map();
for (const w of WORLD.warps) {
  const i = w.ty * W + w.tx;
  warpsFrom.set(i, [...(warpsFrom.get(i) ?? []), w.toTy * W + w.toTx]);
}

// v1.0 (C5): the beach ring is a doorway only with the flag source_open (warps with `if`). The
// playthrough counts it open; a second exploration shows that without it the source is out of reach.
const conditional = new Set(WORLD.warps.filter((w) => w.if).map((w) => w.ty * W + w.tx));

/** Every tile the player can stand on, starting from the spawn. */
function explore(useWarps = true, conditionalOpen = true) {
  const seen = new Uint8Array(W * map.height);
  const start = Math.floor(map.spawn.y / 16) * W + Math.floor(map.spawn.x / 16);
  const queue = [start];
  seen[start] = 1;
  while (queue.length) {
    const i = /** @type {number} */ (queue.pop());
    const x = i % W;
    const next = useWarps && (conditionalOpen || !conditional.has(i)) ? [...(warpsFrom.get(i) ?? [])] : [];
    if (x > 0) next.push(i - 1);
    if (x < W - 1) next.push(i + 1);
    if (i >= W) next.push(i - W);
    if (i < W * (map.height - 1)) next.push(i + W);
    for (const j of next) {
      if (seen[j] || !passable(j)) continue;
      if (!warpsFrom.get(i)?.includes(j) && !canMove(i, j)) continue;
      seen[j] = 1;
      queue.push(j);
    }
  }
  return seen;
}
const seen = explore();
/** A thing is reached when the player can stand within `r` tiles of it (1: on it or next to it). */
const reached = (tx, ty, r = 1) => {
  for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) if (Math.abs(dx) + Math.abs(dy) <= r && seen[(ty + dy) * W + tx + dx]) return true;
  return false;
};

describe('a playthrough of the whole world: everything can be reached from the start', () => {
  // [things, how close is close enough]
  const groups = {
    chests: [WORLD.chests, 1],
    checkpoints: [WORLD.checkpoints, 1],
    'map items': [WORLD.pickups, 1],
    villagers: [WORLD.npcs, 2], // (the shopkeeper is talked to across the counter)
    'cores of the murk': [WORLD.bosses, 1],
    landmarks: [WORLD.landmarks.filter((l) => !l.always), 4], // discovered when seen up close (the windmill stands on its ruin)
    'doorways and stairs': [WORLD.warps, 1],
  };
  for (const [name, [list, r]] of Object.entries(groups)) {
    it(`every one of the ${list.length} ${name}`, () => {
      const missing = list.filter((o) => !reached(o.tx, o.ty, r)).map((o) => o.id ?? `${o.tx},${o.ty}`);
      expect(missing).toEqual([]);
    });
  }

  it('(the check has teeth: without doorways, stairs and passes, the cave, the dungeon and the east are cut off)', () => {
    const walled = explore(false);
    const at = (o) => walled[o.ty * W + o.tx] || walled[(o.ty + 1) * W + o.tx];
    expect(at(WORLD.chests.find((c) => c.id === 'cave'))).toBe(0);
    expect(at(WORLD.chests.find((c) => c.id === 'mine'))).toBe(0);
    expect(at(WORLD.checkpoints.find((c) => c.id === 'forest'))).toBe(0);
    expect(walled[Math.floor(map.spawn.y / 16) * W + Math.floor(map.spawn.x / 16)]).toBe(1);
  });

  it('v1.0: the source\'s antechamber, its record stone and the arena are reached through the beach ring', () => {
    const gate = WORLD.warps.find((w) => w.id === 'source-gate');
    const into = WORLD.warps.find((w) => w.id === 'source-arena-in');
    expect(conditional.size).toBe(1);
    expect(conditional.has(gate.ty * W + gate.tx)).toBe(true);
    const stone = WORLD.checkpoints.find((c) => c.id === 'source');
    const boss = WORLD.finalBoss;
    for (const [tx, ty] of [[gate.toTx, gate.toTy], [stone.tx, stone.ty + 1], [into.toTx, into.toTy], [boss.tx, boss.ty + 2]]) expect(seen[ty * W + tx], `${tx},${ty}`).toBe(1);
    // Every seat can be reached (stood next to).
    for (const sw of WORLD.switches.filter((x) => x.seat)) expect(reached(sw.tx, sw.ty), sw.id).toBe(true);
  });

  it('v1.0: without source_open (the ring only a ring) the source cannot be reached at all', () => {
    const closed = explore(true, false);
    const gate = WORLD.warps.find((w) => w.id === 'source-gate');
    const boss = WORLD.finalBoss;
    const stone = WORLD.checkpoints.find((c) => c.id === 'source');
    expect(closed[gate.ty * W + gate.tx]).toBe(1); // (the ring itself stands on the open beach)
    for (const a of WORLD.areas.filter((x) => x.id === 'source_gate' || x.id === 'source_arena')) {
      for (let ty = a.ty; ty < a.ty + a.th; ty++) for (let tx = a.tx; tx < a.tx + a.tw; tx++) expect(closed[ty * W + tx], `${a.id} ${tx},${ty}`).toBe(0);
    }
    expect(closed[(stone.ty + 1) * W + stone.tx]).toBe(0);
    expect(closed[(boss.ty + 2) * W + boss.tx]).toBe(0);
    // Everything else stays reachable without it.
    const others = [...WORLD.chests, ...WORLD.checkpoints.filter((c) => c.id !== 'source'), ...WORLD.bosses];
    const reach = (o) => [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => closed[(o.ty + dy) * W + o.tx + dx]);
    expect(others.filter((o) => !reach(o)).map((o) => o.id)).toEqual([]);
  });

  it('all six regions, all four cores and all six trials are on the way', () => {
    for (const r of WORLD.regions) {
      let any = false;
      for (let ty = r.ty; ty < r.ty + r.th && !any; ty++) for (let tx = r.tx; tx < r.tx + Math.min(r.tw, 96) && !any; tx++) any = !!seen[ty * W + tx];
      expect(any, r.id).toBe(true);
    }
    expect(WORLD.bosses).toHaveLength(4);
    expect(WORLD.areas.filter((a) => a.id.startsWith('trial_'))).toHaveLength(6);
  });
});
