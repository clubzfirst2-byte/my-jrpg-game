// @ts-check
// v1.0 (C7): how 淀みの源 is drawn — which frame of its art (enemy.boss_source.<action>.<frame>,
// the release art's names) for its state, and its telegraphs: the reach of the slam / inversion wave
// on the ground, and a light over each seat (座) it counts awake. Reads state only.
import { FINAL_BOSS } from '../game/entities/finalBoss.js';
import { windupProgress } from '../game/entities/enemies.js';

/** The art's slot for each attack (the wave uses the 4th attack's frames, `charge`). */
const ACTION = { volley: 'volley', ring: 'ring', slam: 'slam', wave: 'charge' };
const SEAT_COLOR = { 'source-fire': 0xff8a3c, 'source-light': 0xffe27a, 'source-weight': 0xc4beb0, 'source-echo': 0x7fe8ff };

/**
 * Which frame, by the story's rule 「座を目覚めさせると、輪の目が開いて攻撃が通る」 (QA B-2):
 * - inverted, at rest (idle / recover, also asleep): the EYE CLOSED — `hurt.0` (the art's only
 *   closed-eye pose besides the transform / defeat frames);
 * - winding up: the eye a narrow slit (`windup_*`); the attack itself: the eye flashes (`attack_*`,
 *   a fraction of a second);
 * - staggered (the ring turned back, it can be hurt): the EYE WIDE OPEN — `idle` / `idle2` (phase 2,
 *   cracked), the art's open-eye frames, animated;
 * - phase change: `transform`; purified: `defeat`.
 * @param {any} e the source @param {number} timeSec @param {(key: string) => boolean} has
 * @returns {string}
 */
export function sourceFrameKey(e, timeSec, has) {
  const k = (/** @type {string} */ action, /** @type {number} */ f) => `enemy.boss_source.${action}.${f}`;
  const open = k(e.phase === 2 ? 'idle2' : 'idle', Math.floor(timeSec * 3) % 2);
  const closed = k('hurt', 0);
  /** @type {string} */
  let key;
  if (e.state === 'dead') key = k('defeat', Math.min(5, Math.floor(e.t / (FINAL_BOSS.defeatMs / 6))));
  else if (e.state === 'stagger') key = open;
  else if (e.transformUntil > e.clock) key = k('transform', Math.min(3, Math.floor((e.clock - e.transformFrom) / 250)));
  else if (e.state === 'windup' && e.pattern) key = k(`windup_${ACTION[/** @type {'volley'} */ (e.pattern)]}`, Math.floor(timeSec * 4) % 2);
  else if (e.state === 'attack' && e.pattern) key = k(`attack_${ACTION[/** @type {'volley'} */ (e.pattern)]}`, Math.floor(e.t / 120) % 2);
  else key = closed;
  return has(key) ? key : has(closed) ? closed : k('idle', 0);
}

/**
 * The reach of a coming slam / inversion wave, on the ground. `g` is cleared by the caller.
 * @param {import('pixi.js').Graphics} g @param {any} state
 */
export function drawSourceTelegraphs(g, state) {
  const e = state.enemies.find((/** @type {any} */ x) => x.final && x.state !== 'dead');
  if (!e) return;
  if (e.state === 'windup' && (e.pattern === 'slam' || e.pattern === 'wave')) {
    const k = windupProgress(e);
    const r = e.pattern === 'slam' ? FINAL_BOSS.slamRadius : FINAL_BOSS.waveRadius;
    const color = e.pattern === 'slam' ? 0xd0202a : 0xb040b0; // the wave: the murk's glow
    g.circle(Math.round(e.x), Math.round(e.y - e.z), r).stroke({ width: 2, color, alpha: 0.6 + 0.4 * k });
    g.circle(Math.round(e.x), Math.round(e.y - e.z), r * k).fill({ color, alpha: 0.18 });
  }
}

/**
 * A light over each seat the source counts awake. `g` is cleared by the caller.
 * @param {import('pixi.js').Graphics} g @param {any} state @param {number} timeSec
 */
export function drawSeatLights(g, state, timeSec) {
  const e = state.enemies.find((/** @type {any} */ x) => x.final && x.state !== 'dead');
  if (!e || !e.awake) return;
  const ts = state.map.tileSize;
  for (const s of state.switches) {
    if (!s.seat || !e.seats[s.id]) continue;
    const x = s.tx * ts + ts / 2;
    const y = s.ty * ts - 6 - state.map.elev[s.ty * state.map.width + s.tx] + Math.sin(timeSec * 4) * 1.5;
    g.circle(x, y, 3).fill({ color: SEAT_COLOR[/** @type {'source-fire'} */ (s.id)] ?? 0xffffff, alpha: 0.9 });
    g.circle(x, y, 5).stroke({ width: 1, color: 0xffffff, alpha: 0.5 });
  }
}
