import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { STEP_SEC } from '../../src/game/core/fixedStep.js';
import { ENEMY_KINDS, PARRY_STUN_MS, strideFactor } from '../../src/game/entities/enemies.js';
import { hitEnemy } from '../../src/game/combat/damage.js';
import { dropsFor } from '../../src/game/items/inventory.js';
import { WORLD } from '../../src/game/world/world.js';
import { REGIONS } from '../../src/game/world/maps/regions.js';
import DATA from '../../data/items.json';

// v1.0 (docs/enemy/ENEMY_BOSS_DESIGN.md 2.3, 2.4): 澱だまり (slime) and 遺跡の番兵 (sentinel).

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const MS = STEP_SEC * 1000;

/** Open 24x12 arena, player at tile (5,6). */
function arena(enemies) {
  const rows = [];
  for (let y = 0; y < 12; y++) {
    let r = '';
    for (let x = 0; x < 24; x++) r += x === 0 || y === 0 || x === 23 || y === 11 ? '#' : x === 5 && y === 6 ? 'P' : '.';
    rows.push(r);
  }
  return createGameState({ ground: rows, enemies });
}
/** Keeps the player where it is (knockback would move it) with plenty of health. */
function hold(s) {
  const p = s.player;
  p.maxHp = p.hp = 400;
  const at = { x: p.x, y: p.y };
  return () => Object.assign(p, { x: at.x, y: at.y, prevX: at.x, prevY: at.y, knockMs: 0 });
}
/** Steps until `cond` (or `maxMs`); returns whether it happened. */
function until(s, cond, maxMs, before = () => {}) {
  for (let t = 0; t < maxMs; t += MS) {
    before();
    stepGame(s, none);
    if (cond()) return true;
  }
  return false;
}

describe('澱だまり (slime)', () => {
  it('is in ENEMY_KINDS with the design numbers: weak, short wind-up, a small body slam', () => {
    const k = ENEMY_KINDS.slime;
    expect(k.hp).toBeLessThan(ENEMY_KINDS.beast.hp);
    expect(k.damage).toBe(1);
    expect(k.attack).toBe('lunge');
    expect(k.hopAirMs).toBeLessThan(k.hopMs);
  });

  it('hops: covers ground only while in the air, then sits still until the next hop', () => {
    const s = arena([{ kind: 'slime', tx: 9, ty: 6 }]);
    const pin = hold(s);
    const e = s.enemies[0];
    let moved = 0;
    let still = 0;
    for (let i = 0; i < 60; i++) {
      pin();
      const x0 = e.x;
      stepGame(s, none);
      if (e.state !== 'idle') break;
      const dx = Math.abs(e.x - x0);
      if (dx > 0.01) {
        moved++;
        expect(e.hopMs, 'moved while on the ground').toBeLessThan(ENEMY_KINDS.slime.hopAirMs + MS);
      } else still++;
    }
    expect(moved).toBeGreaterThan(0);
    expect(still).toBeGreaterThan(0);
    expect(e.x).toBeLessThan(9 * 16 + 8); // toward the player (west)
  });

  it('two slimes do not hop in step', () => {
    const s = arena([{ kind: 'slime', tx: 12, ty: 3 }, { kind: 'slime', tx: 12, ty: 9 }]);
    expect(s.enemies[0].hopMs).not.toBe(s.enemies[1].hopMs);
  });

  it('lands, squashes (wind-up), then body-slams the player for its damage', () => {
    const s = arena([{ kind: 'slime', tx: 7, ty: 6 }]);
    const pin = hold(s);
    const e = s.enemies[0];
    const hp = s.player.hp;
    expect(until(s, () => e.state === 'windup', 4000, pin)).toBe(true);
    expect(strideFactor(e, ENEMY_KINDS.slime)).toBe(0); // on the ground
    const x0 = e.x;
    expect(until(s, () => e.state === 'attack', ENEMY_KINDS.slime.windupMs + 100, pin)).toBe(true);
    expect(Math.abs(e.x - x0)).toBeLessThan(0.5); // the wind-up stays put
    expect(until(s, () => s.player.hp < hp, 400, pin)).toBe(true);
    expect(hp - s.player.hp).toBe(ENEMY_KINDS.slime.damage);
  });

  it('a sword hit staggers it like the beast', () => {
    const s = arena([{ kind: 'slime', tx: 9, ty: 6 }]);
    const e = s.enemies[0];
    hitEnemy(s, e, { owner: 'player', id: 'x', damage: 2, from: { x: e.x - 8, y: e.y }, kind: 'melee' });
    expect(e.hp).toBe(ENEMY_KINDS.slime.hp - 2);
    expect(e.state).toBe('stun');
  });
});

