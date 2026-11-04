// @ts-check
// Game state and the single fixed-step update entry point for the logic layer.
import { parseMap } from './world/tilemap.js';
import { groundHeightUnder } from './physics/collision.js';
import { createPlayer, updatePlayer, respawn } from './entities/player.js';
import { combatStep, initCombat, COMBAT } from './entities/playerCombat.js';
import { createEnemy, updateEnemy } from './entities/enemies.js';
import { updateProjectiles } from './entities/projectiles.js';
import { hitEnemy } from './combat/damage.js';
import { overlaps } from './combat/hitbox.js';
import { STEP_SEC } from './core/fixedStep.js';
import {
  emptyProgress,
  placeFeatureSolids,
  touchCheckpoints,
  checkWarps,
  discoverLandmarks,
  respawnPoint,
} from './world/features.js';
import { createEnv, stepEnv, SOLID_OBJECTS } from './env/envSim.js';
import { swordHitsObjects, fireDamage } from './env/envActions.js';
import { applyWeatherToPlayer, stormStep } from './env/weatherActions.js';
import { CLOCK } from './env/weather.js';
import { ISLAND } from './world/maps/island.js';
import { TEST_FIELD } from './world/maps/testField.js';
import { HEIGHT_TEST } from './world/maps/heightTest.js';

/** Maps selectable with ?map=... (P3.5 default: the first island). */
export const MAPS = Object.freeze({ island: ISLAND, height: HEIGHT_TEST, field: TEST_FIELD });

/** Landmarks within this distance count as seen (about half a screen). */
const SIGHT_PX = 200;

/** Seconds between collapsing and getting back up at the spawn point. */
export const DEATH_DELAY_MS = 2000;
/** Enemies that died stay (fading) this long before they are removed from play. */
const ENEMY_CORPSE_MS = 600;

/**
 * @typedef {object} GameState
 * @property {number} tick
 * @property {import('./world/tilemap.js').TileMap} map
 * @property {import('./entities/player.js').Player & Record<string, any>} player
 * @property {any[]} enemies
 * @property {any[]} projectiles
 * @property {any[]} hitboxes   player attack hitboxes live this step (also read by the view)
 * @property {{ type: string, tick: number, x?: number, y?: number }[]} events  recent events for the view
 * @property {number} flurryMs  perfect-dodge slow motion remaining
 * @property {boolean} bulletTime aiming in mid-air (everything slowed)
 * @property {number} deathMs   time since the player collapsed (-1 when alive)
 * @property {number} nextId
 * @property {{ kind: 'beast' | 'archer', tx: number, ty: number }[]} enemySpawns
 * @property {any[]} chests
 * @property {any[]} checkpointDefs
 * @property {any[]} campfires
 * @property {any[]} warps
 * @property {any[]} areas
 * @property {any | null} outdoor
 * @property {any[]} landmarks
 * @property {import('./world/features.js').Progress} progress
 * @property {boolean} saveRequested  something worth saving happened (the platform layer saves)
 * @property {import('./env/envSim.js').Env} env  environment simulation (P4)
 */

/** @param {import('./world/tilemap.js').MapDef} [def] @returns {GameState} */
export function createGameState(def = HEIGHT_TEST) {
  const f = /** @type {import('./world/tilemap.js').IslandDef} */ (Array.isArray(def) ? { ground: def } : def);
  const map = parseMap(def);
  const z = groundHeightUnder({ x: map.spawn.x, y: map.spawn.y, halfWidth: 5, height: 6 }, map);
  const player = /** @type {any} */ (createPlayer(map.spawn.x, map.spawn.y, z));
  initCombat(player);
  /** @type {GameState} */
  const state = {
    tick: 0,
    map,
    player,
    enemies: [],
    projectiles: [],
    hitboxes: [],
    events: [],
    flurryMs: 0,
    bulletTime: false,
    deathMs: -1,
    nextId: 1,
    enemySpawns: f.enemies ?? [],
    chests: f.chests ?? [],
    checkpointDefs: f.checkpoints ?? [],
    campfires: f.campfires ?? [],
    warps: f.warps ?? [],
    areas: f.areas ?? [],
    outdoor: f.outdoor ?? null,
    landmarks: f.landmarks ?? [],
    progress: emptyProgress(),
    saveRequested: false,
    env: /** @type {any} */ (null),
  };
  placeFeatureSolids(state);
  // P4: environment objects join the map's objects (the view draws them all the same way).
  for (const o of f.envObjects ?? []) {
    map.objects.push({ ...o });
    if (SOLID_OBJECTS.has(o.type)) map.solid[o.ty * map.width + o.tx] = 1;
  }
  const campfires = state.campfires.map((c) => ({ type: 'campfire', tx: c.tx, ty: c.ty }));
  state.env = createEnv(map, [...map.objects, ...campfires], 1, CLOCK.startHour * CLOCK.hourMs);
  // Caves are under a roof: no rain, no wind, no lightning.
  for (const a of state.areas) {
    for (let ty = a.ty; ty < a.ty + a.th; ty++) for (let tx = a.tx; tx < a.tx + a.tw; tx++) state.env.indoor[ty * map.width + tx] = 1;
  }
  spawnEnemies(state);
  return state;
}

