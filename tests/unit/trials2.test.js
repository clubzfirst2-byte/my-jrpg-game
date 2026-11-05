import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { tileFeet, areaAt } from '../../src/game/world/features.js';
import { COMBAT } from '../../src/game/entities/playerCombat.js';
import { Ground } from '../../src/game/world/tilemap.js';

// P10.5 completion check (DESIGN.md roadmap): every new trial and every floor of the dungeon can
// be solved in at least two ways. Coordinates are the room's own: x 99-109 inside, rows from y0.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false, ability: false };
const area = (id) => WORLD.areas.find((a) => a.id === id);
/** The room's origin: world column of x=96 in its region's strip, and its top row. */
const origin = (id) => ({ ox: area(id).tx - 98 + 96 - 96, y0: area(id).ty });

let shared = null;
function room(id, abilities = []) {
  const s = createGameState(WORLD);
  s.enemies = [];
  s.enemySpawns = [];
  s.progress.abilities = [...abilities];
  s.progress.ability = abilities[0] ?? null;
  const { ox, y0 } = origin(id);
  const at = (x, y) => ({ tx: ox + x, ty: y0 + y });
  shared = { s, at };
  place(s, at(104, 11), 'up');
  stepGame(s, none);
  expect(areaAt(s, s.player.x, s.player.y)?.id).toBe(id);
  return { s, at };
}
function place(s, { tx, ty }, facing) {
  const f = tileFeet(s.map, tx, ty);
  const p = s.player;
  Object.assign(p, { x: f.x, y: f.y, prevX: f.x, prevY: f.y, vx: 0, vy: 0, swimming: false });
  p.z = p.prevZ = p.groundZ = s.map.elev[ty * s.map.width + tx];
  p.grounded = true;
  p.facing = facing;
  const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[facing];
  p.aimX = v[0];
  p.aimY = v[1];
}
const run = (s, input, n) => {
  for (let i = 0; i < n; i++) stepGame(s, input);
};
const ability = (s, id) => {
  s.progress.ability = id;
  stepGame(s, { ...none, ability: true });
  run(s, none, 100);
};
const shoot = (s) => {
  run(s, { ...none, bow: true }, Math.ceil((COMBAT.bowDrawMs / 1000) * 60) + 2);
  run(s, none, 60);
};
const swing = (s) => {
  stepGame(s, { ...none, attack: true });
  run(s, none, 40);
};
const fireBlade = (s) => {
  s.progress.inv.weapons.push({ id: 'ember_sword', dur: 22, lvl: 0 });
  s.progress.inv.equip.weapon = s.progress.inv.weapons.length - 1;
};
const opened = (s, id) => s.progress.gates.includes(id);
void shared;

describe('双火の試練 (forest): both sconces must burn', () => {
  const t = 'trial_twin';
  it('way 1: fire arrows through the two braziers', () => {
    const { s, at } = room(t);
    place(s, at(99, 7), 'right');
    shoot(s);
    expect(opened(s, t)).toBe(false); // one is not enough
    place(s, at(109, 9), 'left');
    shoot(s);
    expect(opened(s, t)).toBe(true);
  });

  it('way 2: the fire blade, swung next to each sconce', () => {
    const { s, at } = room(t);
    fireBlade(s);
    place(s, at(103, 7), 'left');
    swing(s);
    expect(opened(s, t)).toBe(false);
    place(s, at(105, 9), 'right');
    swing(s);
    expect(opened(s, t)).toBe(true);
  });
});

describe('暗がりの試練 (desert, dark): light on the sensor and weight on the plate together', () => {
  const t = 'trial_dark';
  it('way 1: 念動 slides the crate onto the plate, then a light orb by the sensor', () => {
    const { s, at } = room(t, ['telekinesis', 'light']);
    expect(area(t).dark).toBe(true);
    place(s, at(105, 9), 'left');
    ability(s, 'telekinesis');
    expect(opened(s, t)).toBe(false);
    place(s, at(105, 7), 'up');
    ability(s, 'light');
    expect(opened(s, t)).toBe(true);
  });

  it('way 2: a fire arrow lights the sconce by the sensor; sword hits push the crate', () => {
    const { s, at } = room(t);
    place(s, at(99, 7), 'right');
    shoot(s);
    expect(opened(s, t)).toBe(false);
    for (let x = 105; x > 100; x--) {
      place(s, at(x, 9), 'left');
      swing(s);
    }
    run(s, none, 10);
    expect(opened(s, t)).toBe(true);
  });
});

