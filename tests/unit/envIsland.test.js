import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { ISLAND } from '../../src/game/world/maps/island.js';
import { tileFeet, applyProgress, emptyProgress } from '../../src/game/world/features.js';
import { material, ignite } from '../../src/game/env/envSim.js';
import { createEnemy } from '../../src/game/entities/enemies.js';
import { COMBAT } from '../../src/game/entities/playerCombat.js';
import { discharge } from '../../src/game/env/envActions.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const obj = (s, type, filter = () => true) => ISLAND.envObjects.find((o) => o.type === type && filter(o));
const idx = (s, tx, ty) => ty * s.map.width + tx;

function island() {
  const s = createGameState(ISLAND);
  s.enemies = [];
  s.enemySpawns = [];
  return s;
}
function place(s, tx, ty, facing) {
  const f = tileFeet(s.map, tx, ty);
  const p = s.player;
  p.x = p.prevX = f.x;
  p.y = p.prevY = f.y;
  p.z = p.prevZ = p.groundZ = s.map.elev[idx(s, tx, ty)];
  p.grounded = true;
  p.facing = facing;
  const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[facing];
  p.aimX = v[0];
  p.aimY = v[1];
}
function run(s, input, n) {
  for (let i = 0; i < n; i++) stepGame(s, input);
}
/** Draws the bow fully and releases. */
function shoot(s) {
  run(s, { ...none, bow: true }, Math.ceil((COMBAT.bowDrawMs / 1000) * 60) + 2);
  stepGame(s, none);
}
/** One sword swing (then waits for it to finish). */
function swing(s) {
  stepGame(s, { ...none, attack: true });
  run(s, none, 40);
}

describe('fire on the island', () => {
  it('an arrow shot through the brazier becomes a fire arrow and burns the brambles away', () => {
    const s = island();
    const b = obj(s, 'bramble');
    const brazier = obj(s, 'brazier');
    place(s, brazier.tx, brazier.ty + 2, 'up');
    shoot(s);
    run(s, none, 60);
    expect(s.events.some((e) => e.type === 'fireArrow')).toBe(true);
    run(s, none, 60 * 6);
    expect(material(s.env, s.map, idx(s, b.tx, b.ty))).not.toBe('bramble');
    expect(s.map.solid[idx(s, b.tx, b.ty)]).toBe(0); // the way into the pocket is open
  });

  it('the sword cuts the brambles too (three swings)', () => {
    const s = island();
    const b = obj(s, 'bramble');
    place(s, b.tx, b.ty + 1, 'up');
    swing(s);
    swing(s);
    expect(s.map.solid[idx(s, b.tx, b.ty)]).toBe(1);
    swing(s);
    expect(s.map.solid[idx(s, b.tx, b.ty)]).toBe(0);
  });

  it('standing in fire hurts; a water jar puts the fire out', () => {
    const s = island();
    const jar = obj(s, 'jar');
    // Grass west of the camp, next to the jar.
    const tx = jar.tx;
    const ty = jar.ty + 1;
    expect(material(s.env, s.map, idx(s, tx, ty))).toMatch(/grass|metal/);
    const t = idx(s, jar.tx - 1, jar.ty);
    ignite(s.env, s.map, t);
    place(s, jar.tx - 1, jar.ty, 'right');
    const hp = s.player.hp;
    run(s, none, 2);
    expect(s.player.hp).toBeLessThan(hp);
    swing(s); // break the jar
    expect(s.events.some((e) => e.type === 'douse')).toBe(true);
    expect(s.env.burning.has(t)).toBe(false);
    expect(ignite(s.env, s.map, t)).toBe(false); // still wet
  });
});

describe('electricity', () => {
  it('the camp crystal shocks enemies on the metal floor, not the player on the grass', () => {
    const s = island();
    const c = obj(s, 'crystal', (o) => !o.link && o.tx < 80);
    const onMetal = createEnemy('beast', (c.tx + 3) * 16 + 8, c.ty * 16 + 14, 0, 99);
    const onGrass = createEnemy('beast', (c.tx - 3) * 16 + 8, (c.ty - 3) * 16 + 14, 0, 98);
    s.enemies = [onMetal, onGrass];
    place(s, c.tx - 1, c.ty, 'right');
    const hp = s.player.hp;
    stepGame(s, { ...none, attack: true });
    run(s, none, 15);
    expect(s.events.some((e) => e.type === 'discharge')).toBe(true);
    expect(onMetal.hp).toBeLessThan(12);
    expect(onGrass.hp).toBe(12);
    expect(s.player.hp).toBe(hp);
  });

  it('the islet crystal powers the receiver through the sea and opens the vault (saved)', () => {
    const s = island();
    const c = obj(s, 'crystal', (o) => o.tx > 80);
    const doors = ISLAND.envObjects.filter((o) => o.type === 'door' && o.link === 'vault');
    for (const d of doors) expect(s.map.solid[idx(s, d.tx, d.ty)]).toBe(1);
    place(s, c.tx + 1, c.ty, 'left');
    stepGame(s, { ...none, attack: true });
    run(s, none, 15);
    for (const d of doors) expect(s.map.solid[idx(s, d.tx, d.ty)]).toBe(0);
    expect(s.progress.gates).toEqual(['vault']);
    expect(s.saveRequested).toBe(true);
    // A new game with that progress has the vault open.
    const t = island();
    applyProgress(t, { ...emptyProgress(), gates: ['vault'] });
    for (const d of doors) expect(t.map.solid[idx(t, d.tx, d.ty)]).toBe(0);
  });

  it('a swimmer in the current is hurt', () => {
    const s = island();
    const c = obj(s, 'crystal', (o) => o.tx > 80);
    // Discharge directly with the player swimming next to the crystal.
    const p = s.player;
    p.x = (c.tx - 1) * 16 + 8;
    p.y = c.ty * 16 + 14;
    p.z = s.map.elev[idx(s, c.tx - 1, c.ty)];
    p.swimming = true;
    const hp = p.hp;
    discharge(s, idx(s, c.tx, c.ty));
    expect(p.hp).toBeLessThan(hp);
  });
});
