// @ts-check
// v1.0: what an enemy (or a core of the murk) looks like this frame — which sprite, and the attack
// warning flash. Pure (no Pixi), unit-tested.
//
// Frames: an enemy with release art (src/art-release/enemy/, enemy.<kind>.<action>.<n>, the action
// names of docs/art-release/enemy/frames.json on the art branch) shows the frame for what it is
// doing; one without keeps the placeholder enemy.<kind>.<0|1> (standing / moving). A missing action
// falls back to idle, so the art can arrive a little at a time. The release art has 2 art pixels per
// game pixel (art density 2): its atlas is built at that resolution (placeholderPack.js ART_SCALE),
// so its textures already measure in game pixels and the sprite keeps scale ±1 (−1 = facing left;
// the art faces right, and a core's front-facing art is mirrored the same way on a charge).
//
// Warning flash (docs/art-direction/ART_STYLE_GUIDE.md 5.4 B, approved for v1.0): during a wind-up
// the sprite's shape is covered with red #ff3a3a at 50%, pulsing faster as the attack nears. It is
// laid OVER the art rather than multiplied into it, so it shows on dark bodies too.
import { BOSS_PARRY_STUN_MS, BOSS_KINDS } from '../game/entities/bosses.js';
import { ENEMY_KINDS } from '../game/entities/enemies.js';
import { ENEMY_CORPSE_MS } from '../game/state.js';
import { actionInfo, loopFrame, onceFrame, spreadFrame } from './enemyFrames.js';

// gfx W3: frame counts and speeds per action come from the art's frames.json (enemyFrames.js) —
// v1 (2–4 frames) or v2 (4–8) — so nothing here assumes how many frames an action has.

/** Spans the game gives some actions (the frame count and speed of every action: enemyFrames.js). */
export const ENEMY_ANIM = Object.freeze({
  /** a defeated enemy is removed ENEMY_CORPSE_MS after it falls: its defeat frames play over this
   *  first part of that time (then the last frame stays and fades out) */
  defeatPlayMs: ENEMY_CORPSE_MS * 0.6,
  /** it starts to fade at this point */
  fadeFromMs: ENEMY_CORPSE_MS * 0.6,
  /** the archer's shot pose lasts this long after the orb leaves */
  shotPoseMs: 240,
  /** placeholder (enemy.<kind>.<0|1>, standing / moving): moving alternates at this rate */
  placeholderFps: 6,
});

/** How long the attack itself lasts before its recovery (so the attack frames run on through it). @param {any} e */
export function attackMs(e) {
  if (e.boss) {
    const k = /** @type {any} */ (BOSS_KINDS)[e.bossKind];
    return e.pattern === 'charge' ? (k?.chargeMs ?? 0) : e.pattern === 'slam' ? 200 : 0;
  }
  return /** @type {any} */ (ENEMY_KINDS)[e.kind]?.activeMs ?? 0;
}

/** The wind-up warning: colour and strength of the overlay. */
export const WARNING_FLASH = Object.freeze({ color: 0xff3a3a, alpha: 0.5 });

/**
 * How many frames an action has (0 when there is none). With `counts`, each answer is remembered
 * (the caller clears it when the loaded art changes), so nothing is recounted every frame.
 * @param {string} base @param {(key: string) => boolean} has @param {Map<string, { n: number, fps: number }>} [counts]
 */
export function frameCount(base, has, counts) {
  return actionInfo(base, has, counts).n;
}

/** How opaque a defeated enemy is, `ms` after it fell: solid while its defeat frames play, then fading out. @param {number} ms */
export function defeatAlpha(ms) {
  return Math.max(0, Math.min(1, 1 - (ms - ENEMY_ANIM.fadeFromMs) / (ENEMY_CORPSE_MS - ENEMY_ANIM.fadeFromMs)));
}

/**
 * The release action for an enemy's state, and how far into it (ms), or null to stand idle.
 * @param {any} e @param {boolean} moving
 * @returns {{ action: string, ms: number, loop: boolean } | { action: string, progress: number }}
 */
