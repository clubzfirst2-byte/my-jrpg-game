import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { areaAt, tileFeet } from '../../src/game/world/features.js';
import { dialogueView, advance } from '../../src/game/npc/talk.js';
import { msUntilHour } from '../../src/game/world/interiors.js';
import { hourOf, CLOCK } from '../../src/game/env/weather.js';
import { ignite } from '../../src/game/env/envSim.js';

// P10.1: inside the village houses — doors, walls, the shop counter, beds and the stove.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const world = () => {
  const s = createGameState(WORLD);
  s.enemies = [];
  s.enemySpawns = [];
  return s;
};
const HOUSES = ['shop', 'kitchen', 'elder_house', 'inn'];
const place = (s, tx, ty, facing = 'up') => {
  const f = tileFeet(s.map, tx, ty);
  const aim = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[facing];
  Object.assign(s.player, { x: f.x, y: f.y, prevX: f.x, prevY: f.y, z: 0, prevZ: 0, groundZ: 0, facing, aimX: aim[0], aimY: aim[1] });
};
const walk = (s, moveX, moveY, steps) => {
  for (let i = 0; i < steps; i++) stepGame(s, { ...none, moveX, moveY });
};
const room = (s) => areaAt(s, s.player.x, s.player.y)?.id ?? null;

describe('doors', () => {
  it('every village house has a door in and a mat out', () => {
    for (const id of HOUSES) {
      expect(WORLD.warps.filter((w) => w.id === `${id}-in`)).toHaveLength(1);
      expect(WORLD.warps.filter((w) => w.id === `${id}-out`)).toHaveLength(1);
      const a = WORLD.areas.find((x) => x.id === id);
      expect(a?.home).toBe(true);
      expect(a?.name).toBeTruthy();
    }
  });

  it('walking up into a door enters the house; walking down onto the mat leads back out', () => {
    for (const id of HOUSES) {
      const s = world();
      const door = WORLD.warps.find((w) => w.id === `${id}-in`);
      place(s, door.tx, door.ty + 1);
      walk(s, 0, -1, 40);
      expect(room(s)).toBe(id);
      // Inside: walk back down to the mat.
      for (let k = 0; k < 120 && room(s) !== null; k++) stepGame(s, { ...none, moveY: 1 });
      expect(room(s)).toBe(null);
      expect(Math.floor(s.player.x / 16)).toBe(door.tx);
      expect(Math.floor(s.player.y / 16)).toBe(door.ty + 1);
    }
  });

  it('walls hold: no walking through the sides, no climbing the back wall', () => {
    const s = world();
    const a = WORLD.areas.find((x) => x.id === 'kitchen');
    place(s, a.tx + 6, a.ty + 7); // a row with no furniture
    walk(s, -1, 0, 120);
    expect(Math.floor(s.player.x / 16)).toBe(a.tx + 1);
    walk(s, 1, 0, 240);
    expect(Math.floor(s.player.x / 16)).toBe(a.tx + a.tw - 2);
    place(s, a.tx + 9, a.ty + 5);
    walk(s, 0, -1, 60 * 4);
    expect(s.player.climbing).toBe(false);
    expect(room(s)).toBe('kitchen');
    expect(s.player.z).toBe(0);
  });
});

describe('the shop', () => {
  it('the shopkeeper stays behind the counter and is talked to across it', () => {
    const s = world();
    const m = s.npcs.find((n) => n.id === 'merchant');
    const at = { x: m.x, y: m.y };
    const a = WORLD.areas.find((x) => x.id === 'shop');
    expect(areaAt(s, m.x, m.y)?.id).toBe('shop');
    place(s, a.tx + 4, a.ty + 4); // somewhere else in the room
    walk(s, 0, 0, 60 * 10);
    expect(Math.hypot(m.x - at.x, m.y - at.y)).toBeLessThan(0.5); // never strolls
    place(s, Math.floor(m.x / 16), Math.floor(m.y / 16) + 2); // in front of the counter
    stepGame(s, { ...none, attack: true });
    expect(s.dialogue?.id).toBe('merchant');
    expect(s.player.action).toBe('none');
  });
});

