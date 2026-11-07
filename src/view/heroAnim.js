// @ts-check
// The hero's animation: which action and which frame to draw, from the player's state.
// Release art (docs/hero/HERO_ANIMATION_SPEC.md) is named hero.<action>.<down|up|right|left>.<frame>;
// an action whose frames are not drawn yet falls back (see HeroAnimator.textureKey), so the game
// always has a picture. Pure logic (no PixiJS): unit-tested.

import { COMBAT, SWORD } from '../game/entities/playerCombat.js';

/**
 * Every action the hero has, its frame count (per direction) and timing.
 * fps: frames per second for looping actions; `by` says what drives the frame:
 *   time  — the clock (idle breathing, gliding)
 *   walk  — the distance walked (walk, run, climb, swim): feet never slide
 *   once  — plays once over the action's own duration (attacks, dodge, bow, land, collapse)
 * @type {Record<string, { frames: number, fps?: number, by: 'time' | 'walk' | 'once', loop: boolean }>}
 */
export const HERO_ANIMS = Object.freeze({
  idle: { frames: 4, fps: 4, by: 'time', loop: true },
  walk: { frames: 6, fps: 10, by: 'walk', loop: true },
  run: { frames: 6, fps: 9, by: 'walk', loop: true }, // walkTime runs 1.6× while dashing: ~14 frames/s
  jump: { frames: 2, by: 'once', loop: false }, // 0 rising, 1 falling
  land: { frames: 2, by: 'once', loop: false },
  glide: { frames: 4, fps: 6, by: 'time', loop: true },
  climb: { frames: 4, fps: 8, by: 'walk', loop: true },
  swim: { frames: 4, fps: 6, by: 'walk', loop: true },
  dodge: { frames: 4, by: 'once', loop: false },
  attack1: { frames: 4, by: 'once', loop: false },
  attack2: { frames: 4, by: 'once', loop: false },
  attack3: { frames: 6, by: 'once', loop: false },
  bow: { frames: 4, by: 'once', loop: false }, // 0-2 drawing, 3 drawn and aiming
  guard: { frames: 2, by: 'once', loop: false }, // 0 raising the shield, 1 holding
  hurt: { frames: 2, by: 'once', loop: false },
  down: { frames: 4, by: 'once', loop: false }, // collapsing
});

/** How long a landing shows (ms). */
export const LAND_MS = 140;
const DOWN_FRAME_MS = 140;

/**
 * @typedef {{ action: string, frame: number }} HeroPose
 */

/** Frame `i` of `n` for a progress of t in [0, 1). @param {number} t @param {number} n */
const part = (t, n) => Math.max(0, Math.min(n - 1, Math.floor(t * n)));

export class HeroAnimator {
  constructor() {
    this.wasGrounded = true;
    /** Logic time (ms) since the last landing. */
    this.sinceLandMs = Infinity;
  }

  /**
   * @param {any} p the player
   * @param {{ deathMs?: number }} state
   * @param {number} timeSec real time (for idle and gliding loops)
   * @param {number} dtMs time since the previous call
   * @returns {HeroPose}
   */
  update(p, state, timeSec, dtMs) {
    const landed = p.grounded && !this.wasGrounded && !p.swimming && !p.climbing;
    this.wasGrounded = p.grounded;
    this.sinceLandMs = landed ? 0 : this.sinceLandMs + dtMs;
    return poseOf(p, state, timeSec, this.sinceLandMs);
  }

  /**
   * The texture to draw for a pose, falling back while an action has no release art:
   * the action's own frame → standing / walking release art → `null` (the caller then uses the
   * placeholder hero).
   * @param {HeroPose} pose @param {string} dir @param {boolean} moving
   * @param {(key: string) => boolean} has
   */
  textureKey(pose, dir, moving, has) {
    const own = `hero.${pose.action}.${dir}.${pose.frame}`;
    if (has(own)) return own;
    const base = moving ? `hero.walk.${dir}.0` : `hero.idle.${dir}.0`;
    if (has(base)) return base;
    return null;
  }
}

/**
 * The pose for the player's state (pure).
 * @param {any} p @param {{ deathMs?: number }} state @param {number} timeSec @param {number} sinceLandMs
 * @returns {HeroPose}
 */
export function poseOf(p, state, timeSec, sinceLandMs) {
  if (p.dead || (state.deathMs ?? -1) >= 0) {
    return { action: 'down', frame: Math.min(3, Math.floor(Math.max(0, state.deathMs ?? 0) / DOWN_FRAME_MS)) };
  }
  if (p.swimming) return loop('swim', p, timeSec);
  if (p.climbing) return loop('climb', p, timeSec);
  if (p.gliding) return loop('glide', p, timeSec);
  if ((p.knockMs ?? 0) > 0) {
    return { action: 'hurt', frame: part(1 - p.knockMs / COMBAT.knockbackMs, HERO_ANIMS.hurt.frames) };
  }
  if (p.action === 'attack') {
    const sw = SWORD[p.comboIndex ?? 0];
    const name = `attack${(p.comboIndex ?? 0) + 1}`;
    return { action: name, frame: part(p.actionMs / (sw.startupMs + sw.activeMs + sw.recoveryMs), HERO_ANIMS[name].frames) };
  }
  if (p.action === 'dodge') return { action: 'dodge', frame: part(p.actionMs / COMBAT.dodgeMs, HERO_ANIMS.dodge.frames) };
  if (p.action === 'aim') return { action: 'bow', frame: part(Math.min(1, p.actionMs / COMBAT.bowDrawMs) * 0.999, 3) + (p.actionMs >= COMBAT.bowDrawMs ? 1 : 0) };
  if (!p.grounded) return { action: 'jump', frame: p.vz > 0 ? 0 : 1 };
  if (sinceLandMs < LAND_MS) return { action: 'land', frame: part(sinceLandMs / LAND_MS, HERO_ANIMS.land.frames) };
  if (p.guarding) return { action: 'guard', frame: (p.guardMs ?? 0) < 90 ? 0 : 1 };
  if (p.moving) return loop(p.dashing ? 'run' : 'walk', p, timeSec);
  return loop('idle', p, timeSec);
}

/** @param {string} action @param {any} p @param {number} timeSec @returns {HeroPose} */
function loop(action, p, timeSec) {
  const a = HERO_ANIMS[action];
  const fps = /** @type {number} */ (a.fps);
  const t = a.by === 'walk' ? p.walkTime ?? 0 : timeSec;
  // walking actions stand still on frame 0 when not moving (swimming in place keeps paddling slowly)
  if (a.by === 'walk' && !p.moving && action !== 'swim') return { action, frame: 0 };
  const rate = action === 'swim' && !p.moving ? fps / 2 : fps;
  return { action, frame: Math.floor(t * rate) % a.frames };
}
