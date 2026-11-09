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
import { BOSS_PARRY_STUN_MS } from '../game/entities/bosses.js';
import { ENEMY_KINDS } from '../game/entities/enemies.js';

/** Frame timings (docs/art-release/enemy/PRODUCTION.md 2.3). */
export const ENEMY_ANIM = Object.freeze({
  idleMs: 400,
  moveMs: 140,
  attackMs: 120,
  hurtMs: 200,
  defeatMs: 260,
  /** the archer's shot pose lasts this long after the orb leaves */
  shotPoseMs: 240,
  /** placeholder: 2 frames at this rate while moving */
  placeholderFps: 6,
});

/** The wind-up warning: colour and strength of the overlay. */
export const WARNING_FLASH = Object.freeze({ color: 0xff3a3a, alpha: 0.5 });

/** How many frames an action has (0 when there is none). @param {string} base @param {(key: string) => boolean} has */
export function frameCount(base, has) {
  let n = 0;
  while (n < 16 && has(`${base}.${n}`)) n++;
  return n;
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
      // The follow-through pose (the attack's last frame) while it recovers.
      return { action: `attack${suffix}`, ms: Infinity, loop: false };
    case 'stun':
      // A core knocked off balance by a parry staggers; any other stun is a flinch.
      if (e.boss && e.stunMs >= BOSS_PARRY_STUN_MS) return { action: 'stagger', ms: e.t, loop: true };
      return { action: 'hurt', ms: e.t, loop: false };
  }
  const k = /** @type {any} */ (ENEMY_KINDS)[e.kind];
  if (k?.attack === 'shoot' && k.cooldownMs - e.cooldownMs < ENEMY_ANIM.shotPoseMs && e.cooldownMs > 0) {
    return { action: 'attack', ms: k.cooldownMs - e.cooldownMs, loop: false };
  }
  if (moving) return { action: 'move', ms: -1, loop: true };
  return { action: e.boss && e.phase === 2 ? 'idle2' : 'idle', ms: -1, loop: true };
}

const PER_FRAME = /** @type {Record<string, number>} */ ({ defeat: ENEMY_ANIM.defeatMs, hurt: ENEMY_ANIM.hurtMs, stagger: ENEMY_ANIM.hurtMs });

/**
 * The sprite key for an enemy this frame.
 * @param {any} e the enemy (or boss) from the game state
 * @param {number} timeSec real time (looping animations)
 * @param {boolean} moving whether it moved this step
 * @param {(key: string) => boolean} has whether a texture is loaded
 * @returns {string}
 */
export function enemyFrameKey(e, timeSec, moving, has) {
  const base = `enemy.${e.kind}`;
  if (has(`${base}.idle.0`)) {
    const a = enemyAction(e, moving);
    let name = a.action;
    let n = frameCount(`${base}.${name}`, has);
    if (n === 0 && name === 'idle2') {
      name = 'idle';
      n = frameCount(`${base}.idle`, has);
    }
    if (n > 0) {
      if ('progress' in a) return `${base}.${name}.${Math.min(n - 1, Math.floor(a.progress * n))}`;
      if (a.ms < 0) {
        // Looping by real time; each enemy at its own offset so a group does not move in step.
        const per = name === 'move' ? ENEMY_ANIM.moveMs : ENEMY_ANIM.idleMs;
        return `${base}.${name}.${Math.floor((timeSec * 1000) / per + (e.id % 7) * 0.37) % n}`;
      }
      const per = PER_FRAME[name] ?? ENEMY_ANIM.attackMs;
      const f = Math.floor(a.ms / per);
      return `${base}.${name}.${a.loop ? f % n : Math.min(n - 1, f)}`;
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