describe('遺跡の番兵 (sentinel)', () => {
  it('is slow: it walks at well under half the beast speed', () => {
    expect(ENEMY_KINDS.sentinel.speed * 2).toBeLessThan(ENEMY_KINDS.beast.speed);
    const s = arena([{ kind: 'sentinel', tx: 9, ty: 6 }]);
    const pin = hold(s);
    const e = s.enemies[0];
    const x0 = e.x;
    for (let t = 0; t < 1000; t += MS) {
      pin();
      stepGame(s, none);
    }
    expect(x0 - e.x).toBeGreaterThan(8);
    expect(x0 - e.x).toBeLessThan(ENEMY_KINDS.sentinel.speed * 1.05);
  });

  /** A sentinel next to the player, already in reach. */
  const near = (dx) => {
    const s = arena([{ kind: 'sentinel', tx: 5, ty: 6 }]);
    const e = s.enemies[0];
    const pin = hold(s);
    Object.assign(e, { x: s.player.x + dx, prevX: s.player.x + dx, y: s.player.y, prevY: s.player.y });
    return { s, e, pin };
  };

  it('winds up (fist raised) for its long wind-up without moving, then slams the ground around it', () => {
    const { s, e, pin } = near(20);
    const hp = s.player.hp;
    expect(until(s, () => e.state === 'windup', 200, pin)).toBe(true);
    const x0 = e.x;
    let windup = 0;
    until(s, () => e.state !== 'windup', 2000, () => {
      pin();
      windup += MS;
    });
    expect(windup).toBeGreaterThanOrEqual(ENEMY_KINDS.sentinel.windupMs - MS);
    expect(e.state).toBe('attack');
    expect(e.x).toBe(x0);
    expect(s.events.some((ev) => ev.type === 'enemySlam')).toBe(true);
    until(s, () => e.state === 'recover', 400, pin);
    expect(hp - s.player.hp).toBe(ENEMY_KINDS.sentinel.damage);
  });

  it('the slam misses a jumping player and anyone outside its radius', () => {
    const run = (dx, jump) => {
      const { s, e, pin } = near(dx);
      // Let it wind up even from afar: it only slams where it stands.
      e.state = 'windup';
      e.t = 0;
      const hp = s.player.hp;
      until(s, () => e.state === 'recover', 2000, () => {
        pin();
        if (jump) Object.assign(s.player, { z: s.player.groundZ + 20, grounded: false, vz: 0 });
      });
      return hp - s.player.hp;
    };
    expect(run(20, false)).toBeGreaterThan(0);
    expect(run(20, true)).toBe(0);
    expect(run(ENEMY_KINDS.sentinel.slamRadius + 12, false)).toBe(0);
  });

  it('swords glance off: half damage, and a sword hit does not interrupt its wind-up', () => {
    const { s, e } = near(20);
    e.state = 'windup';
    e.t = 300;
    hitEnemy(s, e, { owner: 'player', id: 'a', damage: 4, from: { x: s.player.x, y: s.player.y }, kind: 'melee' });
    expect(e.hp).toBe(ENEMY_KINDS.sentinel.hp - 2);
    expect(e.state).toBe('windup');
    expect(e.t).toBe(300);
    // Arrows are not swords.
    hitEnemy(s, e, { owner: 'player', id: 'b', damage: 4, from: { x: s.player.x, y: s.player.y }, kind: 'projectile' });
    expect(e.hp).toBe(ENEMY_KINDS.sentinel.hp - 6);
  });

  it('electricity does double damage and stuns it', () => {
    const { s, e } = near(20);
    e.state = 'windup';
    hitEnemy(s, e, { owner: 'player', id: 'z', damage: 4, from: { x: e.x, y: e.y - 1 }, kind: 'projectile', element: 'shock' });
    expect(e.hp).toBe(ENEMY_KINDS.sentinel.hp - 8);
    expect(e.state).toBe('stun');
  });

  it('a parried slam stuns it', () => {
    const { s, e, pin } = near(20);
    Object.assign(s.player, { aimX: 1, aimY: 0, facing: 'right' });
    e.state = 'windup';
    e.t = 0;
    const hp = s.player.hp;
    // Perfect guard: the guard goes up just before the slam lands.
    for (let t = 0; t < 1400 && e.state !== 'stun'; t += MS) {
      pin();
      const guard = (e.state === 'windup' && e.t >= ENEMY_KINDS.sentinel.windupMs - 3 * MS) || e.state === 'attack';
      stepGame(s, { ...none, guard });
    }
    expect(e.state).toBe('stun');
    expect(e.stunMs).toBe(PARRY_STUN_MS);
    expect(s.player.hp).toBe(hp);
  });

  it('knockback barely moves it', () => {
    const { s, e } = near(20);
    const x0 = e.x;
    hitEnemy(s, e, { owner: 'player', id: 'k', damage: 1, from: { x: e.x - 10, y: e.y }, kind: 'projectile', knock: 1 });
    for (let t = 0; t < 300; t += MS) stepGame(s, none);
    const b = arena([{ kind: 'beast', tx: 5, ty: 6 }]);
    const be = b.enemies[0];
    Object.assign(be, { x: b.player.x + 20, prevX: b.player.x + 20, y: b.player.y, prevY: b.player.y });
    const bx0 = be.x;
    hitEnemy(b, be, { owner: 'player', id: 'k', damage: 1, from: { x: be.x - 10, y: be.y }, kind: 'projectile', knock: 1 });
    for (let t = 0; t < 300; t += MS) stepGame(b, none);
    expect(Math.abs(e.x - x0)).toBeLessThan(Math.abs(be.x - bx0) * 0.5);
  });
});

