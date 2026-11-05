// @ts-check
// Time of day and weather (P5, DESIGN.md 4). Both are pure functions of the world time (ms since the
// world began) and the seed, so the fast-forward of far-away regions knows exactly when it rained
// there (DESIGN.md 4.4) and the same world always has the same skies.
import { roll } from '../core/hashRandom.js';

export const CLOCK = Object.freeze({
  /** One game hour = one real minute: a day lasts 24 minutes. */
  hourMs: 60_000,
  dayMs: 24 * 60_000,
  /** A new game starts at 7:00. */
  startHour: 7,
});

/** P10.2: four seasons of 7 game days each, in this order; a new world starts on the first day of spring. */
export const SEASON = Object.freeze({
  days: 7,
  order: /** @type {const} */ (['spring', 'summer', 'autumn', 'winter']),
  names: /** @type {Record<string, string>} */ ({ spring: '春', summer: '夏', autumn: '秋', winter: '冬' }),
});
/** @typedef {'spring' | 'summer' | 'autumn' | 'winter'} SeasonId */

/**
 * The season at a moment, and which day of it (1..7).
 * @param {number} worldMs @returns {{ id: SeasonId, index: number, day: number, name: string }}
 */
export function seasonAt(worldMs) {
  const dayNo = Math.floor(worldMs / CLOCK.dayMs);
  const index = (((Math.floor(dayNo / SEASON.days) % 4) + 4) % 4);
  const id = SEASON.order[index];
  return { id, index, day: (((dayNo % SEASON.days) + SEASON.days) % SEASON.days) + 1, name: SEASON.names[id] };
}

/** World time at the same hour of the first day of a season (a debug / test helper). @param {number} worldMs @param {SeasonId} id */
export function inSeason(worldMs, id) {
  const yearMs = 4 * SEASON.days * CLOCK.dayMs;
  const hourMs = ((worldMs % CLOCK.dayMs) + CLOCK.dayMs) % CLOCK.dayMs;
  const year = Math.floor(worldMs / yearMs);
  return year * yearMs + SEASON.order.indexOf(id) * SEASON.days * CLOCK.dayMs + hourMs;
}

export const WEATHER = Object.freeze({
  /** Weather changes every 3 game hours. */
  slotMs: 3 * CLOCK.hourMs,
  /** The first morning of a new game is always clear (until noon). */
  clearUntilMs: 12 * CLOCK.hourMs,
  /** Chances of each kind by season (the rest is clear). In winter it snows instead of raining. */
  chance: /** @type {Record<SeasonId, { cloudy: number, rain: number, storm: number, snow: number }>} */ ({
    spring: { cloudy: 0.25, rain: 0.22, storm: 0.05, snow: 0 },
    summer: { cloudy: 0.15, rain: 0.12, storm: 0.13, snow: 0 },
    autumn: { cloudy: 0.3, rain: 0.15, storm: 0.04, snow: 0 },
    winter: { cloudy: 0.3, rain: 0, storm: 0, snow: 0.28 },
  }),
  /** Things stay wet this long after the rain stops. */
  wetAfterMs: 20_000,
  /** Chance per 10 Hz tick that the rain puts out a burning tile. */
  rainDouse: 0.08,
  /** Fire spreads up to (1 + windBias * strength) times as fast downwind. */
  windBias: 1.5,
  /** Gliding drifts with the wind at up to this speed (px/s). */
  glideDrift: 28,
  /** Lightning strikes per second in a storm (near the player). */
  strikesPerSec: 0.12,
  strikeWarnMs: 900,
});

/** @typedef {'clear' | 'cloudy' | 'rain' | 'storm' | 'snow'} WeatherKind */
/** @typedef {{ kind: WeatherKind, windX: number, windY: number, wind: number }} Weather */

/** Hour of the day (0 to 24, fractional). @param {number} worldMs */
export function hourOf(worldMs) {
  return (((worldMs % CLOCK.dayMs) + CLOCK.dayMs) % CLOCK.dayMs) / CLOCK.hourMs;
}

/** "07:30". @param {number} worldMs */
export function clockText(worldMs) {
  const h = hourOf(worldMs);
  const hh = Math.floor(h);
  const mm = Math.floor((h - hh) * 60);
  return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
}

/**
 * The weather at a moment (deterministic). A dry region (P8: the desert) gets the same skies
 * without the rain: rain becomes clear, a storm becomes cloudy.
 * @param {number} seed @param {number} worldMs @param {WeatherKind | null} [override]
 * @param {'temperate' | 'dry'} [climate]
 * @returns {Weather}
 */
