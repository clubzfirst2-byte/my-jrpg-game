// @ts-check
// v1.0 story notices (docs/story/V1_STORY_PROPOSAL.md C8): short messages that point the player
// back to the princess's 写し身 when the story would otherwise give no hint. Pure: main.js shows
// the text.
import { coresPurified, questState } from './talk.js';

/** Saves started with the v1.0 story carry this flag; a save without it is from before v1.0. */
export const STORY_FLAG = 'story_v1';

export const NOTICE = Object.freeze({
  /** After the fourth core, while 「星環の呼び声」 is not reported. */
  allCores: '記録石のそばで、姫の写し身が待っている…',
  /** Loading a save from before v1.0 whose player never met the princess. */
  oldSave: '浜の記録石のあたりに、青い光が見える…',
});

/** A new game: mark its save as one of the v1.0 story. @param {any} state */
export function markNewGame(state) {
  state.progress.flags[STORY_FLAG] = true;
}

/**
 * After a save is loaded. A save from before v1.0 (no story flag) is marked, so this happens once;
 * if its player never met the princess (whatever the number of cores), the notice to show.
 * @param {any} state @returns {string | null}
 */
export function noticeOnLoad(state) {
  const flags = state.progress.flags;
  if (flags[STORY_FLAG]) return null;
  flags[STORY_FLAG] = true;
  state.saveRequested = true;
  return flags.princess_met ? null : NOTICE.oldSave;
}

/**
 * After a core of the murk is purified: with all four purified and 「星環の呼び声」 not yet
 * reported (or never taken), the notice to show. @param {any} state @returns {string | null}
 */
export function noticeOnCore(state) {
  if (coresPurified(state) < 4) return null;
  return questState(state, 'star_ring_call') === 'done' ? null : NOTICE.allCores;
}
