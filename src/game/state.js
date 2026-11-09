// @ts-check
// Game state and the single fixed-step update entry point for the logic layer.
import { parseMap } from './world/tilemap.js';
import { groundHeightUnder } from './physics/collision.js';
import { createPlayer, updatePlayer, respawn } from './entities/player.js';
import { combatStep, initCombat, COMBAT } from './entities/playerCombat.js';
import { createBoss, settleBosses } from './entities/bosses.js';
import { placeFinalBoss, settleFinalBoss, FINAL_BOSS } from './entities/finalBoss.js';
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
import { CLOCK, seasonAt } from './env/weather.js';
import { applyGear, itemStep, placePickups } from './items/itemSystem.js';
import { stepSwitches } from './puzzles/switches.js';
import { useAbility, stepAbilities, grantAbility } from './puzzles/abilities.js';
import { areaAt } from './world/features.js';
import { ISLAND } from './world/maps/island.js';
import { WORLD } from './world/world.js';
import { objectBaseline } from './world/worldDiff.js';
import { createNpcs, stepNpcs } from './npc/npcs.js';
import { TEST_FIELD } from './world/maps/testField.js';
import { HEIGHT_TEST } from './world/maps/heightTest.js';

/** Maps selectable with ?map=... (P3.5 default: the first island). */
export const MAPS = Object.freeze({ world: WORLD, island: ISLAND, height: HEIGHT_TEST, field: TEST_FIELD });

/** Landmarks within this distance count as seen (about half a screen). */
const SIGHT_PX = 200;

/** Seconds between collapsing and getting back up at the spawn point. */
export const DEATH_DELAY_MS = 2000;
/** Enemies that died stay (fading) this long before they are removed from play. */
const ENEMY_CORPSE_MS = 600;

/**
 * @typedef {object} GameState
 * @property {number} tick
 * @property {'easy' | 'normal' | 'hard'} difficulty  P11.3: how hard enemy hits land (a player setting)
 * @property {import('./env/weather.js').SeasonId | null} season  P10.2: the season the world is dressed for
 * @property {string} [spawnSeason]  the season the enemies were placed for
 * @property {import('./world/tilemap.js').TileMap} map
 * @property {import('./entities/player.js').Player & Record<string, any>} player
 * @property {any[]} enemies
 * @property {any[]} projectiles
 * @property {any[]} hitboxes   player attack hitboxes live this step (also read by the view)
 * @property {{ type: string, tick: number, x?: number, y?: number, id?: string }[]} events  recent events for the view
 * @property {number} flurryMs  perfect-dodge slow motion remaining
 * @property {boolean} bulletTime aiming in mid-air (everything slowed)
 * @property {number} deathMs   time since the player collapsed (-1 when alive)
 * @property {number} nextId
 * @property {import('./world/tilemap.js').EnemySpawn[]} enemySpawns
 * @property {import('./entities/bosses.js').BossDef[]} bossDefs  P10.4
 * @property {import('./entities/finalBoss.js').FinalBossDef | null} finalBossDef  v1.0 (C7): 淀みの源
 * @property {any[]} chests
 * @property {any[]} checkpointDefs
 * @property {any[]} campfires
 * @property {any[]} warps
 * @property {any[]} areas
 * @property {any | null} outdoor
 * @property {any[]} outdoors  P10.3: camera bounds of each column of regions
 * @property {any[]} landmarks
 * @property {import('./world/features.js').Progress} progress
 * @property {boolean} saveRequested  something worth saving happened (the platform layer saves)
 * @property {import('./env/envSim.js').Env} env  environment simulation (P4)
 * @property {any[]} pickupDefs   items placed by the map (P6)
 * @property {import('./items/itemSystem.js').Pickup[]} pickups  items lying in the world now
 * @property {any[]} landedHits   player sword hits that landed this step
 * @property {'cook' | 'forge' | 'talk' | 'sleep' | null} nearby  something to use in reach
 * @property {import('./npc/npcs.js').Npc | null} [nearbyNpc]  P9: the villager in front
 * @property {number} respawns
 * @property {boolean} [pickupsStale]
 * @property {import('./puzzles/switches.js').SwitchDef[]} switches  P7
 * @property {Record<string, number>} switchUntil  stones: active until (world ms)
 * @property {Record<string, boolean>} switchActive  for the view and tests
 * @property {{ x: number, y: number, z: number, untilMs: number } | null} orb   灯火
 * @property {{ x: number, y: number, startMs: number } | null} pulse  共鳴
 * @property {number} abilityReadyAt
 * @property {boolean} abilityHeld
 * @property {import('./world/world.js').RegionInfo[]} regions  P8
 * @property {any[]} objectBaseline  P8: objects as the map made them (for saving differences)
 * @property {import('./npc/npcs.js').Npc[]} npcs  P9: villagers
 * @property {{ id: string, npc: string | null, node: string, line: number } | null} dialogue  P9: the conversation going on
 * @property {string | null} shop  P9: the shop open now
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
    season: null,
    difficulty: 'normal',
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
    bossDefs: f.bosses ?? [],
    finalBossDef: f.finalBoss ?? null,
    chests: f.chests ?? [],
    checkpointDefs: f.checkpoints ?? [],
    campfires: f.campfires ?? [],
    warps: f.warps ?? [],
    areas: f.areas ?? [],
    outdoor: f.outdoor ?? null,
    outdoors: f.outdoors ?? (f.outdoor ? [f.outdoor] : []),
    landmarks: f.landmarks ?? [],
    progress: emptyProgress(),
    saveRequested: false,
    env: /** @type {any} */ (null),
    pickupDefs: f.pickups ?? [],
    pickups: [],
    landedHits: [],
    nearby: null,
    respawns: 0,
    pickupsStale: true,
    switches: f.switches ?? [],
    switchUntil: {},
    switchActive: {},
    orb: null,
    pulse: null,
    abilityReadyAt: 0,
    abilityHeld: false,
    regions: f.regions ?? [],
    objectBaseline: [],
    npcs: [],
    dialogue: null,
    shop: null,
  };
  placeFeatureSolids(state);
  // P4: environment objects join the map's objects (the view draws them all the same way).
  for (const o of f.envObjects ?? []) {
    map.objects.push({ ...o });
    if (SOLID_OBJECTS.has(o.type)) map.solid[o.ty * map.width + o.tx] = 1;
    // P9: a house covers 3 x 2 tiles (its door tile at the bottom middle is the anchor).
    if (o.type === 'house') {
      for (let dy = -1; dy <= 0; dy++) for (let dx = -1; dx <= 1; dx++) map.solid[(o.ty + dy) * map.width + o.tx + dx] = 1;
    }
  }
  state.objectBaseline = objectBaseline(map.objects);
  state.npcs = createNpcs(map, f.npcs ?? []);
  const campfires = state.campfires.map((c) => ({ type: 'campfire', tx: c.tx, ty: c.ty }));
  state.env = createEnv(map, [...map.objects, ...campfires], 1, CLOCK.startHour * CLOCK.hourMs);
  // P8: dry regions (the desert) never get rain.
  // P10.3: cold regions (the mountains) snow instead of raining.
  for (const r of f.regions ?? []) {
    const mark = r.climate === 'dry' ? state.env.dry : r.climate === 'cold' ? state.env.cold : null;
    if (!mark) continue;
    for (let ty = r.ty; ty < r.ty + r.th; ty++) for (let tx = r.tx; tx < r.tx + r.tw; tx++) mark[ty * map.width + tx] = 1;
  }
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
  // P10.2: some enemies only come out in certain seasons.
  const season = seasonAt(state.env.now).id;
  state.spawnSeason = season;
  state.enemies = state.enemySpawns.flatMap((s, i) => {
    if (s.seasons && !s.seasons.includes(season)) return [];
    const x = s.tx * ts + ts / 2;
    const y = s.ty * ts + ts - 2;
    const z = groundHeightUnder({ x, y, halfWidth: 5, height: 6 }, state.map);
    return [createEnemy(s.kind, x, y, z, i + 1)];
  });
  // P10.4: the cores not yet purified wait in their arenas.
  state.bossDefs.forEach((/** @type {any} */ b, /** @type {number} */ k) => {
    if (!state.progress.bosses.includes(b.id)) state.enemies.push(createBoss(b, state.map, 1000 + k));
  });
}

