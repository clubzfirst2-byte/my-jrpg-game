// @ts-check
// v1.0 beginning and end (docs/story/V1_STORY_PROPOSAL.md C9 minimal, C10). Pure logic: the view
// draws the opening from `state.opening`, main.js shows the ending screen while `state.ending` is
// 'screen' and calls finishEnding when it is over.
//
// Opening (C9, minimal): a new game only (「はじめから」); the controls stop, the small 星環 on the
// beach flashes once, the hero gets up (his collapse played backwards), the pendant glows — about
// 2.6 s, the camera does not move, a tap skips it. Then the flag `opening_seen`: never again, and a
// save from before v1.0 (continued, never started anew) never sees it.
//
// Ending (C10): 2 s after the source is purified (finalBoss.js pushes `sourcePurified`), the
// princess by the ring (princess_end) speaks the dialogue `ending` by herself. When that dialogue
// is over (its choice made, however it was started), the ending screen is shown; after it the
// record stone becomes the plains', the hero wakes in front of the inn of 風見の村 at 6:00, the flag
// `ending_seen` is set and the game saved. Closed during the screen? The screen comes back on the
// next step (the choice is saved, `ending_seen` is not).
import { startDialogue } from '../npc/talk.js';
import { sleepUntil } from '../world/interiors.js';
import { tileFeet } from '../world/features.js';

export const OPENING = Object.freeze({
  /** The beach ring flashes from 0 to here (ms). */
  flashEndMs: 700,
  /** The hero gets up between these (ms): his collapse frames backwards. */
  riseStartMs: 700,
  riseEndMs: 1500,
  /** The pendant glows from here to the end. */
  glowStartMs: 1300,
  totalMs: 2600,
  flag: 'opening_seen',
});

export const ENDING = Object.freeze({
  /** After the source is purified, the ending dialogue starts by itself this much later. */
  delayTicks: 120, // 2 s at 60 Hz
  dialogue: 'ending',
  princess: 'princess_end',
  /** Where the hero wakes: in front of the inn (one tile south of its doorway), facing the village. */
  innDoor: 'inn-in',
  checkpoint: 'plains',
  hour: 6,
  flag: 'ending_seen',
  /** How long the ending screen plays unless skipped (ms; the UI's timing). */
  screenMs: 30_000,
});

// ---- opening ----

/** A new game begins with the opening (unless it was already seen). @param {any} state */
export function startOpening(state) {
  if (state.progress.flags[OPENING.flag]) return;
  state.opening = { ms: 0 };
}

/** Ends the opening now (a tap, or its time is up): never again. @param {any} state */
export function skipOpening(state) {
  if (!state.opening) return;
  state.opening = null;
  state.progress.flags[OPENING.flag] = true;
  state.events.push({ type: 'openingDone', tick: state.tick });
  state.saveRequested = true;
}

/**
 * One logic step of the opening. Returns true while it plays (the world and the controls wait).
 * @param {any} state @param {number} dtMs
 */
export function stepOpening(state, dtMs) {
  if (!state.opening) return false;
  state.opening.ms += dtMs;
  if (state.opening.ms >= OPENING.totalMs) skipOpening(state);
  return true;
}

/**
 * What the opening shows now (null when there is none): the ring's flash, the hero's frame of
 * getting up (3 lying … 0 standing; his collapse backwards), the pendant's glow (0..1).
 * @param {any} state @returns {{ flash: boolean, riseFrame: number, glow: number } | null}
 */
export function openingView(state) {
  const o = state.opening;
  if (!o) return null;
  const t = o.ms;
  const rise = Math.max(0, Math.min(1, (t - OPENING.riseStartMs) / (OPENING.riseEndMs - OPENING.riseStartMs)));
  const g = Math.max(0, Math.min(1, (t - OPENING.glowStartMs) / (OPENING.totalMs - OPENING.glowStartMs)));
  return {
    flash: t < OPENING.flashEndMs && Math.floor(t / 120) % 2 === 0,
    riseFrame: 3 - Math.min(3, Math.floor(rise * 4)),
    glow: Math.sin(g * Math.PI), // swells and fades
  };
}

// ---- ending ----

/** The ending dialogue's choice has been made (the regalia joined or kept). @param {any} state */
export function endingChosen(state) {
  const f = state.progress.flags;
  return !!(f.regalia_joined || f.regalia_kept);
}

/**
 * One logic step of the ending (after everything else in stepGame): counts down from the source's
 * purification to the princess's words, and shows the ending screen once her dialogue is over.
 * @param {any} state
 */
export function stepEnding(state) {
  const flags = state.progress.flags;
  if (flags[ENDING.flag]) return;
  if (state.events.some((/** @type {any} */ e) => e.type === 'sourcePurified' && e.tick === state.tick)) {
    state.endingAt = state.tick + ENDING.delayTicks;
  }
  if (state.ending === 'screen') return;
  if (endingChosen(state) && !state.dialogue) {
    state.ending = 'screen';
    state.endingAt = null;
    state.events.push({ type: 'endingScreen', tick: state.tick });
    return;
  }
  if (state.endingAt != null && state.tick >= state.endingAt && !state.dialogue && !state.player.dead) {
    state.endingAt = null;
    startDialogue(state, ENDING.dialogue, ENDING.princess);
  }
}

/**
 * The ending screen is over (watched or skipped): to the village in front of the inn at 6:00, the
 * plains' record stone, `ending_seen`, saved. @param {any} state
 */
export function finishEnding(state) {
  if (state.progress.flags[ENDING.flag]) return;
  const pr = state.progress;
  if (!pr.checkpoints.includes(ENDING.checkpoint)) pr.checkpoints.push(ENDING.checkpoint);
  pr.checkpoint = ENDING.checkpoint;
  const door = state.warps.find((/** @type {any} */ w) => w.id === ENDING.innDoor);
  const p = state.player;
  const f = tileFeet(state.map, door.tx, door.ty + 1);
  p.x = p.prevX = f.x;
  p.y = p.prevY = f.y;
  p.z = p.prevZ = p.groundZ = state.map.elev[(door.ty + 1) * state.map.width + door.tx];
  p.vx = p.vy = p.vz = 0;
  p.facing = 'down';
  p.aimX = 0;
  p.aimY = 1;
  p.action = 'none';
  state.projectiles = [];
  pr.flags[ENDING.flag] = true;
  sleepUntil(state, ENDING.hour); // the morning (the world catches up as after a night at the inn); full hearts
  state.ending = null;
  state.endingAt = null;
  state.dialogue = null;
  state.events.push({ type: 'warp', tick: state.tick, id: 'ending' });
  state.events.push({ type: 'endingDone', tick: state.tick });
  state.saveRequested = true;
}

/** The closing line of the ending screen, after the princess's choice. @param {any} state */
export function endingLine(state) {
  const f = state.progress.flags;
  if (f.regalia_joined) return '二つの石の光は輪に還り、星環はひとりでに回りはじめた。';
  if (f.regalia_kept) return '二つの石は、いまも二人の胸で静かに光っている。';
  return '';
}