export function enemyAction(e, moving) {
  const suffix = e.boss && e.pattern ? `_${e.pattern}` : '';
  switch (e.state) {
    case 'dead':
      return { action: 'defeat', ms: e.t, loop: false };
    case 'windup': {
      const total = e.boss ? e.windupMs : /** @type {any} */ (ENEMY_KINDS)[e.kind]?.windupMs ?? 1;
      return { action: `windup${suffix}`, progress: Math.min(0.999, e.t / total) };
    }
    case 'attack':
      return { action: `attack${suffix}`, ms: e.t, loop: false };
    case 'recover':
      // The attack runs on through the recovery (a long swing finishes), then holds its last frame.
      return { action: `attack${suffix}`, ms: attackMs(e) + e.t, loop: false };
    case 'stun':
      // A core knocked off balance by a parry staggers; any other stun is a flinch.
      if (e.boss && e.stunMs >= BOSS_PARRY_STUN_MS) return { action: 'stagger', ms: e.t, loop: true };
      return { action: 'hurt', ms: e.t, loop: false };
  }
  // The archer holds its shot pose for a moment after the orb leaves (by its own clock, so the pose
  // ends even if it loses sight of the player at once).
  if (!e.boss && e.sinceShotMs < ENEMY_ANIM.shotPoseMs) return { action: 'attack', ms: e.sinceShotMs, loop: false };
  if (moving) return { action: 'move', ms: -1, loop: true };
  return { action: e.boss && e.phase === 2 ? 'idle2' : 'idle', ms: -1, loop: true };
}


/**
 * The sprite key for an enemy this frame.
 * @param {any} e the enemy (or boss) from the game state
 * @param {number} timeSec real time (looping animations)
 * @param {boolean} moving whether it moved this step
 * @param {(key: string) => boolean} has whether a texture is loaded
 * @param {Map<string, { n: number, fps: number }>} [counts] remembered frame counts and speeds (enemyFrames.js actionInfo)
 * @returns {string}
 */
export function enemyFrameKey(e, timeSec, moving, has, counts) {
  const base = `enemy.${e.kind}`;
  if (actionInfo(`${base}.idle`, has, counts).n > 0) {
    const a = enemyAction(e, moving);
    let name = a.action;
    let info = actionInfo(`${base}.${name}`, has, counts);
    if (info.n === 0 && name === 'idle2') {
      name = 'idle';
      info = actionInfo(`${base}.idle`, has, counts);
    }
    if (info.n > 0) {
      if ('progress' in a) return `${base}.${name}.${spreadFrame(a.progress, info.n)}`;
      // Looping by real time; each enemy at its own offset so a group does not move in step.
      if (a.ms < 0) return `${base}.${name}.${loopFrame(timeSec, info, (e.id % 7) * 0.37)}`;
      // The defeat frames are spread over the time before the body is removed.
      if (name === 'defeat') return `${base}.${name}.${spreadFrame(a.ms / ENEMY_ANIM.defeatPlayMs, info.n)}`;
      if (a.loop) return `${base}.${name}.${loopFrame(a.ms / 1000, info)}`;
      return `${base}.${name}.${onceFrame(a.ms, info)}`;
    }
    return `${base}.idle.0`;
  }
  // Placeholder (or the minimal release set under the same names).
  return `${base}.${moving ? Math.floor(timeSec * ENEMY_ANIM.placeholderFps) % 2 : 0}`;
}

/**
 * The wind-up warning overlay's strength right now: WARNING_FLASH.alpha while the pulse is on, else
 * 0. Same timing as before v1.0 (it pulses faster as the attack nears).
 * @param {any} e @param {number} timeSec @param {number} progress 0..1 into the wind-up (windupProgress)
 */
export function warningFlashAlpha(e, timeSec, progress) {
  if (e.state !== 'windup') return 0;
  return Math.sin(timeSec * (12 + 24 * progress)) > 0 ? WARNING_FLASH.alpha : 0;
}