describe('水鏡の試練 (lake): any switch across the water opens the prize', () => {
  const t = 'trial_water';
  it('way 1: a fire arrow over the water onto the sconce', () => {
    const { s, at } = room(t);
    place(s, at(106, 11), 'up');
    shoot(s);
    expect(opened(s, t)).toBe(true);
  });

  it('way 2: swim across and stand on the plate', () => {
    const { s, at } = room(t);
    expect(s.map.ground[at(103, 6).ty * s.map.width + at(103, 6).tx]).toBe(Ground.WATER);
    place(s, at(103, 8), 'up');
    for (let i = 0; i < 60 * 5 && !opened(s, t); i++) stepGame(s, { ...none, moveY: -1 });
    expect(opened(s, t)).toBe(true);
  });

  it('way 3: 共鳴 reaches the stone', () => {
    const { s, at } = room(t, ['resonance']);
    place(s, at(108, 3), 'right');
    ability(s, 'resonance');
    expect(opened(s, t)).toBe(true);
  });
});

describe('白嶺の坑道 (the dungeon): three floors', () => {
  it('B1 (dark), way 1: a light orb by the sensor', () => {
    const { s, at } = room('mine_1', ['light']);
    place(s, at(105, 7), 'up');
    ability(s, 'light');
    expect(opened(s, 'mine_1')).toBe(true);
  });

  it('B1, way 2: a fire arrow through the brazier onto the sconce', () => {
    const { s, at } = room('mine_1');
    place(s, at(99, 7), 'right');
    shoot(s);
    expect(opened(s, 'mine_1')).toBe(true);
  });

  it('B2, way 1: strike the crystal; the sparks run along the metal floor to the stone', () => {
    const { s, at } = room('mine_2');
    place(s, at(100, 9), 'up');
    swing(s);
    run(s, none, 30);
    expect(opened(s, 'mine_2')).toBe(true);
  });

  it('B2, way 2: 共鳴 by the stone', () => {
    const { s, at } = room('mine_2', ['resonance']);
    place(s, at(108, 7), 'right');
    ability(s, 'resonance');
    expect(opened(s, 'mine_2')).toBe(true);
  });

  it('B3, way 1: 念動 slides the crate onto one plate, the player stands on the other', () => {
    const { s, at } = room('mine_3', ['telekinesis']);
    place(s, at(105, 9), 'left');
    ability(s, 'telekinesis');
    expect(opened(s, 'mine_3')).toBe(false);
    place(s, at(109, 7), 'down');
    stepGame(s, none);
    expect(opened(s, 'mine_3')).toBe(true);
  });

  it('B3, way 2: sword hits push the crate', () => {
    const { s, at } = room('mine_3');
    for (let x = 105; x > 100; x--) {
      place(s, at(x, 9), 'left');
      swing(s);
    }
    place(s, at(109, 7), 'down');
    stepGame(s, none);
    expect(opened(s, 'mine_3')).toBe(true);
  });

  it('the stairs lead down floor by floor, and back up; the way in is a cave in the cliff', () => {
    const s = createGameState(WORLD);
    s.enemies = [];
    s.enemySpawns = [];
    const inn = WORLD.warps.find((w) => w.id === 'mine-in');
    expect(inn.reveal).toBe(true);
    for (const [from, to] of [['mine1-down', 'mine_2'], ['mine2-down', 'mine_3'], ['mine3-up', 'mine_2'], ['mine2-up', 'mine_1'], ['mine-out', null], ['mine-in', 'mine_1']]) {
      const w = WORLD.warps.find((x) => x.id === from);
      place(s, { tx: w.tx, ty: w.ty + (w.facing === 'up' ? 1 : -1) }, w.facing);
      for (let i = 0; i < 90 && (areaAt(s, s.player.x, s.player.y)?.id ?? null) !== to; i++) stepGame(s, { ...none, moveY: w.facing === 'up' ? -1 : 1 });
      expect(areaAt(s, s.player.x, s.player.y)?.id ?? null, from).toBe(to);
    }
  });
});
