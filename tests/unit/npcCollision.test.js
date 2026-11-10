import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { STEP_SEC } from '../../src/game/core/fixedStep.js';
import { tileFeet } from '../../src/game/world/features.js';
import { groundHeightUnder } from '../../src/game/physics/collision.js';
import { isSolidTile, terrainHeightAt, Ground } from '../../src/game/world/tilemap.js';
import { createNpcs, stepNpcs, npcInReach, npcOverlap, keepClearTiles, onKeepClear, blockPlayerByNpcs, playerFrom, NPC, NPC_BODY } from '../../src/game/npc/npcs.js';

// v1.0 final (QA C-2): villagers have a small solid body; none can block a doorway or a narrow way.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const world = () => {
  const s = createGameState(WORLD);
  s.enemies = [];
  s.enemySpawns = [];
  return s;
};
/** The elder, held at home; the player two tiles below (clear of its 18 px front), facing up. */
function atElder() {
  const s = world();
  const elder = s.npcs.find((n) => n.id === 'elder');
  elder.homeX = elder.tx = elder.x;
  elder.homeY = elder.ty = elder.y;
  const p = s.player;
  const f = tileFeet(s.map, Math.floor(elder.x / 16), Math.floor(elder.y / 16) + 2);
  Object.assign(p, { x: f.x, y: f.y, z: elder.z, facing: 'up', aimX: 0, aimY: -1 });
  return { s, elder, p };
}

describe('villagers have a solid body', () => {
  it('walking straight at a villager stops at its body (no overlap), and talking still works from the front', () => {
    const { s, elder, p } = atElder();
    for (let i = 0; i < 60; i++) {
      stepGame(s, { ...none, moveY: -1 });
      expect(npcOverlap(p.x, p.y, p, elder)).toBe(0);
    }
    // right against it, below: final QA L-5 / QA4 L-7, 18 px (its front) so the hero no longer hides it
    expect(p.y - elder.y).toBeGreaterThanOrEqual(6 + NPC_BODY.front - 0.01);
    expect(p.y - elder.y).toBeLessThan(6 + NPC_BODY.front + 2);
    expect(NPC_BODY.front).toBe(12);
    expect(Math.abs(p.x - elder.x)).toBeLessThan(1);
    expect(npcInReach(s)?.id).toBe('elder');
    stepGame(s, { ...none, attack: true });
    expect(s.dialogue?.id).toBe('elder');
  });

  it('a diagonal push slides along the villager', () => {
    const { s, elder, p } = atElder();
    p.x = elder.x - 6;
    for (let i = 0; i < 40; i++) stepGame(s, { ...none, moveX: 0.7, moveY: -0.7 });
    expect(npcOverlap(p.x, p.y, p, elder)).toBe(0);
    expect(p.x).toBeGreaterThan(elder.x - 6); // it moved along
  });

  it('a player already overlapping one (it appeared on top of them) can walk out, and the villager never moves the player', () => {
    const { s, elder, p } = atElder();
    p.x = elder.x + 3;
    p.y = elder.y;
    const at = { x: p.x, y: p.y };
    stepGame(s, none);
    expect([p.x, p.y]).toEqual([at.x, at.y]); // not pushed
    for (let i = 0; i < 30; i++) stepGame(s, { ...none, moveX: 1 });
    expect(npcOverlap(p.x, p.y, p, elder)).toBe(0);
  });

  it('jumping height clears it; a villager at another height is no wall', () => {
    const { s, elder, p } = atElder();
    elder.z = p.z + NPC_BODY.zReach + 4;
    for (let i = 0; i < 40; i++) stepGame(s, { ...none, moveY: -1 });
    expect(p.y).toBeLessThan(elder.y - NPC_BODY.depth);
  });

  it('the 写し身 (ghost) has no body: the player walks through her', () => {
    const s = world();
    const def = WORLD.npcs.find((n) => n.id === 'princess_beach');
    const [ghost] = createNpcs(s.map, [def]);
    s.npcs = [ghost];
    s.npcDefs = [];
    const p = s.player;
    Object.assign(p, { x: ghost.x, y: ghost.y + 10, z: ghost.z });
    for (let i = 0; i < 40; i++) stepGame(s, { ...none, moveY: -1 });
    expect(p.y).toBeLessThan(ghost.y - NPC_BODY.depth);
  });

  it('a walking villager never steps into the player (it stops; strolling ones already stop 40 px away)', () => {
    const s = world();
    const n = s.npcs.find((x) => x.id === 'smith');
    const p = s.player;
    Object.assign(p, { x: n.x + 16, y: n.y, z: n.z });
    n.aside = { x: n.x + 32, y: n.y }; // (the one move that ignores the stop distance) — right through the player
    for (let i = 0; i < 120; i++) {
      stepNpcs(s, STEP_SEC);
      expect(npcOverlap(p.x, p.y, p, n)).toBe(0);
    }
    expect(n.aside).toBe(null); // it gave up on that spot
  });

  it('pushing into a villager for a moment makes it step aside, and the player gets by', () => {
    const { s, elder, p } = atElder();
    const startY = p.y;
    let t = 0;
    while (p.y > elder.homeY - 24 && t < 60 * 6) {
      stepGame(s, { ...none, moveY: -1 });
      t++;
    }
    expect(p.y).toBeLessThan(elder.homeY - 24); // past it
    expect(t / 60).toBeLessThan(3);
    expect(Math.abs(elder.x - elder.homeX)).toBeGreaterThan(NPC_BODY.halfWidth * 2 - 1); // it stepped aside
    expect(startY).toBeGreaterThan(p.y);
  });
});

