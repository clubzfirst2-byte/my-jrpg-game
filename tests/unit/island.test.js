import { describe, it, expect } from 'vitest';
import { createGameState, stepGame, respawnPlayer } from '../../src/game/state.js';
import { ISLAND } from '../../src/game/world/maps/island.js';
import { Ground, isSolidTile } from '../../src/game/world/tilemap.js';
import { overlapsSolid } from '../../src/game/physics/collision.js';
import { tileFeet, areaAt, applyProgress, emptyProgress, HIGH_GROUND_PX } from '../../src/game/world/features.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };

function island() {
  const s = createGameState(ISLAND);
  s.enemies = []; // these tests are about the island, not combat
  s.enemySpawns = [];
  return s;
}

/** Puts the player on tile (tx, ty) standing on the terrain, facing a direction. */
function place(s, tx, ty, facing = 'down') {
  const f = tileFeet(s.map, tx, ty);
  const p = s.player;
  p.x = p.prevX = f.x;
  p.y = p.prevY = f.y;
  p.z = p.prevZ = p.groundZ = s.map.elev[ty * s.map.width + tx];
  p.grounded = true;
  p.facing = facing;
  const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[facing];
  p.aimX = v[0];
  p.aimY = v[1];
}

describe('island map', () => {
  it('parses, and the spawn point is free and on dry ground', () => {
    const s = island();
    const p = s.player;
    expect(overlapsSolid(p, s.map)).toBe(false);
    const t = Math.floor(p.y / 16) * s.map.width + Math.floor(p.x / 16);
    expect(s.map.ground[t]).not.toBe(Ground.WATER);
  });

  it('has the features of DESIGN.md 5.9: landmarks, chests, checkpoints, a cave with two doorways', () => {
    expect(ISLAND.landmarks.find((l) => l.id === 'tower')?.always).toBe(true);
    expect(ISLAND.chests.length).toBeGreaterThanOrEqual(5);
    expect(ISLAND.chests.filter((c) => c.reward === 'heart')).toHaveLength(2);
    expect(ISLAND.checkpoints.length).toBeGreaterThanOrEqual(3);
    expect(ISLAND.areas.find((a) => a.id === 'cave')).toBeTruthy();
    expect(ISLAND.warps.length).toBeGreaterThanOrEqual(2);
  });

  it('chests and campfires are solid; checkpoints and warp tiles are walkable', () => {
    const s = island();
    for (const c of [...ISLAND.chests, ...ISLAND.campfires]) expect(isSolidTile(s.map, c.tx, c.ty)).toBe(true);
    for (const c of ISLAND.checkpoints) expect(isSolidTile(s.map, c.tx, c.ty)).toBe(false);
    for (const w of ISLAND.warps) {
      expect(isSolidTile(s.map, w.tx, w.ty)).toBe(false);
      expect(isSolidTile(s.map, w.toTx, w.toTy)).toBe(false);
    }
  });

  it('every enemy starts on a free tile', () => {
    const s = createGameState(ISLAND);
    for (const e of s.enemies) expect(overlapsSolid(e, s.map)).toBe(false);
  });

  it('the north ledge chest sits higher than the plateau below it and lower than the tower top', () => {
    const s = island();
    const at = (tx, ty) => s.map.elev[ty * s.map.width + tx];
    const ledge = ISLAND.chests.find((c) => c.id === 'ledge');
    const tower = ISLAND.chests.find((c) => c.id === 'tower');
    expect(at(ledge.tx, ledge.ty + 1)).toBe(48);
    expect(at(ledge.tx, ledge.ty + 5)).toBe(32); // plateau: a 1-level climb up to the ledge
    expect(at(tower.tx, tower.ty + 1)).toBeGreaterThan(48); // high enough to glide down to the ledge
  });
});

