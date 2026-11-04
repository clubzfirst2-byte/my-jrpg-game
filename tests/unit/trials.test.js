import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { ISLAND } from '../../src/game/world/maps/island.js';
import { tileFeet } from '../../src/game/world/features.js';
import { createEnemy } from '../../src/game/entities/enemies.js';
import { COMBAT } from '../../src/game/entities/playerCombat.js';
import { Ground } from '../../src/game/world/tilemap.js';
import { ABILITY } from '../../src/game/puzzles/abilities.js';

// P7 completion check (DESIGN.md roadmap): every trial can be solved in at least two ways.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false, ability: false };
const area = (id) => ISLAND.areas.find((a) => a.id === id);
const y0 = (id) => area(id).ty;

function trial(id, abilities = []) {
  const s = createGameState(ISLAND);
  s.enemies = [];
  s.enemySpawns = [];
  s.progress.abilities = [...abilities];
  s.progress.ability = abilities[0] ?? null;
  // Arrive like the player does (the entrance teaches the room's ability).
  place(s, 104, y0(id) + 11, 'up');
  stepGame(s, none);
  return s;
}
function place(s, tx, ty, facing) {
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
const run = (s, input, n) => {
  for (let i = 0; i < n; i++) stepGame(s, input);
};
const ability = (s, id) => {
  s.progress.ability = id;
  stepGame(s, { ...none, ability: true });
  run(s, none, 100); // past every ability's cooldown
};
const shoot = (s) => {
  run(s, { ...none, bow: true }, Math.ceil((COMBAT.bowDrawMs / 1000) * 60) + 2);
  run(s, none, 60);
};
const swing = (s) => {
  stepGame(s, { ...none, attack: true });
  run(s, none, 40);
};
const opened = (s, id) => s.progress.gates.includes(id);

describe('entering a trial teaches its ability', () => {
  it('灯火 / 念動 / 蔓結び from the three trials, 共鳴 from the tower altar', () => {
    expect(trial('trial_light').progress.abilities).toEqual(['light']);
    expect(trial('trial_weight').progress.abilities).toEqual(['telekinesis']);
    expect(trial('trial_chasm').progress.abilities).toEqual(['vine']);
    const s = createGameState(ISLAND);
    const altar = ISLAND.envObjects.find((o) => o.type === 'altar');
    place(s, altar.tx, altar.ty + 1, 'up');
    stepGame(s, none);
    expect(s.progress.abilities).toContain('resonance');
  });
});

describe('灯りの試練 (light): the sensor needs light', () => {
  it('way 1: a light orb (灯火) by the sensor', () => {
    const s = trial('trial_light');
    expect(opened(s, 'trial_light')).toBe(false);
    place(s, 105, y0('trial_light') + 7, 'up');
    ability(s, 'light');
    expect(opened(s, 'trial_light')).toBe(true);
  });

  it('way 2: a fire arrow through the brazier lights the sconce next to the sensor', () => {
    const s = trial('trial_light');
    place(s, 99, y0('trial_light') + 7, 'right');
    shoot(s);
    expect(s.events.some((e) => e.type === 'fireArrow')).toBe(true);
    expect(opened(s, 'trial_light')).toBe(true);
  });

  it('way 3: the fire blade lights the sconce', () => {
    const s = trial('trial_light');
    s.progress.inv.weapons.push({ id: 'ember_sword', dur: 22, lvl: 0 });
    s.progress.inv.equip.weapon = s.progress.inv.weapons.length - 1;
    place(s, 106, y0('trial_light') + 7, 'right');
    swing(s);
    expect(opened(s, 'trial_light')).toBe(true);
  });

  it('nothing happens without light', () => {
    const s = trial('trial_light');
    run(s, none, 120);
    expect(opened(s, 'trial_light')).toBe(false);
  });
});

describe('重さの試練 (weight): two plates at once', () => {
  const t = 'trial_weight';
  it('way 1: telekinesis slides the crate onto one plate, the player stands on the other', () => {
    const s = trial(t, []);
    place(s, 105, y0(t) + 9, 'left');
    ability(s, 'telekinesis');
    const crate = [...s.env.objectAt.values()].find((o) => o.type === 'crate');
    expect([crate.tx, crate.ty]).toEqual([99, y0(t) + 9]);
    expect(opened(s, t)).toBe(false); // one plate is not enough
    place(s, 109, y0(t) + 7, 'down');
    stepGame(s, none);
    expect(opened(s, t)).toBe(true);
  });

  it('way 2: pushing the crate with sword hits, one tile per hit', () => {
    const s = trial(t, []);
    s.progress.abilities = [];
    for (let x = 105; x > 100; x--) {
      place(s, x, y0(t) + 9, 'left');
      swing(s);
    }
    const crate = [...s.env.objectAt.values()].find((o) => o.type === 'crate');
    expect(crate.tx).toBe(99);
    place(s, 109, y0(t) + 7, 'down');
    stepGame(s, none);
    expect(opened(s, t)).toBe(true);
  });

  it('way 3: an enemy standing on a plate counts as weight', () => {
    const s = trial(t, []);
    const f = tileFeet(s.map, 99, y0(t) + 9);
    const e = createEnemy('beast', f.x, f.y, 0, 90);
    e.state = 'stun';
    e.stunMs = 99999;
    s.enemies = [e];
    place(s, 109, y0(t) + 7, 'down');
    stepGame(s, none);
    expect(opened(s, t)).toBe(true);
  });
});

describe('奈落の試練 (chasm): any switch across the pit opens the prize', () => {
  const t = 'trial_chasm';
  it('way 1: a fire arrow through the brazier across the pit onto the sconce', () => {
    const s = trial(t);
    place(s, 106, y0(t) + 11, 'up');
    shoot(s);
    expect(opened(s, t)).toBe(true);
  });

  it('way 2: a vine bridge (蔓結び) across the pit to the plate', () => {
    const s = trial(t, ['vine']);
    place(s, 103, y0(t) + 8, 'up');
    ability(s, 'vine');
    expect(s.map.ground[(y0(t) + 7) * s.map.width + 103]).toBe(Ground.VINE);
    place(s, 103, y0(t) + 7, 'up');
    ability(s, 'vine');
    place(s, 103, y0(t) + 6, 'up');
    run(s, { ...none, moveY: -1 }, 70); // walk across onto the plate
    expect(s.events.some((e) => e.type === 'fell')).toBe(false);
    expect(opened(s, t)).toBe(true);
  });

  it('way 3: a resonance pulse (共鳴) reaches the stone', () => {
    const s = trial(t, ['resonance']);
    place(s, 109, y0(t) + 8, 'up');
    ability(s, 'resonance');
    expect(opened(s, t)).toBe(true);
  });

  it('walking into the pit drops you back at the edge (half a heart)', () => {
    const s = trial(t);
    place(s, 104, y0(t) + 8, 'up');
    const hp = s.player.hp;
    for (let i = 0; i < 60 && !s.events.some((e) => e.type === 'fell'); i++) stepGame(s, { ...none, moveY: -1 });
    expect(s.events.some((e) => e.type === 'fell')).toBe(true);
    expect(s.player.hp).toBe(hp - ABILITY.pitDamage);
    expect(Math.floor(s.player.y / 16)).toBeGreaterThanOrEqual(y0(t) + 8);
  });

  it('a vine burns away (fire) and the pit is back', async () => {
    const { ignite } = await import('../../src/game/env/envSim.js');
    const s = trial(t, ['vine']);
    place(s, 103, y0(t) + 8, 'up');
    ability(s, 'vine');
    const i = (y0(t) + 7) * s.map.width + 103;
    expect(ignite(s.env, s.map, i)).toBe(true);
    run(s, none, 200);
    expect(s.map.ground[i]).toBe(Ground.PIT);
  });
});

describe('the doors stay open (saved)', () => {
  it('an opened trial is restored from the progress', async () => {
    const { applyProgress, emptyProgress } = await import('../../src/game/world/features.js');
    const s = createGameState(ISLAND);
    applyProgress(s, { ...emptyProgress(), gates: ['trial_light'] });
    expect(s.map.solid[(y0('trial_light') + 4) * s.map.width + 104]).toBe(0);
  });
});
