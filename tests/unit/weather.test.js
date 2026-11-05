import { describe, it, expect } from 'vitest';
import { CLOCK, WEATHER, SEASON, inSeason, hourOf, clockText, weatherAt, rainWetAt, ambientAt, isDark } from '../../src/game/env/weather.js';
import { parseMap } from '../../src/game/world/tilemap.js';
import { createEnv, stepEnv, ignite, ENV, envSummary } from '../../src/game/env/envSim.js';
import { createGameState, stepGame } from '../../src/game/state.js';
import { CLIMB } from '../../src/game/entities/climbing.js';
import { GLIDE } from '../../src/game/entities/glider.js';
import { strike, STORM } from '../../src/game/env/weatherActions.js';
import { applyProgress, emptyProgress } from '../../src/game/world/features.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const H = CLOCK.hourMs;

describe('clock', () => {
  it('a day is 24 game hours of one real minute each', () => {
    expect(hourOf(7 * H)).toBe(7);
    expect(hourOf(CLOCK.dayMs + 13.5 * H)).toBe(13.5);
    expect(clockText(19.75 * H)).toBe('19:45');
  });

  it('nights are dark, days are full light, weather dims the sky', () => {
    expect(isDark(ambientAt(2 * H, 'clear'))).toBe(true);
    expect(ambientAt(12 * H, 'clear')).toEqual({ r: 1, g: 1, b: 1 });
    expect(ambientAt(12 * H, 'storm').r).toBeLessThan(ambientAt(12 * H, 'rain').r);
    expect(isDark(ambientAt(12 * H, 'clear'))).toBe(false);
  });
});

describe('weather', () => {
  it('is the same for the same seed and time, and changes every few hours', () => {
    expect(weatherAt(1, 30 * H)).toEqual(weatherAt(1, 30 * H));
    const kinds = new Set();
    for (let slot = 0; slot < 1200; slot++) kinds.add(weatherAt(1, CLOCK.dayMs + slot * WEATHER.slotMs).kind);
    expect([...kinds].sort()).toEqual(['clear', 'cloudy', 'rain', 'snow', 'storm']);
  });

  it('roughly matches the planned chances of each season (P10.2)', () => {
    const yearMs = 4 * SEASON.days * CLOCK.dayMs;
    for (const id of SEASON.order) {
      const count = { clear: 0, cloudy: 0, rain: 0, storm: 0, snow: 0 };
      let n = 0;
      // Many years, only the slots of this season.
      for (let year = 1; year < 60; year++) {
        const start = inSeason(year * yearMs, id);
        for (let slot = 0; slot < (SEASON.days * CLOCK.dayMs) / WEATHER.slotMs; slot++) {
          count[weatherAt(3, start + slot * WEATHER.slotMs).kind]++;
          n++;
        }
      }
      const c = WEATHER.chance[id];
      expect(count.storm / n).toBeCloseTo(c.storm, 1);
      expect(count.rain / n).toBeCloseTo(c.rain, 1);
      expect(count.snow / n).toBeCloseTo(c.snow, 1);
    }
  });

  it('the first morning is always clear, and an override wins', () => {
    for (let t = 0; t < WEATHER.clearUntilMs; t += 10_000) expect(weatherAt(5, t).kind).toBe('clear');
    expect(weatherAt(5, 1000, 'storm').kind).toBe('storm');
  });

  it('things stay wet for a while after the rain', () => {
    expect(rainWetAt(1, 100, 'rain')).toBe(true);
    expect(rainWetAt(1, 100, null)).toBe(false);
  });
});