export function weatherAt(seed, worldMs, override = null, climate = 'temperate') {
  const slot = Math.floor(worldMs / WEATHER.slotMs);
  /** @type {WeatherKind} */
  let kind = 'clear';
  const r = roll(seed, slot, 0, 11);
  // The season at the start of the slot (P10.2): slots never straddle two seasons' skies.
  const c = WEATHER.chance[seasonAt(slot * WEATHER.slotMs).id];
  if (r < c.storm) kind = 'storm';
  else if (r < c.storm + c.rain) kind = 'rain';
  else if (r < c.storm + c.rain + c.snow) kind = 'snow';
  else if (r < c.storm + c.rain + c.snow + c.cloudy) kind = 'cloudy';
  if (worldMs < WEATHER.clearUntilMs) kind = 'clear';
  if (override) kind = override;
  // The wind belongs to the sky (the same everywhere); a dry region only loses the rain.
  const angle = roll(seed, slot, 1, 11) * Math.PI * 2;
  const base = { clear: 0.2, cloudy: 0.4, rain: 0.6, storm: 0.9, snow: 0.35 }[kind];
  const wind = Math.min(1, base + roll(seed, slot, 2, 11) * 0.2);
  if (climate === 'dry' && kind === 'rain') kind = 'clear';
  if (climate === 'dry' && kind === 'storm') kind = 'cloudy';
  if (climate === 'dry' && kind === 'snow') kind = 'clear'; // P10.2: no snow in the desert either
  return { kind, windX: Math.cos(angle) * wind, windY: Math.sin(angle) * wind, wind };
}

/** Rain on screen and slippery cliffs (not snow). @param {Weather} w */
export const isRaining = (w) => w.kind === 'rain' || w.kind === 'storm';

/** Wet from the sky: rain, a storm, or snow (P10.2: snow puts fires out too). @param {Weather} w */
export const isWet = (w) => isRaining(w) || w.kind === 'snow';

/**
 * Wet from rain at t: raining now or within the last WEATHER.wetAfterMs.
 * @param {number} seed @param {number} t @param {WeatherKind | null} [override]
 */
export function rainWetAt(seed, t, override = null, climate = /** @type {'temperate' | 'dry'} */ ('temperate')) {
  return isWet(weatherAt(seed, t, override, climate)) || isWet(weatherAt(seed, t - WEATHER.wetAfterMs, override, climate));
}

/**
 * Ambient light color for the time and weather (multiplied over the scene).
 * @param {number} worldMs @param {WeatherKind} kind
 * @returns {{ r: number, g: number, b: number }} 0..1
 */
export function ambientAt(worldMs, kind) {
  const h = hourOf(worldMs);
  // Keyframes: night, dawn, day, dusk.
  const keys = [
    [0, [0.22, 0.26, 0.45]],
    [4.5, [0.22, 0.26, 0.45]],
    [6, [0.95, 0.75, 0.6]],
    [7.5, [1, 1, 1]],
    [17, [1, 1, 1]],
    [18.5, [1, 0.72, 0.5]],
    [20, [0.22, 0.26, 0.45]],
    [24, [0.22, 0.26, 0.45]],
  ];
  let a = keys[0];
  let b = keys[1];
  for (let k = 0; k < keys.length - 1; k++) {
    if (h >= /** @type {number} */ (keys[k][0]) && h <= /** @type {number} */ (keys[k + 1][0])) {
      a = keys[k];
      b = keys[k + 1];
      break;
    }
  }
  const span = /** @type {number} */ (b[0]) - /** @type {number} */ (a[0]);
  const f = span > 0 ? (h - /** @type {number} */ (a[0])) / span : 0;
  const ca = /** @type {number[]} */ (a[1]);
  const cb = /** @type {number[]} */ (b[1]);
  const dim = { clear: 1, cloudy: 0.85, rain: 0.7, storm: 0.55, snow: 0.88 }[kind];
  const mix = (/** @type {number} */ i) => (ca[i] + (cb[i] - ca[i]) * f) * dim;
  return { r: mix(0), g: mix(1), b: mix(2) };
}

/** Whether lights (fires, lanterns) are worth drawing: dark enough. @param {{ r: number, g: number, b: number }} c */
export const isDark = (c) => c.r + c.g + c.b < 2.4;