describe('beds', () => {
  const inBed = () => {
    const s = world();
    const bed = WORLD.envObjects.find((o) => o.type === 'bed' && areaAt(s, o.tx * 16 + 8, o.ty * 16 + 8)?.id === 'inn');
    place(s, bed.tx, bed.ty + 1);
    stepGame(s, none);
    return s;
  };

  it('in front of a bed, the button says sleep and the attack button asks how long', () => {
    const s = inBed();
    expect(s.nearby).toBe('sleep');
    stepGame(s, { ...none, attack: true });
    expect(s.dialogue?.id).toBe('bed');
    expect(dialogueView(s).choices).toEqual(['朝まで眠る', '夕方まで眠る', 'やめておく']);
  });

  it('sleeping until morning: the clock jumps to 6:00, hearts are full, the game is saved', () => {
    const s = inBed();
    s.player.hp = 3;
    const before = s.env.now;
    stepGame(s, { ...none, attack: true });
    s.saveRequested = false;
    advance(s, 0);
    expect(hourOf(s.env.now)).toBe(6);
    expect(s.env.now).toBeGreaterThan(before);
    expect(s.player.hp).toBe(s.player.maxHp);
    expect(s.saveRequested).toBe(true);
    expect(s.events.some((e) => e.type === 'slept')).toBe(true);
    advance(s);
    expect(s.dialogue).toBe(null);
  });

  it('sleeping until evening, and "not now" changes nothing', () => {
    const s = inBed();
    stepGame(s, { ...none, attack: true });
    advance(s, 1);
    expect(hourOf(s.env.now)).toBe(18);
    const t = inBed();
    const now = t.env.now;
    stepGame(t, { ...none, attack: true });
    advance(t, 2);
    expect(t.dialogue).toBe(null);
    expect(t.env.now - now).toBeLessThan(1000);
  });

  it('time asleep always moves forward (to the next such hour)', () => {
    expect(msUntilHour(5 * CLOCK.hourMs, 6)).toBe(CLOCK.hourMs);
    expect(msUntilHour(7 * CLOCK.hourMs, 6)).toBe(23 * CLOCK.hourMs);
    expect(msUntilHour(6 * CLOCK.hourMs, 6)).toBe(24 * CLOCK.hourMs);
  });

  it('a fire left burning outside has moved on by morning (fast-forwarded, the same way every time)', () => {
    const run = (sleep) => {
      const s = world();
      // Light the grass by the village, then go to bed (or just stand in the inn as long).
      const door = WORLD.warps.find((w) => w.id === 'inn-in');
      place(s, door.tx, door.ty + 1);
      ignite(s.env, s.map, (door.ty + 3) * s.map.width + door.tx + 4);
      walk(s, 0, 0, 30);
      const bed = WORLD.envObjects.find((o) => o.type === 'bed' && areaAt(s, o.tx * 16 + 8, o.ty * 16 + 8)?.id === 'inn');
      place(s, bed.tx, bed.ty + 1);
      if (sleep) {
        stepGame(s, { ...none, attack: true });
        advance(s, 0);
        advance(s);
      }
      walk(s, 0, 0, 5);
      // Back outside: the region wakes and is fast-forwarded to now.
      place(s, door.tx, door.ty + 1, 'down');
      walk(s, 0, 0, 120);
      return [...s.env.cells.values()].filter((c) => c.ashUntil > 0).length;
    };
    const slept = run(true);
    expect(slept).toBeGreaterThan(run(false) * 2);
    expect(run(true)).toBe(slept);
  });
});

describe('the kitchen', () => {
  it('the stove is a place to cook', () => {
    const s = world();
    const stove = WORLD.envObjects.find((o) => o.type === 'stove');
    place(s, stove.tx, stove.ty + 1);
    stepGame(s, none);
    expect(s.nearby).toBe('cook');
  });
});