/** (Re)places every enemy of the map at its spawn point. @param {GameState} state */
export function spawnEnemies(state) {
  const ts = state.map.tileSize;
  state.enemies = state.enemySpawns.map((s, i) => {
    const x = s.tx * ts + ts / 2;
    const y = s.ty * ts + ts - 2;
    const z = groundHeightUnder({ x, y, halfWidth: 5, height: 6 }, state.map);
    return createEnemy(s.kind, x, y, z, i + 1);
  });
}

/**
 * Advances the game by exactly one fixed step.
 * @param {GameState} state
 * @param {import('./input.js').InputFrame} input
 */
export function stepGame(state, input) {
  state.tick++;
  state.hitboxes = [];
  // The world keeps going while the player is down (fires burn on).
  stepEnv(state.env, state.map, state.player, STEP_SEC * 1000);
  stormStep(state, STEP_SEC * 1000);
  applyWeatherToPlayer(state);
  if (state.events.length > 64) state.events.splice(0, state.events.length - 64);
  const p = state.player;

  // Death sequence (P3): collapse, wait, get back up at the spawn point with enemies reset.
  if (p.dead) {
    if (state.deathMs < 0) {
      state.deathMs = 0;
      state.events.push({ type: 'death', tick: state.tick, x: p.x, y: p.y });
    }
    state.deathMs += STEP_SEC * 1000;
    if (state.deathMs >= DEATH_DELAY_MS) respawnPlayer(state);
    return;
  }

  // Slow motion: bullet time slows everything; a perfect dodge slows only the enemies.
  combatStep(p, input, state, STEP_SEC);
  const worldScale = state.bulletTime ? COMBAT.bulletTimeScale : 1;
  const enemyScale = worldScale * (state.flurryMs > 0 ? COMBAT.flurryScale : 1);
  state.flurryMs = Math.max(0, state.flurryMs - STEP_SEC * 1000);

  updatePlayer(p, input, state.map, STEP_SEC * worldScale);
  touchCheckpoints(state);
  checkWarps(state);
  discoverLandmarks(state, SIGHT_PX);

  // Player sword hits.
  for (const hb of state.hitboxes) {
    for (const e of state.enemies) {
      if (e.state !== 'dead' && overlaps(hb, { x: e.x, y: e.y - 3, z: e.z, r: 6 })) hitEnemy(state, e, hb);
    }
  }

  swordHitsObjects(state);

  const enemyDt = STEP_SEC * enemyScale;
  fireDamage(state, enemyDt * 1000);
  for (const e of state.enemies) updateEnemy(e, state, enemyDt);
  state.enemies = state.enemies.filter((e) => !(e.state === 'dead' && e.t > ENEMY_CORPSE_MS));
  pushApart(state);
  updateProjectiles(state, enemyDt);
}

/** Keeps the player and enemies from standing inside each other. @param {GameState} state */
function pushApart(state) {
  const p = state.player;
  for (const e of state.enemies) {
    if (e.state === 'dead' || Math.abs(e.z - p.z) > 12) continue;
    const dx = e.x - p.x;
    const dy = e.y - p.y;
    const d = Math.hypot(dx, dy);
    const min = 10;
    if (d > 0.001 && d < min) {
      // Move the enemy, not the player: the player's position is never pushed into walls.
      const push = min - d;
      e.x += (dx / d) * push;
      e.y += (dy / d) * push;
    }
  }
}

/** @param {GameState} state */
export function respawnPlayer(state) {
  const p = state.player;
  // Back at the active checkpoint (P3.5), else the map's start.
  const at = respawnPoint(state);
  p.spawnX = at.x;
  p.spawnY = at.y;
  p.spawnZ = groundHeightUnder({ x: at.x, y: at.y, halfWidth: 5, height: 6 }, state.map);
  p.maxHp = state.progress.maxHp;
  respawn(p);
  initCombat(p);
  state.deathMs = -1;
  state.flurryMs = 0;
  state.projectiles = [];
  spawnEnemies(state);
  state.events.push({ type: 'respawn', tick: state.tick });
}
