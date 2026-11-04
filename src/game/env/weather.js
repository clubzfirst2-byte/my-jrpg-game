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

export const WEATHER = Object.freeze({
  /** Weather changes every 3 game hours. */
  slotMs: 3 * CLOCK.hourMs,
  /** The first morning of a new game is always clear (until noon). */
  clearUntilMs: 12 * CLOCK.hourMs,
  /** Chances of each kind (the rest is clear). */
  chance: { cloudy: 0.25, rain: 0.17, storm: 0.08 },
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

/** @typedef {'clear' | 'cloudy' | 'rain' | 'storm'} WeatherKind */
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
 * The weather at a moment (deterministic).
 * @param {number} seed @param {number} worldMs @param {WeatherKind | null} [override]
 * @returns {Weather}
 */
export function weatherAt(seed, worldMs, override = null) {
  const slot = Math.floor(worldMs / WEATHER.slotMs);
  /** @type {WeatherKind} */
  let kind = 'clear';
  const r = roll(seed, slot, 0, 11);
  const c = WEATHER.chance;
  if (r < c.storm) kind = 'storm';
  else if (r < c.storm + c.rain) kind = 'rain';
  else if (r < c.storm + c.rain + c.cloudy) kind = 'cloudy';
  if (worldMs < WEATHER.clearUntilMs) kind = 'clear';
  if (override) kind = override;
  const angle = roll(seed, slot, 1, 11) * Math.PI * 2;
  const base = { clear: 0.2, cloudy: 0.4, rain: 0.6, storm: 0.9 }[kind];
  const wind = Math.min(1, base + roll(seed, slot, 2, 11) * 0.2);
  return { kind, windX: Math.cos(angle) * wind, windY: Math.sin(angle) * wind, wind };
}

/** @param {Weather} w */
export const isRaining = (w) => w.kind === 'rain' || w.kind === 'storm';

/**
 * Wet from rain at t: raining now or within the last WEATHER.wetAfterMs.
 * @param {number} seed @param {number} t @param {WeatherKind | null} [override]
 */
export function rainWetAt(seed, t, override = null) {
  return isRaining(weatherAt(seed, t, override)) || isRaining(weatherAt(seed, t - WEATHER.wetAfterMs, override));
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
  const dim = { clear: 1, cloudy: 0.85, rain: 0.7, storm: 0.55 }[kind];
  const mix = (/** @type {number} */ i) => (ca[i] + (cb[i] - ca[i]) * f) * dim;
  return { r: mix(0), g: mix(1), b: mix(2) };
}

/** Whether lights (fires, lanterns) are worth drawing: dark enough. @param {{ r: number, g: number, b: number }} c */
export const isDark = (c) => c.r + c.g + c.b < 2.4;