describe('drops', () => {
  it('both new enemies drop murk crystals', () => {
    for (const kind of ['slime', 'sentinel']) {
      expect(DATA.drops[kind]?.length, kind).toBeGreaterThan(0);
      expect(dropsFor(kind, () => 0).some((d) => d.item === 'murk_crystal')).toBe(true);
    }
    expect(dropsFor('sentinel', () => 0.99).find((d) => d.item === 'murk_crystal').count).toBe(2);
  });

  it('a defeated sentinel leaves its drop on the ground', () => {
    const s = arena([{ kind: 'sentinel', tx: 9, ty: 6 }]);
    const e = s.enemies[0];
    hitEnemy(s, e, { owner: 'player', id: 'kill', damage: 999, from: { x: e.x - 8, y: e.y }, kind: 'projectile' });
    stepGame(s, none);
    expect(s.pickups.some((p) => p.item === 'murk_crystal' && p.count === 2)).toBe(true);
  });
});

describe('where they appear (design 2.3, 2.4)', () => {
  const region = (id) => REGIONS.find((r) => r.id === id);
  const kinds = (r, kind) => r.enemies.filter((e) => e.kind === kind);

  it('slimes by the forest bog pools and in the dark first floor of the mine', () => {
    expect(kinds(region('forest'), 'slime').length).toBeGreaterThanOrEqual(3);
    const mineSlimes = kinds(region('mountains'), 'slime');
    expect(mineSlimes.length).toBeGreaterThan(0);
    for (const e of mineSlimes) expect(e.tx).toBeGreaterThanOrEqual(96); // the east strip of rooms
  });

  it('sentinels at the desert ruins and in the mine', () => {
    expect(kinds(region('desert'), 'sentinel').length).toBeGreaterThanOrEqual(2);
    expect(kinds(region('mountains'), 'sentinel').some((e) => e.tx >= 96)).toBe(true);
  });

  it('not on the first island or in the plains (the beginner areas)', () => {
    expect(kinds(region('plains'), 'slime').length + kinds(region('plains'), 'sentinel').length).toBe(0);
    const isl = WORLD.regions.find((r) => r.id === 'island');
    const onIsland = (e) => e.tx >= isl.tx && e.tx < isl.tx + 128 && e.ty >= isl.ty && e.ty < isl.ty + isl.th; // (with its strip of rooms)
    expect(WORLD.enemies.filter((e) => (e.kind === 'slime' || e.kind === 'sentinel') && onIsland(e))).toEqual([]);
  });

  it('the new spawns come after every older one in each region (nothing placed before moved)', () => {
    for (const r of REGIONS) {
      const firstNew = r.enemies.findIndex((e) => e.kind === 'slime' || e.kind === 'sentinel');
      if (firstNew < 0) continue;
      expect(r.enemies.slice(firstNew).every((e) => e.kind === 'slime' || e.kind === 'sentinel'), r.id).toBe(true);
    }
  });

  it('every new enemy starts on open, walkable ground in the world', () => {
    const s = createGameState(WORLD);
    const news = s.enemies.filter((e) => e.kind === 'slime' || e.kind === 'sentinel');
    expect(news.length).toBe(WORLD.enemies.filter((e) => e.kind === 'slime' || e.kind === 'sentinel').length);
    for (const e of news) {
      const i = Math.floor(e.y / 16) * s.map.width + Math.floor(e.x / 16);
      expect(s.map.solid[i], `${e.kind} at ${e.x},${e.y}`).toBe(0);
    }
  });
});