// ---- no villager can block a doorway or a narrow passage ----

const ts = 16;
/** Can the player's box stand with its feet at (x, y) at height z? */
function playerFits(map, x, y, z) {
  for (const px of [x - 5, x + 5 - 1e-4]) {
    for (const py of [y - 6, y - 1e-4]) {
      const tx = Math.floor(px / ts);
      const ty = Math.floor(py / ts);
      if (isSolidTile(map, tx, ty)) return false;
      const g = map.ground[ty * map.width + tx];
      if (g === Ground.WATER || g === Ground.PIT) return false;
      if (terrainHeightAt(map, px, py) !== z) return false;
    }
  }
  return true;
}

/** Connected groups (≥ minSize cells, 2 px grid) of player spots in a window, with a villager body at npc (or none). */
function bigGroups(map, win, z, npc, minSize = 24) {
  const step = 2;
  const w = Math.floor((win.x1 - win.x0) / step) + 1;
  const h = Math.floor((win.y1 - win.y0) / step) + 1;
  const ok = new Uint8Array(w * h);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) {
      const x = win.x0 + i * step;
      const y = win.y0 + j * step;
      if (!playerFits(map, x, y, z)) continue;
      if (npc && npcOverlap(x, y, { halfWidth: 5, height: 6 }, npc) > 0) continue;
      ok[j * w + i] = 1;
    }
  }
  const seen = new Uint8Array(w * h);
  let groups = 0;
  for (let k = 0; k < w * h; k++) {
    if (!ok[k] || seen[k]) continue;
    let size = 0;
    const stack = [k];
    seen[k] = 1;
    while (stack.length) {
      const c = stack.pop();
      size++;
      const ci = c % w;
      const cj = (c - ci) / w;
      for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const ni = ci + di;
        const nj = cj + dj;
        if (ni < 0 || nj < 0 || ni >= w || nj >= h) continue;
        const nk = nj * w + ni;
        if (ok[nk] && !seen[nk]) {
          seen[nk] = 1;
          stack.push(nk);
        }
      }
    }
    if (size >= minSize) groups++;
  }
  return groups;
}

describe('no villager can block a doorway or a narrow passage (soft-lock check)', () => {
  const s = world();
  const map = s.map;
  const clear = keepClearTiles(map, s.warps);
  const solidDefs = WORLD.npcs.filter((d) => !d.ghost);

  it('doorways (and around them) and 1-tile corridors are keep-clear; e.g. every village door', () => {
    for (const id of ['shop-in', 'kitchen-in', 'elder_house-in', 'inn-in']) {
      const w = s.warps.find((x) => x.id === id);
      expect(w, id).toBeTruthy();
      for (const [dx, dy] of [[0, 0], [0, 1], [1, 0], [-1, 0]]) expect(clear[(w.ty + dy) * map.width + w.tx + dx]).toBe(1);
    }
  });

  it('no villager starts on a keep-clear tile', () => {
    for (const n of createNpcs(map, solidDefs)) {
      if (n.stay) continue;
      expect(onKeepClear(map, clear, n.x, n.y), n.id).toBe(false);
    }
  });

  it('strolling for 10 minutes, no villager ever touches a keep-clear tile or cuts a way in two', () => {
    const t = world();
    t.npcDefs = [];
    t.npcs = createNpcs(t.map, solidDefs);
    const p = t.player;
    Object.assign(p, { x: 8, y: 8 }); // far from everyone
    /** @type {Map<string, Set<string>>} */
    const spots = new Map(t.npcs.map((n) => [n.id, new Set([`${Math.round(n.x)},${Math.round(n.y)}`])]));
    for (let i = 0; i < 60 * 600; i++) {
      t.tick++;
      stepNpcs(t, STEP_SEC);
      for (const n of t.npcs) {
        expect(onKeepClear(map, clear, n.x, n.y) && !n.stay, `${n.id} on a keep-clear tile at ${n.x},${n.y}`).toBe(false);
        // (a 4 px grid of spots is enough for the passage check: the body is 10 × 6)
        spots.get(n.id).add(`${Math.round(n.x / 4) * 4},${Math.round(n.y / 4) * 4}`);
      }
    }
    for (const n of t.npcs) {
      const list = [...spots.get(n.id)].map((k) => k.split(',').map(Number));
      expect(list.every(([x, y]) => Math.hypot(x - n.homeX, y - n.homeY) <= NPC.wander + 4), n.id).toBe(true);
      // Every spot it stood on: with its body there, the free space around stays in one piece.
      for (const [x, y] of list) {
        const win = { x0: x - 56, x1: x + 56, y0: y - 56, y1: y + 56 };
        const base = bigGroups(map, win, n.z, null);
        expect(bigGroups(map, win, n.z, { x, y }), `${n.id} at ${x},${y} splits the way`).toBeLessThanOrEqual(base);
      }
    }
  }, 120_000);
});

