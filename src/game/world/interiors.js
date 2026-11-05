// @ts-check
// Inside the houses (P10.1): beds to sleep in until morning or evening, and the furniture you can
// use. The rooms themselves are map data (tools/gen_world.py); doors are warps. Pure logic.
import { CLOCK } from '../env/weather.js';
import { skipTime } from '../env/envSim.js';

const BED_RANGE = 22;

/**
 * The bed in front of the player, close enough to lie down in.
 * @param {any} state @returns {{ tx: number, ty: number } | null}
 */
export function bedInReach(state) {
  const p = state.player;
  const map = state.map;
  const ts = map.tileSize;
  for (const [i, o] of state.env.objectAt) {
    if (o.gone || o.type !== 'bed') continue;
    const bx = (i % map.width) * ts + ts / 2;
    const by = Math.floor(i / map.width) * ts + ts / 2;
    const dx = bx - p.x;
    const dy = by - (p.y - 3);
    if (Math.hypot(dx, dy) < BED_RANGE && dx * p.aimX + dy * p.aimY > 0 && Math.abs(map.elev[i] - p.z) < 12) return o;
  }
  return null;
}

/**
 * How long until the clock next shows `hour` (never zero: sleeping always takes some time).
 * @param {number} now world ms @param {number} hour
 */
export function msUntilHour(now, hour) {
  // Exactly on the hour (computed in whole world ms, so the clock then reads hh:00).
  let t = Math.floor(now / CLOCK.dayMs) * CLOCK.dayMs + hour * CLOCK.hourMs;
  while (t - now <= CLOCK.hourMs / 4) t += CLOCK.dayMs;
  return t - now;
}

/**
 * Sleeps until the given hour: time passes, the hearts are full again, and the game is saved.
 * @param {any} state @param {number} hour
 */
export function sleepUntil(state, hour) {
  const ms = msUntilHour(state.env.now, hour);
  skipTime(state.env, ms);
  const p = state.player;
  p.hp = p.maxHp;
  state.events.push({ type: 'slept', tick: state.tick, hour });
  state.saveRequested = true;
  return ms;
}
