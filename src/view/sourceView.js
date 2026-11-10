// @ts-check
// v1.0 (C7): how 淀みの源 is drawn — which frame of its art (enemy.boss_source.<action>.<frame>,
// the release art's names) for its state, and its telegraphs: the reach of the slam / inversion wave
// on the ground, and a light over each seat (座) it counts awake. Reads state only.
import { FINAL_BOSS } from '../game/entities/finalBoss.js';
import { windupProgress } from '../game/entities/enemies.js';
import { actionInfo, loopFrame, onceFrame, spreadFrame } from './enemyFrames.js';

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
 * Frame counts and speeds come from the art's frames.json (enemyFrames.js): any number of frames.
 * @param {any} e the source @param {number} timeSec @param {(key: string) => boolean} has
 * @param {Map<string, { n: number, fps: number }>} [cache] remembered counts (cleared by the caller when the art changes)
 * @returns {string}
 */
export function sourceFrameKey(e, timeSec, has, cache) {
  const B = 'enemy.boss_source';
  const info = (/** @type {string} */ action) => actionInfo(`${B}.${action}`, has, cache);
  const k = (/** @type {string} */ action, /** @type {number} */ f) => `${B}.${action}.${f}`;
  const openAction = e.phase === 2 && info('idle2').n > 0 ? 'idle2' : 'idle';
  const open = info(openAction).n > 0 ? k(openAction, loopFrame(timeSec, info(openAction))) : k('idle', 0);
  const closed = k('hurt', 0);
  const of = (/** @type {string} */ action, /** @type {(n: { n: number, fps: number }) => number} */ pick) => {
    const a = info(action);
    return a.n > 0 ? k(action, pick(a)) : closed;
  };
  /** @type {string} */
  let key;
  if (e.state === 'dead') key = of('defeat', (a) => spreadFrame(e.t / FINAL_BOSS.defeatMs, a.n));
  else if (e.state === 'stagger') key = open;
  else if (e.transformUntil > e.clock) key = of('transform', (a) => spreadFrame((e.clock - e.transformFrom) / Math.max(1, e.transformUntil - e.transformFrom), a.n));
  else if (e.state === 'windup' && e.pattern) key = of(`windup_${ACTION[/** @type {'volley'} */ (e.pattern)]}`, (a) => spreadFrame(e.t / (e.windupMs || FINAL_BOSS.windupMs), a.n));
  else if (e.state === 'attack' && e.pattern) key = of(`attack_${ACTION[/** @type {'volley'} */ (e.pattern)]}`, (a) => onceFrame(e.t, a));
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
  if (e.pattern !== 'slam' && e.pattern !== 'wave') return;
  const r = e.pattern === 'slam' ? FINAL_BOSS.slamRadius : FINAL_BOSS.waveRadius;
  // v1.0 final: brighter colours (the wave's purple was close to the murk on the stone floor) on a
  // dark under-line, so the edge reads on the light stone and in the dark alike (the ring is also lit:
  // weatherView.js warningLights).
  const color = e.pattern === 'slam' ? 0xff3040 : 0xe060ff; // the wave: the murk's glow
  const x = Math.round(e.x);
  const y = Math.round(e.y - e.z);
  if (e.state === 'windup') {
    const k = windupProgress(e);
    g.circle(x, y, r * k).fill({ color, alpha: 0.22 });
    g.circle(x, y, r).stroke({ width: 4, color: 0x12060e, alpha: 0.45 });
    g.circle(x, y, r).stroke({ width: 2, color, alpha: 0.7 + 0.3 * k });
  } else if (e.state === 'attack') {
    // The shockwave going out (it hurts now; jumping clears it).
    g.circle(x, y, r).fill({ color, alpha: 0.3 });
    g.circle(x, y, r).stroke({ width: 3, color: 0xffffff, alpha: 0.9 });
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
