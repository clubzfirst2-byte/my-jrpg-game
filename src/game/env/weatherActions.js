// @ts-check
// What the weather does to the player and the world each step (P5): wind on the glider, rising air
// over fires, rain on climbing walls, and lightning in storms. Pure logic.
import { roll } from '../core/hashRandom.js';
import { WEATHER, isRaining } from './weather.js';
import { weatherNow, material } from './envSim.js';
import { conductorsFrom, tileIndexAt } from './envActions.js';
import { hitPlayer, hitEnemy } from '../combat/damage.js';

export const STORM = Object.freeze({
  /** Strikes land 2 to 10 tiles from the player. */
  minTiles: 2,
  maxTiles: 10,
  /** Damage within this distance (px) of the strike, or anywhere in the water / metal it hits. */
  radius: 20,
  playerDamage: 6,
  enemyDamage: 12,
  sparkMs: 500,
});

/**
 * Sets the weather inputs the player physics reads this step.
 * @param {any} state
 */
export function applyWeatherToPlayer(state) {
  const env = state.env;
  const p = state.player;
  const map = state.map;
  const w = weatherNow(env);
  const i = tileIndexAt(state, p.x, p.y);
  const indoor = i >= 0 && env.indoor[i] === 1;
  // Clear days are calm for the glider; from cloudy weather on, the wind carries it.
  const drift = indoor || w.kind === 'clear' ? 0 : WEATHER.glideDrift;
  p.windX = w.windX * drift;
  p.windY = w.windY * drift;
  p.rainOn = !indoor && isRaining(w) && !p.grip; // grip boots (P6) do not slip
  // Rising air over fire: any burning tile in the 3x3 under the player.
  let hot = false;
  if (p.gliding && i >= 0) {
    const tx = i % map.width;
    const ty = (i / map.width) | 0;
    for (let dy = -1; dy <= 1 && !hot; dy++) {
      for (let dx = -1; dx <= 1 && !hot; dx++) {
        const x = tx + dx;
        const y = ty + dy;
        if (x >= 0 && y >= 0 && x < map.width && y < map.height && env.burning.has(y * map.width + x)) hot = true;
      }
    }
  }
  p.updraft = hot;
}

/**
 * Storm lightning: picks a spot near the player, warns, then strikes.
 * @param {any} state @param {number} dtMs
 */
export function stormStep(state, dtMs) {
  const env = state.env;
  const map = state.map;
  const p = state.player;
  if (env.strike && env.now >= env.strike.atMs) {
    strike(state, env.strike.i);
    env.strike = null;
  }
  if (env.strike || p.dead) return;
  const w = weatherNow(env);
  if (w.kind !== 'storm') return;
  const pi = tileIndexAt(state, p.x, p.y);
  if (pi < 0 || env.indoor[pi]) return; // no lightning in the cave
  if (roll(env.seed, state.tick, 0, 21) >= (WEATHER.strikesPerSec * dtMs) / 1000) return;
  const span = STORM.maxTiles - STORM.minTiles;
  const dist = STORM.minTiles + roll(env.seed, state.tick, 1, 21) * span;
  const ang = roll(env.seed, state.tick, 2, 21) * Math.PI * 2;
  const tx = Math.floor(p.x / map.tileSize + Math.cos(ang) * dist);
  const ty = Math.floor(p.y / map.tileSize + Math.sin(ang) * dist);
  if (tx < 0 || ty < 0 || tx >= map.width || ty >= map.height) return;
  const i = ty * map.width + tx;
  if (env.indoor[i]) return;
  env.strike = { i, atMs: env.now + WEATHER.strikeWarnMs };
  state.events.push({ type: 'strikeWarn', tick: state.tick });
}

/**
 * A lightning strike on tile i: hurts who is near, and runs through water and metal.
 * @param {any} state @param {number} i
 */
export function strike(state, i) {
  const env = state.env;
  const map = state.map;
  const ts = map.tileSize;
  const cx = (i % map.width) * ts + ts / 2;
  const cy = ((i / map.width) | 0) * ts + ts / 2;
  const m = material(env, map, i);
  const cells = m === 'water' || m === 'metal' ? [i, ...conductorsFrom(state, i)] : [i];
  const set = new Set(cells);
  env.sparks = { cells, untilMs: env.now + STORM.sparkMs };
  env.version++;
  state.events.push({ type: 'lightning', tick: state.tick, x: cx, y: cy });
  const near = (/** @type {any} */ b) => {
    if (Math.hypot(b.x - cx, b.y - 4 - cy) <= STORM.radius) return true;
    const bi = tileIndexAt(state, b.x, b.y);
    return set.has(bi) && (b.z - map.elev[bi] <= 4 || !!b.swimming);
  };
  const p = state.player;
  if (!p.dead && near(p)) {
    hitPlayer(state, { owner: 'enemy', id: `bolt${state.tick}`, damage: STORM.playerDamage, from: { x: cx, y: cy }, kind: 'env', knock: 0.6, element: 'shock' });
  }
  for (const e of state.enemies) {
    if (e.state !== 'dead' && near(e)) {
      hitEnemy(state, e, { owner: 'player', id: `bolt${state.tick}`, damage: STORM.enemyDamage, from: { x: cx, y: cy }, kind: 'projectile', knock: 0.6 });
    }
  }
}