describe('chests', () => {
  it('the attack button opens a chest in front instead of swinging, once', () => {
    const s = island();
    const c = ISLAND.chests.find((x) => x.id === 'camp');
    place(s, c.tx, c.ty + 1, 'up');
    stepGame(s, { ...none, attack: true });
    expect(s.progress.openedChests).toContain('camp');
    expect(s.progress.inv.items[c.item]).toBe(1); // P6: chests hold equipment or money
    expect(s.player.action).toBe('none'); // no swing
    run(s, none, 2);
    stepGame(s, { ...none, attack: true });
    expect(s.progress.inv.items[c.item]).toBe(1); // already open: now it is just a swing
    expect(s.player.action).toBe('attack');
  });

  it('a chest behind the player is not opened', () => {
    const s = island();
    const c = ISLAND.chests.find((x) => x.id === 'camp');
    place(s, c.tx, c.ty + 1, 'down');
    stepGame(s, { ...none, attack: true });
    expect(s.progress.openedChests).not.toContain('camp');
  });

  it('a heart container raises and refills health and asks for a save', () => {
    const s = island();
    s.player.hp = 3;
    const c = ISLAND.chests.find((x) => x.reward === 'heart');
    place(s, c.tx, c.ty + 1, 'up');
    stepGame(s, { ...none, attack: true });
    expect(s.progress.maxHp).toBe(16);
    expect(s.player.maxHp).toBe(16);
    expect(s.player.hp).toBe(16);
    expect(s.saveRequested).toBe(true);
  });
});

function run(s, input, n) {
  for (let i = 0; i < n; i++) stepGame(s, input);
}

describe('checkpoints and respawn', () => {
  it('touching a stone activates it; after a death the player respawns there', () => {
    const s = island();
    const cp = ISLAND.checkpoints.find((c) => c.id === 'camp');
    place(s, cp.tx, cp.ty);
    stepGame(s, none);
    expect(s.progress.checkpoint).toBe('camp');
    expect(s.saveRequested).toBe(true);
    respawnPlayer(s);
    const f = tileFeet(s.map, cp.tx, cp.ty + 1);
    expect(s.player.x).toBe(f.x);
    expect(s.player.y).toBe(f.y);
    expect(s.player.hp).toBe(s.player.maxHp);
  });

  it('without a checkpoint the player respawns at the start', () => {
    const s = island();
    respawnPlayer(s);
    expect(s.player.x).toBe(s.map.spawn.x);
  });
});

describe('the secret cave', () => {
  it('walking north into the cliff opening enters the cave, with the cave area active', () => {
    const s = island();
    const door = ISLAND.warps.find((w) => w.id === 'cave-in');
    place(s, door.tx, door.ty + 1, 'up');
    run(s, { ...none, moveY: -1 }, 30);
    const p = s.player;
    expect(areaAt(s, p.x, p.y)?.id).toBe('cave');
    expect(s.events.some((e) => e.type === 'warp')).toBe(true);
  });

  it('the north doorway of the cave leads out onto the high ledge', () => {
    const s = island();
    const out = ISLAND.warps.find((w) => w.id === 'cave-out');
    place(s, out.tx, out.ty + 1, 'up');
    run(s, { ...none, moveY: -1 }, 30);
    const p = s.player;
    expect(areaAt(s, p.x, p.y)).toBe(null);
    expect(p.z).toBe(48); // on the north ledge
  });

  it('walking back south out of the cave returns to the opening', () => {
    const s = island();
    const back = ISLAND.warps.find((w) => w.id === 'cave-back');
    place(s, back.tx, back.ty - 1, 'down');
    run(s, { ...none, moveY: 1 }, 30);
    expect(areaAt(s, s.player.x, s.player.y)).toBe(null);
    expect(s.player.z).toBe(0);
  });
});

describe('landmarks and progress', () => {
  it('the tower is known from the start; the smoke is discovered from high ground', () => {
    const s = island();
    stepGame(s, none);
    expect(s.progress.landmarks).toContain('tower');
    expect(s.progress.landmarks).not.toContain('smoke');
    place(s, 48, 35); // on the level-2 plateau around the tower
    expect(s.player.z).toBeGreaterThanOrEqual(HIGH_GROUND_PX);
    stepGame(s, none);
    expect(s.progress.landmarks).toContain('smoke');
  });

  it('saved progress is applied to a new game', () => {
    const s = island();
    applyProgress(s, { ...emptyProgress(), openedChests: ['cave'], maxHp: 20, checkpoint: 'hill', checkpoints: ['hill'] });
    expect(s.player.maxHp).toBe(20);
    expect(s.progress.openedChests).toEqual(['cave']);
    respawnPlayer(s);
    const hill = ISLAND.checkpoints.find((c) => c.id === 'hill');
    expect(s.player.x).toBe(tileFeet(s.map, hill.tx, hill.ty + 1).x);
  });
});