describe('rain and wind on fire', () => {
  const field = (w, h) => parseMap(Array.from({ length: h }, () => '.'.repeat(w)));
  const run = (env, map, player, ms) => {
    for (let k = 0; k < ms / (1000 / 60); k++) stepEnv(env, map, player, 1000 / 60);
  };

  it('rain puts fires out and nothing catches fire', () => {
    const map = field(16, 16);
    const env = createEnv(map, map.objects);
    for (let i = 0; i < 16 * 16; i += 3) ignite(env, map, i);
    const lit = env.burning.size;
    env.weatherOverride = 'rain';
    run(env, map, { x: 8, y: 8 }, 3000);
    expect(env.burning.size).toBeLessThan(lit / 4);
    expect(ignite(env, map, 5)).toBe(false);
  });

  it('under a roof (cave) the rain does not reach', () => {
    const map = field(4, 1);
    const env = createEnv(map, map.objects);
    env.weatherOverride = 'rain';
    env.indoor[2] = 1;
    expect(ignite(env, map, 1)).toBe(false);
    expect(ignite(env, map, 2)).toBe(true);
  });

  it('fire runs downwind faster than upwind', () => {
    // Find a slot with a strong east or west wind, then burn a long strip from its middle.
    let t = CLOCK.dayMs;
    while (Math.abs(weatherAt(1, t).windX) < 0.5 || weatherAt(1, t).kind === 'rain' || weatherAt(1, t).kind === 'storm') t += WEATHER.slotMs;
    const w = weatherAt(1, t);
    const map = field(120, 1);
    const env = createEnv(map, map.objects, 1, t);
    ignite(env, map, 60);
    run(env, map, { x: 60 * 16, y: 8 }, 8000);
    let east = 0;
    let west = 0;
    for (const [i, c] of env.cells) {
      if (!(c.ashUntil > 0 || env.burning.has(i))) continue;
      if (i > 60) east++;
      if (i < 60) west++;
    }
    if (w.windX > 0) expect(east).toBeGreaterThan(west);
    else expect(west).toBeGreaterThan(east);
  });

  it('a far fire that was rained on while frozen is found out when the player returns', () => {
    // Find a clear slot followed by a rainy one, and a clear slot followed by a clear one.
    const kind = (slot) => weatherAt(7, slot * WEATHER.slotMs).kind;
    const after = (next) => {
      for (let slot = 20; ; slot++) if (kind(slot) === 'clear' && kind(slot + 1) === next) return (slot + 1) * WEATHER.slotMs;
    };
    // Light a fire 2 s before the boundary, walk far away, come back 40 s later.
    const scenario = (boundary) => {
      const map = field(80, 16);
      const env = createEnv(map, map.objects, 7, boundary - 2100);
      const far = { x: 2 * 16, y: 8 * 16 };
      run(env, map, far, 100);
      for (let x = 66; x < 76; x++) expect(ignite(env, map, 8 * 80 + x)).toBe(true);
      run(env, map, far, 40_000);
      run(env, map, { x: 66 * 16, y: 8 * 16 }, 200);
      return envSummary(env).ash + env.burning.size;
    };
    expect(scenario(after('rain'))).toBeLessThan(scenario(after('clear')));
  });
});

describe('the player in the weather', () => {
  it('rain makes climbing slippery: less height for the same climb', () => {
    const corridor = { ground: ['##########', '#P.......#', '##########'], height: ['0000000000', '000gggggg0', '0000000000'] };
    const climb = (rain) => {
      const s = createGameState(corridor);
      s.env.weatherOverride = rain ? 'rain' : null;
      for (let i = 0; i < 300 && !s.player.climbing; i++) stepGame(s, { ...none, moveX: 1 });
      const z0 = s.player.z;
      for (let i = 0; i < 150; i++) stepGame(s, { ...none, moveX: 1 });
      return s.player.z - z0;
    };
    const dry = climb(false);
    const wet = climb(true);
    expect(dry).toBeCloseTo(CLIMB.speed * 2.5, 0);
    expect(wet).toBeLessThan(dry - CLIMB.slipDistance);
  });

  it('rising air over a fire lifts the glider', () => {
    const s = createGameState(['..........', '....P.....', '..........']);
    const p = s.player;
    expect(ignite(s.env, s.map, 1 * s.map.width + 3)).toBe(true);
    p.z = p.prevZ = 30;
    p.grounded = false;
    p.gliding = true;
    const z0 = p.z;
    for (let i = 0; i < 30; i++) stepGame(s, none);
    expect(p.z).toBeGreaterThan(z0 + GLIDE.updraftSpeed * 0.3);
    for (let i = 0; i < 600; i++) stepGame(s, none);
    expect(p.z).toBeLessThanOrEqual(GLIDE.updraftHeight + 2); // it only carries so high
  });

  it('lightning hurts whoever is near the strike', () => {
    const s = createGameState(['..........', '....P.....', '..........']);
    s.enemies = [];
    const hp = s.player.hp;
    strike(s, 1 * s.map.width + 4);
    expect(s.player.hp).toBe(hp - STORM.playerDamage);
    expect(s.events.some((e) => e.type === 'lightning')).toBe(true);
  });

  it('the time of day is saved and restored', () => {
    const s = createGameState(['....P....']);
    applyProgress(s, { ...emptyProgress(), worldMs: 21 * H });
    expect(hourOf(s.env.now)).toBe(21);
    stepGame(s, none);
    expect(s.env.now).toBeGreaterThan(21 * H);
    expect(ENV.tickMs).toBeGreaterThan(0);
  });
});
