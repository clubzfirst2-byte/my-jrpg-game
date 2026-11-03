// @ts-check
// Game state and the single fixed-step update entry point for the logic layer.
import { parseMap } from './world/tilemap.js';
import { createPlayer, updatePlayer } from './entities/player.js';
import { STEP_SEC } from './core/fixedStep.js';
import { TEST_FIELD } from './world/maps/testField.js';

/**
 * @typedef {object} GameState
 * @property {number} tick
 * @property {import('./world/tilemap.js').TileMap} map
 * @property {import('./entities/player.js').Player} player
 */

/** @param {string[]} [rows] @returns {GameState} */
export function createGameState(rows = TEST_FIELD) {
  const map = parseMap(rows);
  return { tick: 0, map, player: createPlayer(map.spawn.x, map.spawn.y) };
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