describe('review fixes (v1-final-a)', () => {
  it('one who keeps their place (stay: the princess before the inn) is never pushed out of it: the player squeezes by instead', () => {
    const s = world();
    const def = WORLD.npcs.find((n) => n.id === 'princess_home');
    const [princess] = createNpcs(s.map, [def]);
    expect(princess.stay).toBe(true);
    s.npcs = [princess];
    s.npcDefs = [];
    const home = { x: princess.x, y: princess.y };
    const p = s.player;
    Object.assign(p, { x: princess.x, y: princess.y + 14, z: princess.z, groundZ: princess.z });
    let t = 0;
    while (p.y > home.y - 20 && t < 60 * 5) {
      stepGame(s, { ...none, moveY: -1 });
      t++;
      expect([princess.x, princess.y]).toEqual([home.x, home.y]);
    }
    expect(p.y).toBeLessThan(home.y - 20); // through
    expect(t / 60).toBeLessThan(2.5);
    for (let i = 0; i < 120; i++) stepGame(s, none);
    expect([princess.x, princess.y]).toEqual([home.x, home.y]);
    expect(princess.aside).toBe(null);
  });

  it('a villager by a cliff corner: the slide never pokes the player into the cliff or onto it', () => {
    const s = world();
    const map = s.map;
    const [C, R] = [22, 91]; // open, flat village grass
    for (let ty = R - 2; ty <= R + 1; ty++) for (let tx = C - 2; tx <= C; tx++) expect(map.elev[ty * map.width + tx]).toBe(0);
    map.elev[R * map.width + C] = 32; // a cliff tile; the tile above it (the corner) stays open
    const fx = C * 16 - 6; // the player's right side 1 px short of the cliff
    const fy = R * 16 + 2; // the box spans rows R-1 and R
    const [villager] = createNpcs(map, [{ id: 'v', name: 'v', dialogue: 'elder', tx: C - 1, ty: R - 1 }]);
    Object.assign(villager, { x: fx + 3, y: fy - 6 - NPC_BODY.front, z: 0 }); // its body (with its front) ends where the box starts
    s.npcs = [villager];
    s.npcDefs = [];
    const p = s.player;
    Object.assign(p, { x: fx, y: fy, z: 0, groundZ: 0, grounded: true, vz: 0 });
    const from = playerFrom(p);
    // The move went up-right past the corner (row R-1 is open) and into the villager's body.
    Object.assign(p, { x: fx + 3, y: fy - 3 });
    expect(npcOverlap(p.x, p.y, p, villager)).toBeGreaterThan(0);
    expect(npcOverlap(p.x, fy, p, villager)).toBe(0); // the slide "keep x" would be free of the villager…
    blockPlayerByNpcs(s, from, true, STEP_SEC, 8);
    // …but it is in the cliff: the whole move is undone instead.
    expect([p.x, p.y, p.z]).toEqual([fx, fy, 0]);
    expect(groundHeightUnder(p, map)).toBe(0);
  });

  it('a move undone by a villager puts the height back with the position', () => {
    const s = world();
    const n = s.npcs.find((x) => x.id === 'elder');
    const p = s.player;
    Object.assign(p, { x: n.x, y: n.y + 13, z: n.z, groundZ: n.z, grounded: true, vz: 0 });
    const from = playerFrom(p);
    // As if the move had climbed a step on its way into the villager's body:
    Object.assign(p, { y: n.y + 2, z: n.z + 8, groundZ: n.z + 8 });
    blockPlayerByNpcs(s, from, true, STEP_SEC, 8);
    expect([p.x, p.y, p.z, p.groundZ, p.grounded]).toEqual([from.x, from.y, from.z, from.groundZ, true]);
  });
});