/**
 * A new season (P10.2): its own items lie in the world and its own enemies come out.
 * @param {GameState} state
 */
function changeSeason(state) {
  const id = seasonAt(state.env.now).id;
  if (id === state.season) return;
  const first = state.season === null;
  state.season = id;
  state.pickupsStale = true;
  if (state.spawnSeason !== id) spawnEnemies(state); // (a saved game may start in another season)
  if (!first) state.events.push({ type: 'season', tick: state.tick, id });
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
  changeSeason(state);
  stormStep(state, STEP_SEC * 1000);
  applyGear(state);
  applyWeatherToPlayer(state);
  if (state.pickupsStale) {
    state.pickupsStale = false;
    placePickups(state);
  }
  state.landedHits = [];
  // P7: the ability button (on the press, not while held).
  if (input.ability && !state.abilityHeld && !state.player.dead) useAbility(state);
  state.abilityHeld = !!input.ability;
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
      if (e.state !== 'dead' && overlaps(hb, { x: e.x, y: e.y - 3, z: e.z, r: e.r ?? 6 }) && hitEnemy(state, e, hb)) state.landedHits.push(hb);
    }
  }

  swordHitsObjects(state);

  placeFinalBoss(state); // v1.0: the source appears when the player steps into its arena
  const enemyDt = STEP_SEC * enemyScale;
  fireDamage(state, enemyDt * 1000);
  for (const e of state.enemies) updateEnemy(e, state, enemyDt);
  state.enemies = state.enemies.filter((e) => !(e.state === 'dead' && e.t > (e.final ? FINAL_BOSS.defeatMs : ENEMY_CORPSE_MS)));
  pushApart(state);
  updateProjectiles(state, enemyDt);
  itemStep(state);
  stepNpcs(state, STEP_SEC);
  stepAbilities(state);
  stepSwitches(state);
  learnAbilities(state);
  settleBosses(state);
  settleFinalBoss(state);
}

/**
 * Entering a trial teaches its ability; touching the tower altar teaches resonance (P7).
 * @param {GameState} state
 */
function learnAbilities(state) {
  const p = state.player;
  const area = areaAt(state, p.x, p.y);
  if (area?.grants) grantAbility(state, area.grants);
  const ts = state.map.tileSize;
  for (const [i, o] of state.env.objectAt) {
    if (o.type !== 'altar') continue;
    const ax = (i % state.map.width) * ts + ts / 2;
    const ay = Math.floor(i / state.map.width) * ts + ts / 2;
    if (Math.hypot(ax - p.x, ay - (p.y - 4)) <= 22 && Math.abs(state.map.elev[i] - p.z) < 12) grantAbility(state, 'resonance');
  }
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
  p.maxStamina = state.progress.maxStamina ?? 100;
  respawn(p);
  initCombat(p);
  state.deathMs = -1;
  state.flurryMs = 0;
  state.projectiles = [];
  spawnEnemies(state);
  state.events.push({ type: 'respawn', tick: state.tick });
  state.respawns += 1;
}
