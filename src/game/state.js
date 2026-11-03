// @ts-check
// Game state and the single fixed-step update entry point for the logic layer.
import { parseMap } from './world/tilemap.js';
import { groundHeightUnder } from './physics/collision.js';
import { createPlayer, updatePlayer } from './entities/player.js';
import { STEP_SEC } from './core/fixedStep.js';
import { TEST_FIELD } from './world/maps/testField.js';
import { HEIGHT_TEST } from './world/maps/heightTest.js';

/** Maps selectable with ?map=... (P2 default: the height verification map). */
export const MAPS = Object.freeze({ height: HEIGHT_TEST, field: TEST_FIELD });

/**
 * @typedef {object} GameState
 * @property {number} tick
 * @property {import('./world/tilemap.js').TileMap} map
 * @property {import('./entities/player.js').Player} player
 */

/** @param {import('./world/tilemap.js').MapDef} [def] @returns {GameState} */
export function createGameState(def = HEIGHT_TEST) {
  const map = parseMap(def);
  const z = groundHeightUnder({ x: map.spawn.x, y: map.spawn.y, halfWidth: 5, height: 6 }, map);
  return { tick: 0, map, player: createPlayer(map.spawn.x, map.spawn.y, z) };
}

/**
 * Advances the game by exactly one fixed step.
 * @param {GameState} state
 * @param {import('./input.js').InputFrame} input
 */
export function stepGame(state, input) {
  state.tick++;
  updatePlayer(state.player, input, state.map, STEP_SEC);
}
