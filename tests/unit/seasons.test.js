import { describe, it, expect } from 'vitest';
import { CLOCK, SEASON, seasonAt, inSeason, weatherAt, rainWetAt } from '../../src/game/env/weather.js';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { applyProgress, emptyProgress } from '../../src/game/world/features.js';
import { setWorldTime } from '../../src/game/env/envSim.js';
import { validateItems } from '../../src/game/items/validateItems.js';
import ITEMS from '../../data/items.json';

// P10.2: the four seasons — the calendar, the skies, and what each season brings.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const DAY = CLOCK.dayMs;
const YEAR = 4 * SEASON.days * DAY;

describe('the calendar', () => {
  it('seven days each: spring, summer, autumn, winter, and round again', () => {
    expect(seasonAt(0)).toMatchObject({ id: 'spring', day: 1, name: '春' });
    expect(seasonAt(6 * DAY + DAY - 1)).toMatchObject({ id: 'spring', day: 7 });
    expect(seasonAt(7 * DAY)).toMatchObject({ id: 'summer', day: 1, name: '夏' });
    expect(seasonAt(14 * DAY)).toMatchObject({ id: 'autumn', day: 1, name: '秋' });
    expect(seasonAt(27 * DAY + 5 * CLOCK.hourMs)).toMatchObject({ id: 'winter', day: 7, name: '冬' });
    expect(seasonAt(YEAR)).toMatchObject({ id: 'spring', day: 1 });
  });

  it('jumping to a season keeps the hour', () => {
    const t = inSeason(3 * DAY + 15 * CLOCK.hourMs, 'autumn');
    expect(seasonAt(t)).toMatchObject({ id: 'autumn', day: 1 });
    expect((t % DAY) / CLOCK.hourMs).toBe(15);
  });
});

describe('the skies', () => {
  const kindsIn = (id, climate = 'temperate') => {
    const kinds = new Set();
    for (let year = 1; year < 30; year++) {
      const start = inSeason(year * YEAR, id);
      for (let t = start; t < start + SEASON.days * DAY; t += 3 * CLOCK.hourMs) kinds.add(weatherAt(7, t, null, climate).kind);
    }
    return kinds;
  };

  it('it snows only in winter, and never rains then', () => {
    expect(kindsIn('winter').has('snow')).toBe(true);
    expect(kindsIn('winter').has('rain')).toBe(false);
    expect(kindsIn('winter').has('storm')).toBe(false);
    for (const id of ['spring', 'summer', 'autumn']) expect(kindsIn(id).has('snow')).toBe(false);
  });

  it('the desert never gets snow (nor rain)', () => {
    for (const id of SEASON.order) {
      const k = kindsIn(id, 'dry');
      expect(k.has('snow') || k.has('rain') || k.has('storm')).toBe(false);
    }
  });

  it('snow puts fires out like rain, but cliffs are not slippery', () => {
    expect(rainWetAt(1, 100, 'snow')).toBe(true);
    const s = createGameState(WORLD);
    s.env.weatherOverride = 'snow';
    stepGame(s, none);
    expect(s.player.rainOn).toBe(false);
  });
});

describe('what each season brings', () => {
  const at = (id) => {
    const s = createGameState(WORLD);
    applyProgress(s, { ...emptyProgress(), worldMs: inSeason(YEAR, id) + 10 * CLOCK.hourMs });
    stepGame(s, none);
    s.enemies = s.enemies.filter((e) => !e.boss); // (the cores of the murk are there all year)
    return s;
  };
  const seasonal = (s, season) => s.pickups.filter((p) => p.mapId && WORLD.pickups.find((d) => d.id === p.mapId)?.seasons?.includes(season)).length;

  it('season items lie in the world only in their season', () => {
    for (const id of SEASON.order) {
      const s = at(id);
      expect(seasonal(s, id)).toBeGreaterThan(0);
      for (const other of SEASON.order) if (other !== id) expect(seasonal(s, other)).toBe(0);
    }
  });

  it('beasts come out in packs in autumn; one keeps to its den in winter', () => {
    const all = WORLD.enemies.length;
    const autumnOnly = WORLD.enemies.filter((e) => e.seasons && !e.seasons.includes('summer') && e.seasons.includes('autumn')).length;
    const notWinter = WORLD.enemies.filter((e) => e.seasons && !e.seasons.includes('winter')).length;
    expect(at('autumn').enemies).toHaveLength(all - WORLD.enemies.filter((e) => e.seasons && !e.seasons.includes('autumn')).length);
    expect(at('summer').enemies).toHaveLength(all - autumnOnly);
    expect(at('winter').enemies).toHaveLength(all - notWinter);
    expect(at('autumn').enemies.length).toBeGreaterThan(at('summer').enemies.length);
    expect(at('winter').enemies.length).toBeLessThan(at('summer').enemies.length);
  });

  it('when the season turns, the world changes with it (and says so)', () => {
    const s = createGameState(WORLD);
    stepGame(s, none);
    expect(s.season).toBe('spring');
    setWorldTime(s.env, 14 * DAY - 1000); // the last second of summer
    stepGame(s, none);
    expect(s.season).toBe('summer');
    for (let i = 0; i < 90; i++) stepGame(s, none);
    expect(s.season).toBe('autumn');
    expect(s.events.filter((e) => e.type === 'season').map((e) => e.id)).toEqual(['summer', 'autumn']);
    expect(seasonal(s, 'autumn')).toBeGreaterThan(0);
    expect(seasonal(s, 'summer')).toBe(0);
  });

  it('season names in the map data are checked', () => {
    expect(validateItems(ITEMS, WORLD)).toEqual([]);
    const bad = { pickups: [{ id: 'x', item: 'mushroom', tx: 0, ty: 0, seasons: ['monsoon'] }], enemies: [{ kind: 'beast', tx: 0, ty: 0, seasons: [] }] };
    const errs = validateItems(ITEMS, bad);
    expect(errs.some((e) => e.includes('monsoon'))).toBe(true);
    expect(errs.some((e) => e.includes('enemy 0'))).toBe(true);
  });
});
