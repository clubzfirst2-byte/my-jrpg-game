import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { STEP_SEC } from '../../src/game/core/fixedStep.js';
import { WORLD } from '../../src/game/world/world.js';
import { BOSS_KINDS, PHASE2_WINDUP, BOSS_REWARD, inArena, activeBoss } from '../../src/game/entities/bosses.js';
import { hitEnemy } from '../../src/game/combat/damage.js';
import { applyProgress, emptyProgress } from '../../src/game/world/features.js';
import { countOf } from '../../src/game/items/inventory.js';

// P10.4 completion check (DESIGN.md roadmap): the bosses' attack patterns.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const MS = STEP_SEC * 1000;

/** A world with only one boss, the player standing in its arena at a distance. */
function fight(id, { dx = 0, dy = 40 } = {}) {
  const s = createGameState(WORLD);
  s.enemies = s.enemies.filter((e) => e.boss && e.bossId === id);
  s.enemySpawns = [];
  const b = s.enemies[0];
  Object.assign(s.player, { x: b.x + dx, y: b.y + dy, prevX: b.x + dx, prevY: b.y + dy, z: b.z, groundZ: b.z });
  s.player.maxHp = s.player.hp = 400; // survive to watch every pattern
  s.pin = { x: b.x + dx, y: b.y + dy };
  return { s, b };
}
/** One step with the player held in place (knockback would carry them out of the arena). */
function tick(s, input = none) {
  Object.assign(s.player, { x: s.pin.x, y: s.pin.y, prevX: s.pin.x, prevY: s.pin.y, knockMs: 0 });
  stepGame(s, input);
}
/** Steps until the boss starts its next pattern (a new wind-up); returns the pattern. */
function nextPattern(s, b, maxMs = 6000) {
  const start = b.patternIndex;
  for (let t = 0; t < maxMs; t += MS) {
    tick(s);
    if (b.patternIndex !== start) return b.pattern;
  }
  return null;
}

describe('the four cores', () => {
  it('one in each wild region, each in its own arena', () => {
    expect(WORLD.bosses.map((b) => b.kind).sort()).toEqual(['frost', 'root', 'sand', 'storm']);
    const s = createGameState(WORLD);
    const bosses = s.enemies.filter((e) => e.boss);
    expect(bosses).toHaveLength(4);
    for (const b of bosses) {
      expect(inArena(b, s.map, b.x, b.y)).toBe(true);
      expect(b.hp).toBe(BOSS_KINDS[b.bossKind].hp);
    }
  });
});

describe('waking and staying home', () => {
  it('sleeps until the player steps into the arena; does not leave it', () => {
    const { s, b } = fight('core_forest', { dy: 400 });
    for (let i = 0; i < 120; i++) stepGame(s, none);
    expect(b.awake).toBe(false);
    expect(activeBoss(s)).toBe(null);
    s.player.y = b.y + 40;
    stepGame(s, none);
    expect(b.awake).toBe(true);
    expect(s.events.some((e) => e.type === 'bossAwake')).toBe(true);
    for (let i = 0; i < 60 * 20; i++) {
      stepGame(s, none);
      expect(inArena(b, s.map, b.x, b.y)).toBe(true);
    }
  });
});

describe('attack patterns (phase 1 cycles its list; every attack is telegraphed)', () => {
  for (const [id, kind] of [['core_forest', 'root'], ['core_mountains', 'frost'], ['core_desert', 'sand'], ['core_lake', 'storm']]) {
    it(`${BOSS_KINDS[kind].name}: ${BOSS_KINDS[kind].phase1.join(' → ')}`, () => {
      const { s, b } = fight(id);
      const seen = [];
      for (let n = 0; n < BOSS_KINDS[kind].phase1.length * 2; n++) {
        seen.push(nextPattern(s, b));
        // The wind-up lasts the kind's wind-up time before anything comes out.
        const shots = new Set(s.projectiles.map((p) => p.id));
        for (let t = MS; t < BOSS_KINDS[kind].windupMs - MS; t += MS) tick(s);
        expect(b.state).toBe('windup');
        expect(s.projectiles.every((p) => shots.has(p.id))).toBe(true);
      }
      const k = BOSS_KINDS[kind].phase1;
      expect(seen).toEqual([...k, ...k]);
    });
  }

  it('volley: a fan of orbs toward the player; ring: orbs all around', () => {
    const { s, b } = fight('core_desert');
    expect(nextPattern(s, b)).toBe('volley');
    const before = s.projectiles.length;
    for (let t = 0; t < BOSS_KINDS.sand.windupMs + 2 * MS; t += MS) stepGame(s, none);
    const fan = s.projectiles.slice(before);
    expect(fan).toHaveLength(BOSS_KINDS.sand.shots);
    // All heading down (toward the player south of it), spread out.
    expect(fan.every((p) => p.vy > 0)).toBe(true);
    expect(new Set(fan.map((p) => Math.round(p.vx))).size).toBe(BOSS_KINDS.sand.shots);
    const r = fight('core_lake');
    expect(nextPattern(r.s, r.b)).toBe('ring');
    for (let t = 0; t < BOSS_KINDS.storm.windupMs + 2 * MS; t += MS) stepGame(r.s, none);
    const ring = r.s.projectiles;
    expect(ring.length).toBeGreaterThanOrEqual(BOSS_KINDS.storm.shots);
    const angles = ring.slice(0, BOSS_KINDS.storm.shots).map((p) => Math.atan2(p.vy, p.vx));
    expect(angles.some((a) => a < -1) && angles.some((a) => a > 1) && angles.some((a) => Math.abs(a) < 0.5)).toBe(true);
  });

  it('slam: hurts on the ground nearby, misses a jumping player and anyone outside its radius', () => {
    const run = (dy, jump) => {
      const { s, b } = fight('core_mountains', { dy });
      const hp = s.player.hp;
      expect(nextPattern(s, b)).toBe('slam');
      for (let t = 0; t < BOSS_KINDS.frost.windupMs + 300; t += MS) {
        if (jump) Object.assign(s.player, { z: s.player.groundZ + 20, grounded: false, vz: 0 });
        stepGame(s, none);
        if (jump) s.player.z = Math.max(s.player.z, s.player.groundZ + 20);
      }
      return hp - s.player.hp;
    };
    expect(run(30, false)).toBeGreaterThan(0);
    expect(run(BOSS_KINDS.frost.slamRadius + 30, false)).toBe(0);
    expect(run(30, true)).toBe(0);
  });

  it('charge: dashes along the line it aimed at the end of the wind-up', () => {
    const { s, b } = fight('core_forest', { dx: 60, dy: 0 });
    expect(nextPattern(s, b)).toBe('charge');
    for (let t = MS; t < BOSS_KINDS.root.windupMs; t += MS) stepGame(s, none);
    const x0 = b.x;
    for (let t = 0; t < 300; t += MS) stepGame(s, none);
    expect(b.x - x0).toBeGreaterThan(30); // toward the player (east)
  });
});

