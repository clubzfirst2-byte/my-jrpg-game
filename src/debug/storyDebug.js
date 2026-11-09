// @ts-check
// v1.0 (C9 / C10): test helpers for the opening and the ending on window.__debugApi (main.js adds
// these). E2E: tests/e2e/v1-ending.spec.js.
import { skipOpening, openingView } from '../game/story/story.js';
import { coresPurified } from '../game/npc/talk.js';

const CORES = ['core_forest', 'core_mountains', 'core_desert', 'core_lake'];

/** @param {any} state */
export function storyDebugApi(state) {
  return {
    /** The opening now (null when none): its time and what it shows. */
    opening: () => (state.opening ? { ms: state.opening.ms, ...openingView(state) } : null),
    skipOpening: () => skipOpening(state),
    /** Marks the first n cores of the murk purified (as if their bosses had fallen). */
    setCores: (/** @type {number} */ n) => {
      for (const id of CORES.slice(0, n)) if (!state.progress.bosses.includes(id)) state.progress.bosses.push(id);
      return coresPurified(state);
    },
    /** The ending's state: 'screen' while its screen shows; the tick the dialogue starts by itself. */
    ending: () => ({ ending: state.ending, endingAt: state.endingAt, tick: state.tick }),
  };
}