describe('phase 2, weakness, parry and defeat', () => {
  it('below half health: shorter wind-ups and the phase-2 list', () => {
    const { s, b } = fight('core_lake');
    b.hp = Math.floor(b.maxHp / 2);
    stepGame(s, none);
    expect(b.phase).toBe(2);
    expect(b.windupMs).toBe(Math.round(BOSS_KINDS.storm.windupMs * PHASE2_WINDUP));
    const seen = [];
    for (let n = 0; n < BOSS_KINDS.storm.phase2.length; n++) seen.push(nextPattern(s, b));
    expect(seen).toEqual(BOSS_KINDS.storm.phase2);
  });

  it('cores that burn take double damage from fire; bosses do not flinch', () => {
    const { s, b } = fight('core_forest');
    const hp = b.hp;
    hitEnemy(s, b, { owner: 'player', id: 'a', damage: 4, from: { x: b.x, y: b.y + 20 }, kind: 'melee' });
    expect(b.hp).toBe(hp - 4);
    expect(b.state).not.toBe('stun');
    hitEnemy(s, b, { owner: 'player', id: 'b', damage: 4, from: { x: b.x, y: b.y + 20 }, kind: 'projectile', element: 'fire' });
    expect(b.hp).toBe(hp - 4 - 8);
    const d = fight('core_desert');
    hitEnemy(d.s, d.b, { owner: 'player', id: 'c', damage: 4, from: { x: 0, y: 0 }, kind: 'projectile', element: 'fire' });
    expect(d.b.hp).toBe(d.b.maxHp - 4); // the sand-wraith does not burn
  });

  it('a perfect guard against the charge stuns the boss', () => {
    const { s, b } = fight('core_forest', { dx: 0, dy: 30 });
    expect(nextPattern(s, b)).toBe('charge');
    for (let t = MS; t < BOSS_KINDS.root.windupMs - MS; t += MS) stepGame(s, none);
    // Raise the guard just as the charge comes (facing the boss).
    Object.assign(s.player, { facing: 'up', aimX: 0, aimY: -1 });
    for (let i = 0; i < 40 && b.state !== 'stun'; i++) stepGame(s, { ...none, guard: true });
    expect(b.state).toBe('stun');
    expect(s.events.some((e) => e.type === 'bossStun')).toBe(true);
  });

  it('defeat purifies the core for good: reward once, saved, never back', () => {
    const { s, b } = fight('core_mountains');
    const shards = countOf(s.progress.inv, 'star_shard');
    const money = s.progress.inv.money;
    hitEnemy(s, b, { owner: 'player', id: 'z', damage: 999, from: { x: b.x, y: b.y + 20 }, kind: 'melee' });
    stepGame(s, none);
    stepGame(s, none);
    expect(s.progress.bosses).toEqual(['core_mountains']);
    expect(countOf(s.progress.inv, 'star_shard')).toBe(shards + 1);
    expect(s.progress.inv.money).toBe(money + BOSS_REWARD.money);
    expect(s.events.filter((e) => e.type === 'bossDown')).toHaveLength(1);
    expect(s.saveRequested).toBe(true);
    // Loaded again: the core is gone; the others still wait.
    const t = createGameState(WORLD);
    applyProgress(t, { ...emptyProgress(), bosses: ['core_mountains'] });
    stepGame(t, none);
    expect(t.enemies.filter((e) => e.boss).map((e) => e.bossId).sort()).toEqual(['core_desert', 'core_forest', 'core_lake']);
  });
});
