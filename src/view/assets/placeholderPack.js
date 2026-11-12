// @ts-check
// Builds the placeholder art into ONE atlas texture so everything batches into few draw calls.
// A production pack must provide the same logical names and anchors (DESIGN.md 7.5).
import { Rectangle, Texture } from 'pixi.js';
import { LEVEL_PX } from '../../game/world/tilemap.js';
import {
  PALETTE,
  archerFrames,
  arrowSprite,
  beastFrames,
  slimeFrames,
  sentinelFrames,
  bowSprite,
  orbSprite,
  shieldSprite,
  slashSprite,
  earthFace,
  grassTile,
  pathTile,
  playerFrames,
  gliderSprite,
  rampSprite,
  rockSprite,
  ruinFace,
  ruinFloorTile,
  shadowSprite,
  swimFrames,
  treeSprite,
  waterTile,
  sandTile,
  chestSprite,
  checkpointSprite,
  campfireFrames,
  smokeSprite,
  caveSprite,
  markerSprite,
  metalTile,
  fireFrames,
  brambleSprite,
  crystalSprite,
  jarSprite,
  receiverSprite,
  doorSprite,
  brazierFrames,
  stumpSprite,
  anvilSprite,
  itemIcons,
  pitTile,
  vineTile,
  pillarSprite,
  altarSprite,
  crateSprite,
  sconceSprite,
  stoneSprite,
  plateSprite,
  sensorSprite,
  lightOrbSprite,
  desertSandTile,
  plainsGrassTile,
  cactusSprite,
  villagerFrames,
  houseSprite,
  woodFloorTile,
  wallTopTile,
  darkTile,
  plasterFace,
  lowWallSprite,
  bedSprite,
  tableSprite,
  shelfSprite,
  counterSprite,
  stoveSprite,
  barrelSprite,
  matSprite,
  springTreeSprite,
  autumnTreeSprite,
  autumnGrass,
  winterTreeSprite,
  snowTile,
  winterLip,
  autumnLip,
  forestGrassTile,
  pineSprite,
  mountainSnowTile,
  snowPineSprite,
  stoneFace,
  lakeGrassTile,
  bossSprite,
  stairsSprite,
  PRINCESS_LOOK,
} from './placeholderArt.js';
import { sourceFrames, starRingSprite } from './sourceArt.js';
import { ICON_ANCHORS } from './iconAnchors.js';
import { releaseTerrainEntries } from './terrainArt.js';

const FEET = /** @type {[number, number]} */ ([0.5, 1]);
const TOP_LEFT = /** @type {[number, number]} */ ([0, 0]);

/** @returns {{ key: string, rows: string[], anchor: [number, number] }[]} */
export function placeholderEntries() {
  const entries = [];
  for (const [key, rows] of Object.entries(playerFrames())) entries.push({ key, rows, anchor: FEET });
  for (const [key, rows] of Object.entries(swimFrames())) entries.push({ key, rows, anchor: FEET });
  for (let i = 0; i < 3; i++) entries.push({ key: `tile.grass.${i}`, rows: grassTile(100 + i), anchor: TOP_LEFT });
  entries.push({ key: 'tile.path', rows: pathTile(), anchor: TOP_LEFT });
  for (let i = 0; i < 2; i++) entries.push({ key: `tile.water.${i}`, rows: waterTile(i), anchor: TOP_LEFT });
  entries.push({ key: 'tile.ruin', rows: ruinFloorTile(), anchor: TOP_LEFT });
  entries.push({ key: 'tile.ramp', rows: rampSprite(LEVEL_PX), anchor: TOP_LEFT });
  // Cliff face segments: face.<material>.<top|mid><bottom?>.<4|8>
  for (const [mat, face] of /** @type {const} */ ([['earth', earthFace], ['ruin', ruinFace], ['wall', plasterFace]])) {
    for (const h of [4, 8]) {
      for (const top of [true, false]) {
        for (const bottom of [true, false]) {
          const key = `face.${mat}.${top ? 'top' : 'mid'}${bottom ? '-base' : ''}.${h}`;
          entries.push({ key, rows: face(h, top, bottom), anchor: TOP_LEFT });
        }
      }
    }
  }
  entries.push({ key: 'fx.glider', rows: gliderSprite(), anchor: FEET });
  entries.push({ key: 'fx.shadow', rows: shadowSprite(), anchor: /** @type {[number, number]} */ ([0.5, 0.5]) });
  entries.push({ key: 'px', rows: ['XX', 'XX'], anchor: TOP_LEFT });
  entries.push({ key: 'obj.rock', rows: rockSprite(), anchor: FEET });
  const CENTER = /** @type {[number, number]} */ ([0.5, 0.5]);
  for (const [key, rows] of Object.entries({ ...beastFrames(), ...archerFrames(), ...slimeFrames(), ...sentinelFrames() })) entries.push({ key, rows, anchor: FEET });
  entries.push({ key: 'fx.slash', rows: slashSprite(), anchor: CENTER });
  entries.push({ key: 'fx.arrow', rows: arrowSprite(), anchor: CENTER });
  entries.push({ key: 'fx.orb', rows: orbSprite(), anchor: CENTER });
  entries.push({ key: 'fx.shield', rows: shieldSprite(), anchor: CENTER });
  entries.push({ key: 'fx.bow', rows: bowSprite(), anchor: CENTER });
  entries.push({ key: 'obj.tree', rows: treeSprite(), anchor: FEET });
  // P3.5 island features.
  entries.push({ key: 'tile.sand', rows: sandTile(), anchor: TOP_LEFT });
  entries.push({ key: 'obj.chest.closed', rows: chestSprite(false), anchor: FEET });
  entries.push({ key: 'obj.chest.open', rows: chestSprite(true), anchor: FEET });
  entries.push({ key: 'obj.checkpoint.off', rows: checkpointSprite(false), anchor: FEET });
  entries.push({ key: 'obj.checkpoint.on', rows: checkpointSprite(true), anchor: FEET });
  for (const [key, rows] of Object.entries(campfireFrames())) entries.push({ key, rows, anchor: FEET });
  entries.push({ key: 'fx.smoke', rows: smokeSprite(), anchor: CENTER });
  entries.push({ key: 'obj.cave', rows: caveSprite(), anchor: FEET });
  entries.push({ key: 'ui.marker', rows: markerSprite(), anchor: CENTER });
  // P4 environment.
  entries.push({ key: 'tile.metal', rows: metalTile(), anchor: TOP_LEFT });
  for (const [key, rows] of Object.entries(fireFrames())) entries.push({ key, rows, anchor: FEET });
  for (const [key, rows] of Object.entries(brazierFrames())) entries.push({ key, rows, anchor: FEET });
  entries.push({ key: 'obj.bramble', rows: brambleSprite(), anchor: FEET });
  entries.push({ key: 'obj.crystal', rows: crystalSprite(), anchor: FEET });
  entries.push({ key: 'obj.jar', rows: jarSprite(), anchor: FEET });
  entries.push({ key: 'obj.receiver.off', rows: receiverSprite(false), anchor: FEET });
  entries.push({ key: 'obj.receiver.on', rows: receiverSprite(true), anchor: FEET });
  entries.push({ key: 'obj.door', rows: doorSprite(), anchor: FEET });
  entries.push({ key: 'obj.stump', rows: stumpSprite(), anchor: FEET });
  // P6 items.
  entries.push({ key: 'obj.anvil', rows: anvilSprite(), anchor: FEET });
  for (const [key, rows] of Object.entries(itemIcons())) entries.push({ key, rows, anchor: ICON_ANCHORS[key] ?? FEET });
  // P7 puzzles.
  entries.push({ key: 'tile.pit', rows: pitTile(), anchor: TOP_LEFT });
  entries.push({ key: 'tile.vine', rows: vineTile(), anchor: TOP_LEFT });
  entries.push({ key: 'obj.pillar', rows: pillarSprite(), anchor: FEET });
  entries.push({ key: 'obj.altar', rows: altarSprite(), anchor: FEET });
  entries.push({ key: 'obj.crate', rows: crateSprite(), anchor: FEET });
  entries.push({ key: 'obj.sconce.off', rows: sconceSprite(false), anchor: FEET });
  entries.push({ key: 'obj.sconce.on', rows: sconceSprite(true), anchor: FEET });
  entries.push({ key: 'obj.stone.off', rows: stoneSprite(false), anchor: FEET });
  entries.push({ key: 'obj.stone.on', rows: stoneSprite(true), anchor: FEET });
  entries.push({ key: 'sw.plate.off', rows: plateSprite(false), anchor: FEET });
  entries.push({ key: 'sw.plate.on', rows: plateSprite(true), anchor: FEET });
  entries.push({ key: 'sw.sensor.off', rows: sensorSprite(false), anchor: FEET });
  entries.push({ key: 'sw.sensor.on', rows: sensorSprite(true), anchor: FEET });
  entries.push({ key: 'fx.light', rows: lightOrbSprite(), anchor: CENTER });
  // P10.1: house floors and walls (rooms can be in any region's strip); nothing outside the rooms.
  entries.push({ key: 'tile.wood', rows: woodFloorTile(), anchor: TOP_LEFT });
  entries.push({ key: 'tile.walltop', rows: wallTopTile(), anchor: TOP_LEFT });
  entries.push({ key: 'tile.dark', rows: darkTile(), anchor: TOP_LEFT });
  // v1.0 (C5): the small 星環 on the beach (the island has no region bundle).
  entries.push({ key: 'obj.star_ring.off', rows: starRingSprite(false), anchor: FEET });
  entries.push({ key: 'obj.star_ring.on', rows: starRingSprite(true), anchor: FEET });
  // v1.0 (C4): the princess's placeholder look — she appears by the record stones of every region,
  // and the island has no region bundle, so her art is in the base bundle.
  for (const [key, rows] of Object.entries(villagerFrames(PRINCESS_LOOK))) entries.push({ key, rows, anchor: FEET });
  return entries;
}

/**
 * Region bundles (P8): each region's own art, loaded near it and released away from it.
 * @type {Record<string, () => { key: string, rows: string[], anchor: [number, number] }[]>}
 */
export const REGION_ENTRIES = {
  'region:desert': () => [
    ...[0, 1, 2].map((i) => ({ key: `desert.sand.${i}`, rows: desertSandTile(i), anchor: TOP_LEFT })),
    { key: 'obj.cactus', rows: cactusSprite(), anchor: FEET },
  ],
  'region:plains': () => [
    ...[0, 1, 2, 3].map((i) => ({ key: `plains.grass.${i}`, rows: plainsGrassTile(i), anchor: TOP_LEFT })),
    // P9: the village of 風見 (houses and villagers) is in the plains.
    { key: 'obj.house', rows: houseSprite(), anchor: FEET },
    // v1.0: 6 woman, 7 smith, 8 traveller (the pass east of the plains).
    ...[1, 2, 3, 4, 5, 6, 7, 8].flatMap((look) => Object.entries(villagerFrames(look)).map(([key, rows]) => ({ key, rows, anchor: FEET }))),
    // P10.1: the furniture inside the village houses.
    { key: 'obj.lowwall', rows: lowWallSprite(), anchor: FEET },
    { key: 'obj.bed', rows: bedSprite(), anchor: FEET },
    { key: 'obj.table', rows: tableSprite(), anchor: FEET },
    { key: 'obj.shelf', rows: shelfSprite(), anchor: FEET },
    { key: 'obj.charm_shelf', rows: shelfSprite(), anchor: FEET },
    { key: 'obj.charm_shelf.on', rows: shelfSprite(true), anchor: FEET },
    { key: 'obj.counter', rows: counterSprite(), anchor: FEET },
    { key: 'obj.stove', rows: stoveSprite(), anchor: FEET },
    { key: 'obj.barrel', rows: barrelSprite(), anchor: FEET },
    { key: 'obj.mat', rows: matSprite(), anchor: FEET },
  ],
  // P10.3: the east column.
  'region:forest': () => [
    ...[0, 1, 2, 3].map((i) => ({ key: `forest.grass.${i}`, rows: forestGrassTile(i), anchor: TOP_LEFT })),
    { key: 'forest.pine', rows: pineSprite(), anchor: FEET },
  ],
  'region:mountains': () => [
    ...[0, 1, 2, 3].map((i) => ({ key: `mountains.snow.${i}`, rows: mountainSnowTile(i), anchor: TOP_LEFT })),
    { key: 'mountains.pine', rows: snowPineSprite(), anchor: FEET },
    { key: 'obj.stairs', rows: stairsSprite(), anchor: FEET }, // P10.5: 白嶺の坑道
    ...[4, 8].flatMap((h) =>
      [true, false].flatMap((top) => [true, false].map((bottom) => ({ key: `face.stone.${top ? 'top' : 'mid'}${bottom ? '-base' : ''}.${h}`, rows: stoneFace(h, top, bottom), anchor: TOP_LEFT }))),
    ),
  ],
  'region:lake': () => [...[0, 1, 2, 3].map((i) => ({ key: `lake.grass.${i}`, rows: lakeGrassTile(i), anchor: TOP_LEFT }))],
};

/**
 * Season bundles (P10.2): each season's look of the ground, cliff lips and trees, named
 * "<season>.<the key it replaces>". Summer is the plain art (no bundle).
 */
const lipKeys = () => [4, 8].flatMap((h) => [false, true].map((bottom) => ({ key: `face.earth.top${bottom ? '-base' : ''}.${h}`, rows: earthFace(h, true, bottom) })));
const grassKeys = () => [
  ...[0, 1, 2].map((i) => ({ key: `tile.grass.${i}`, rows: grassTile(100 + i) })),
  ...[0, 1, 2, 3].map((i) => ({ key: `plains.grass.${i}`, rows: plainsGrassTile(i) })),
  // P10.3: the lake's grass dries and is snowed on too; the forest floor only under snow.
  ...[0, 1, 2, 3].map((i) => ({ key: `lake.grass.${i}`, rows: lakeGrassTile(i) })),
];
const forestKeys = () => [0, 1, 2, 3].map((i) => ({ key: `forest.grass.${i}`, rows: forestGrassTile(i) }));
/** @type {Record<string, () => { key: string, rows: string[], anchor: [number, number] }[]>} */
export const SEASON_ENTRIES = {
  'season:spring': () => [{ key: 'spring.obj.tree', rows: springTreeSprite(), anchor: FEET }],
  'season:autumn': () => [
    { key: 'autumn.obj.tree', rows: autumnTreeSprite(), anchor: FEET },
    ...grassKeys().map((e) => ({ key: `autumn.${e.key}`, rows: autumnGrass(e.rows), anchor: TOP_LEFT })),
    ...lipKeys().map((e) => ({ key: `autumn.${e.key}`, rows: autumnLip(e.rows), anchor: TOP_LEFT })),
  ],
  'season:winter': () => [
    { key: 'winter.obj.tree', rows: winterTreeSprite(), anchor: FEET },
    ...[...grassKeys(), ...forestKeys()].map((e, i) => ({ key: `winter.${e.key}`, rows: snowTile(i), anchor: TOP_LEFT })),
    { key: 'winter.forest.pine', rows: snowPineSprite(), anchor: FEET },
    ...lipKeys().map((e) => ({ key: `winter.${e.key}`, rows: winterLip(e.rows), anchor: TOP_LEFT })),
  ],
};
/** The keys a season replaces (without its prefix). @param {string} season */
export function seasonKeys(season) {
  const make = SEASON_ENTRIES[`season:${season}`];
  return new Set(make ? make().map((e) => e.key.slice(season.length + 1)) : []);
}
for (const [name, make] of Object.entries(SEASON_ENTRIES)) REGION_ENTRIES[name] = make;

// P10.4: each core of the murk is drawn by its region's bundle.
/** Which core each region's bundle draws. */
export const BOSS_REGIONS = /** @type {const} */ ({ 'region:forest': 'root', 'region:mountains': 'frost', 'region:desert': 'sand', 'region:lake': 'storm' });
const bossFrames = (/** @type {'root' | 'frost' | 'sand' | 'storm'} */ kind) => [0, 1].map((f) => ({ key: `enemy.boss_${kind}.${f}`, rows: bossSprite(kind, f), anchor: FEET }));
for (const [region, kind] of Object.entries(BOSS_REGIONS)) {
  const make = REGION_ENTRIES[region];
  REGION_ENTRIES[region] = () => [...make(), ...bossFrames(kind)];
}

/**
 * v1.0 (C7): the art of 淀みの源, a bundle of its own. The source fights in the desert's strip of
 * rooms, but its 64 × 64 frames do not fit the 256 × 256 base atlas, and they are not wanted
 * everywhere (about 4 MB once the release art is in): the view loads this bundle only while the
 * player is in the desert region (its strip includes the antechamber and the arena) and releases it
 * elsewhere (SOURCE_REGIONS, gameView.js). The small 星環 on the beach is in the base bundle.
 * The seats reuse the base bundle's sconce, sensor, plate, crate, stone, crystal and brazier.
 * Names: the release art's (enemy.boss_source.<action>.<frame>), so that art drops in under them.
 */
export const SOURCE_BUNDLE = 'common:source';
/** The regions near which the source's bundle is kept loaded. */
export const SOURCE_REGIONS = Object.freeze(['desert']);
/** @returns {{ key: string, rows: string[], anchor: [number, number] }[]} */
export function sourceEntries() {
  return Object.entries(sourceFrames()).map(([key, rows]) => ({ key, rows, anchor: FEET }));
}

/**
 * @param {string} name @param {Map<string, ArtSource>} [overrides]
 * @param {(e: { key: string }) => boolean} [keep] only these entries (gfx W1: a region's own ground in a bundle of its own)
 */
export function buildRegionPack(name, overrides, keep) {
  const entries = [...REGION_ENTRIES[name](), ...releaseBossEntries(name, overrides), ...releaseTerrainEntries(name, overrides)];
  return buildPlaceholderPack(keep ? entries.filter(keep) : entries, overrides);
}

/** Enemy release frames: enemy.<kind>.<action>.<n> (docs/art-release/enemy/frames.json on the art branch). */
const ENEMY_ACTION_KEY = /^enemy\.([a-z_]+)\.([a-z0-9_]+)\.\d+$/;

/**
 * The enemies' per-action release frames (enemy.<kind>.<idle|move|windup|attack|hurt|defeat>.<n>):
 * like the hero's, they get a slot in the base bundle only when such art is given; an enemy without
 * them keeps its enemy.<kind>.<0|1> frames. Cores of the murk (boss_*) go in their region's bundle
 * (releaseBossEntries); the final boss (boss_source) goes in its own bundle (common:source, sourceEntries) and the shots are not used yet. Only the names
 * are read (a URL or a packed sheet frame alike).
 * @param {Map<string, ArtSource>} [overrides]
 */
export function releaseEnemyEntries(overrides) {
  if (!overrides?.size) return [];
  return [...overrides.keys()]
    .filter((k) => {
      const m = ENEMY_ACTION_KEY.exec(k);
      return !!m && !m[1].startsWith('boss_') && m[1] !== 'shot';
    })
    .map((key) => ({ key, rows: ['.'], anchor: FEET }));
}

/**
 * A core's per-action release frames (enemy.boss_<kind>.<action>.<n>) go in its region's bundle, with
 * its enemy.boss_<kind>.<0|1> frames, so they are loaded and released with the region.
 * @param {string} region bundle name @param {Map<string, ArtSource>} [overrides] (only the names are read)
 */
export function releaseBossEntries(region, overrides) {
  const kind = /** @type {Record<string, string>} */ (BOSS_REGIONS)[region];
  if (!kind || !overrides?.size) return [];
  return [...overrides.keys()].filter((k) => ENEMY_ACTION_KEY.exec(k)?.[1] === `boss_${kind}`).map((key) => ({ key, rows: ['.'], anchor: FEET }));
}

/**
 * The hero's release animation frames (hero.<action>.<dir>.<frame>, docs/hero/HERO_ANIMATION_SPEC.md)
 * have no placeholder: they get a slot in the base bundle only when such art is given (?hero=release
 * until approved), so normal play builds exactly the same bundle.
 * @param {Map<string, ArtSource>} [overrides]
 */
export function releaseHeroEntries(overrides) {
  if (!overrides?.size) return [];
  return [...overrides.keys()].filter((k) => /^hero\.[a-z0-9]+\.(down|up|right|left)\.\d+$/.test(k)).map((key) => ({ key, rows: ['.'], anchor: FEET }));
}

/**
 * The villagers' release frames (npc.<id>.<idle|walk>.<dir>.<frame>, docs/npc/NPC_RELEASE_PLAN.md):
 * like the hero's, they get a slot in the base bundle only when such art is given. A villager
 * without them keeps the placeholder npc.<look>.* frames.
 * @param {Map<string, ArtSource>} [overrides]
 */
export function releaseNpcEntries(overrides) {
  if (!overrides?.size) return [];
  return [...overrides.keys()].filter((k) => /^npc\.[a-z]+\.(idle|walk)\.(down|up|right|left)\.\d+$/.test(k)).map((key) => ({ key, rows: ['.'], anchor: FEET }));
}

/** Width and height of an entry: its PNG when one replaces it, else the placeholder. @param {{ rows: string[], image?: { width: number, height: number } }} e */
const sizeOf = (e) => (e.image ? { w: e.image.width, h: e.image.height } : { w: e.rows[0].length, h: e.rows.length });

/**
 * gfx W1: the entries tallest first (same height: as given). Shelves of one height waste no rows, so the
 * base atlas also holds the v2 ground's ~360 island and water tiles within 2048×1024 (in the given
 * order it would need 2048×2048, or a second atlas of 2 MB). Used only with the v2 ground: the v1
 * atlas keeps its layout.
 * @template {{ rows: string[], image?: { width: number, height: number } }} E
 * @param {E[]} entries @returns {E[]}
 */
export function tallestFirstOrder(entries) {
  return entries.map((e, i) => ({ e, i, h: sizeOf(e).h })).sort((a, b) => b.h - a.h || a.i - b.i).map((x) => x.e);
}

/**
 * The atlas the entries fit in, with the same shelf packing: the narrowest power-of-two width (64 ..
 * 2048) whose square would hold them — the same width, so the same layout, as a square atlas — and
 * then the smallest power-of-two height (64 .. that width) the packed shelves actually use, so an
 * atlas that fills only the top of its square is not given the empty rest (perf v1: the base atlas
 * of the release art went from 2048×2048 to 2048×1024).
 * @param {{ rows: string[], image?: { width: number, height: number } }[]} entries
 * @returns {{ width: number, height: number }}
 */
export function atlasSizeFor(entries) {
  for (const size of [64, 128, 256, 512, 1024, 2048]) {
    let x = 0;
    let y = 0;
    let shelf = 0;
    let fits = true;
    for (const e of entries) {
      const { w, h } = sizeOf(e);
      if (x + w > size) {
        x = 0;
        y += shelf + 1;
        shelf = 0;
      }
      if (w > size || y + h > size) {
        fits = false;
        break;
      }
      x += w + 1;
      shelf = Math.max(shelf, h);
    }
    if (!fits) continue;
    const used = y + shelf;
    let height = 64;
    while (height < used) height *= 2;
    return { width: size, height: Math.min(height, size) };
  }
  throw new Error('Too many sprites for one atlas');
}

/** The largest atlas of the real art before the rest goes to a second atlas (perf v1: 2048×1024). */
export const ATLAS_MAX = /** @type {const} */ ({ width: 2048, height: 1024 });

/**
 * gfx v2 integration: the entries in atlases of at most 2048×1024. Entries that fit (atlasSizeFor at most
 * that) are one atlas, exactly as before. Otherwise, rather than a 2048×2048 atlas (8 MB more, half of it
 * empty), the first entries that fill 2048×1024 with the same shelf packing are one atlas, and the rest
 * (with tallestFirst: the shortest pieces) go on to the next, sized to fit them. (Ground v2 + enemy v2:
 * 19 rows over 1024 in one atlas.)
 * @template {{ rows: string[], image?: { width: number, height: number } }} E
 * @param {E[]} entries @returns {E[][]}
 */
export function splitForAtlas(entries) {
  const size = atlasSizeFor(entries);
  if (size.width < ATLAS_MAX.width || size.height <= ATLAS_MAX.height) return [entries];
  let x = 0;
  let y = 0;
  let shelf = 0;
  let n = 0;
  for (const e of entries) {
    const { w, h } = sizeOf(e);
    let nx = x;
    let ny = y;
    let ns = shelf;
    if (nx + w > ATLAS_MAX.width) {
      nx = 0;
      ny += ns + 1;
      ns = 0;
    }
    if (ny + h > ATLAS_MAX.height) break;
    x = nx + w + 1;
    y = ny;
    shelf = Math.max(ns, h);
    n++;
  }
  if (n === 0) throw new Error('Too many sprites for one atlas');
  return [entries.slice(0, n), ...splitForAtlas(entries.slice(n))];
}

/** The smallest power-of-two height (64 .. max) for `used` rows. @param {number} used @param {number} max */
const potHeight = (used, max) => {
  let height = 64;
  while (height < used) height *= 2;
  return Math.min(height, max);
};

/** Tallest first, then widest (same size: as given). @template {{ rows: string[], image?: { width: number, height: number } }} E @param {E[]} entries @returns {E[]} */
const byHeightThenWidth = (entries) =>
  entries.map((e, i) => ({ e, i, ...sizeOf(e) })).sort((a, b) => b.h - a.h || b.w - a.w || a.i - b.i).map((x) => x.e);

/**
 * gfx v2 integration: places on an atlas `width` wide by the skyline (bottom-left): each entry goes where
 * its top edge ends lowest, so the short pieces fill the space beside and above the tall ones that shelf
 * packing leaves empty. With the ground v2 and the enemy v2 the base bundle's real art then needs 1015
 * rows (one 2048×1024 atlas) where shelves need 1043 (a second atlas). 1 px apart, like the shelves.
 * Pure.
 * @template {{ rows: string[], image?: { width: number, height: number } }} E
 * @param {E[]} entries in the order to place them @param {number} width
 * @returns {{ entries: E[], places: { x: number, y: number }[], used: number }}
 */
export function skylinePlaces(entries, width) {
  const PAD = 1;
  /** segments of the skyline, left to right: [x, width, y] */
  let sky = [[0, width + PAD, 0]];
  /** @type {{ x: number, y: number }[]} */
  const places = [];
  let used = 0;
  for (const e of entries) {
    const { w, h } = sizeOf(e);
    const w1 = w + PAD;
    let best = null;
    for (let i = 0; i < sky.length; i++) {
      const x = sky[i][0];
      if (x + w1 > width + PAD) break;
      let y = 0;
      let left = w1;
      for (let j = i; left > 0 && j < sky.length; j++) {
        y = Math.max(y, sky[j][2]);
        left -= sky[j][1];
      }
      if (left > 0) continue;
      if (!best || y + h < best.y + h || (y === best.y && x < best.x)) best = { x, y };
    }
    if (!best) throw new Error(`Too wide for the atlas: ${w}`);
    places.push(best);
    used = Math.max(used, best.y + h);
    const { x, y } = best;
    /** @type {number[][]} */
    const next = [];
    for (const [sx, sw, sy] of sky) {
      const ex = sx + sw;
      if (ex <= x || sx >= x + w1) {
        next.push([sx, sw, sy]);
        continue;
      }
      if (sx < x) next.push([sx, x - sx, sy]);
      if (ex > x + w1) next.push([x + w1, ex - (x + w1), sy]);
    }
    next.push([x, w1, y + h + PAD]);
    next.sort((a, b) => a[0] - b[0]);
    sky = [];
    for (const s of next) {
      const last = sky[sky.length - 1];
      if (last && last[2] === s[2] && last[0] + last[1] === s[0]) last[1] += s[1];
      else sky.push(s);
    }
  }
  return { entries, places, used };
}

/**
 * P11.5 standard: the real art (src/art) has 2 art pixels per game pixel — tiles 32×32, characters
 * 32×56 (docs/ART.md). It is shown at half its pixel size, so it covers the same ground as the
 * placeholder while keeping its finer detail (the renderer draws 2 canvas pixels per game pixel).
 */
export const ART_SCALE = 2;

/**
 * Tiles and cliff faces sit on the 16 px grid, so their size is fixed (ART_SCALE × the placeholder);
 * other sprites may be any size (they are placed by their anchor: feet, or centre for effects).
 * @param {[number, number]} anchor
 */
export const mustKeepSize = (anchor) => anchor[0] === 0 && anchor[1] === 0;

/** @param {string} url @returns {Promise<HTMLImageElement>} */
function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Could not load ${url}`));
    img.src = url;
  });
}

/**
 * One frame of a packed release sheet (docs/perf/release-art-packing.md): the sheet's image and
 * where the frame sits on it, in its pixels.
 * @typedef {{ sheet: CanvasImageSource, x: number, y: number, w: number, h: number }} SheetFrame
 */
/** Where a sprite's art comes from: its own PNG's URL, or its place on a packed sheet. @typedef {string | SheetFrame} ArtSource */

/**
 * Copies a frame off its sheet into its own canvas, pixel for pixel, so it is drawn exactly as its
 * own PNG would be. @param {SheetFrame} f @returns {HTMLCanvasElement}
 */
export function cutSheetFrame(f) {
  const canvas = document.createElement('canvas');
  canvas.width = f.w;
  canvas.height = f.h;
  const ctx = /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d'));
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(f.sheet, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
  return canvas;
}

/**
 * P11.5: puts the real art (src/art/<name>.png) in place of the placeholder where there is one.
 * A tile of the wrong size is left as the placeholder (it would not fit the grid) and reported.
 * @param {{ key: string, rows: string[], anchor: [number, number] }[]} entries
 * @param {Map<string, ArtSource>} overrides logical name → PNG URL (artOverrides.js) or sheet frame
 * @returns {Promise<{ key: string, rows: string[], anchor: [number, number], image?: HTMLImageElement | HTMLCanvasElement }[]>}
 */
export async function withOverrides(entries, overrides) {
  if (overrides.size === 0) return entries;
  return Promise.all(
    entries.map(async (e) => {
      const url = overrides.get(e.key);
      if (!url) return e;
      try {
        const image = typeof url === 'string' ? await loadImage(url) : cutSheetFrame(url);
        const [w, h] = [e.rows[0].length * ART_SCALE, e.rows.length * ART_SCALE];
        if (mustKeepSize(e.anchor) && (image.width !== w || image.height !== h)) {
          console.warn(`art: ${e.key}.png must be ${w}x${h} (is ${image.width}x${image.height}); using the placeholder`);
          return e;
        }
        return { ...e, image };
      } catch (err) {
        console.warn(`art: ${String(err)}; using the placeholder`);
        return e;
      }
    }),
  );
}

/**
 * @param {{ key: string, rows: string[], anchor: [number, number] }[]} [entries]
 * @param {Map<string, ArtSource>} [overrides] the real art (P11.5), by logical name
 * @param {{ tallestFirst?: boolean }} [opts] tallestFirst: pack the real art tallest first (gfx W1), by the
 *   skyline (skylinePlaces) when that keeps it on one 2048×1024 atlas
 * @returns {Promise<import('./assetManager.js').BuiltBundle>}
 */
export async function buildPlaceholderPack(entries = placeholderEntries(), overrides = new Map(), { tallestFirst = false } = {}) {
  const all = await withOverrides(entries, overrides);
  // The placeholders and the real art are packed apart: the real art's atlas has 2 pixels per unit.
  const plain = all.filter((e) => !e.image);
  const real = tallestFirst ? tallestFirstOrder(all.filter((e) => e.image)) : all.filter((e) => e.image);
  const packs = [packAtlas(plain, atlasSizeFor(plain), 1)];
  const sky = tallestFirst && real.length ? skylinePlaces(byHeightThenWidth(real), ATLAS_MAX.width) : null;
  if (sky && sky.used <= ATLAS_MAX.height) packs.push(packAtlas(sky.entries, { width: ATLAS_MAX.width, height: potHeight(sky.used, ATLAS_MAX.width) }, ART_SCALE, sky.places));
  else if (real.length) for (const part of splitForAtlas(real)) packs.push(packAtlas(part, atlasSizeFor(part), ART_SCALE));
  return mergePacks(packs);
}

/** @param {import('./assetManager.js').BuiltBundle[]} packs @returns {import('./assetManager.js').BuiltBundle} */
function mergePacks(packs) {
  if (packs.length === 1) return packs[0];
  return {
    textures: new Map(packs.flatMap((p) => [...p.textures])),
    meta: new Map(packs.flatMap((p) => [...p.meta])),
    destroy() {
      for (const p of packs) p.destroy();
    },
  };
}

/**
 * @param {{ key: string, rows: string[], anchor: [number, number], image?: HTMLImageElement | HTMLCanvasElement }[]} entries
 * @param {{ width: number, height: number }} atlasSize from atlasSizeFor
 * @param {number} resolution pixels per game pixel (1 for placeholders, ART_SCALE for the real art)
 * @param {{ x: number, y: number }[]} [places] where each entry goes (skylinePlaces); else shelves
 * @returns {import('./assetManager.js').BuiltBundle}
 */
function packAtlas(entries, atlasSize, resolution, places) {
  const { width: ATLAS_W, height: ATLAS_H } = atlasSize;
  const PAD = 1;
  const canvas = document.createElement('canvas');
  canvas.width = ATLAS_W;
  canvas.height = ATLAS_H;
  const ctx = /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d'));

  /** @type {Map<string, { x: number, y: number, w: number, h: number }>} */
  const rects = new Map();
  let x = 0;
  let y = 0;
  let shelf = 0;
  for (const [i, e] of entries.entries()) {
    const { w, h } = sizeOf(e);
    if (places) {
      ({ x, y } = places[i]);
      shelf = 0;
    } else if (x + w > ATLAS_W) {
      x = 0;
      y += shelf + PAD;
      shelf = 0;
    }
    if (y + h > ATLAS_H) throw new Error('Placeholder atlas is full');
    if (e.image) {
      ctx.drawImage(e.image, x, y);
      rects.set(e.key, { x, y, w, h });
      x += w + PAD;
      shelf = Math.max(shelf, h);
      continue;
    }
    for (let py = 0; py < h; py++) {
      for (let px = 0; px < w; px++) {
        const c = e.rows[py][px];
        if (c === '.') continue;
        const color = PALETTE[/** @type {keyof typeof PALETTE} */ (c)];
        if (!color) throw new Error(`Unknown palette key "${c}" in ${e.key}`);
        ctx.fillStyle = color;
        ctx.fillRect(x + px, y + py, 1, 1);
      }
    }
    rects.set(e.key, { x, y, w, h });
    x += w + PAD;
    shelf = Math.max(shelf, h);
  }

  const base = Texture.from(canvas);
  base.source.scaleMode = 'nearest';
  // Frames are given in game pixels (the source's size divided by its resolution).
  if (resolution !== 1) base.source.resolution = resolution;
  const k = 1 / resolution;
  /** @type {Map<string, Texture>} */
  const textures = new Map();
  /** @type {Map<string, import('./assetManager.js').SpriteMeta>} */
  const meta = new Map();
  for (const e of entries) {
    const r = /** @type {{ x: number, y: number, w: number, h: number }} */ (rects.get(e.key));
    textures.set(e.key, new Texture({ source: base.source, frame: new Rectangle(r.x * k, r.y * k, r.w * k, r.h * k) }));
    meta.set(e.key, { anchor: e.anchor });
  }
  return {
    textures,
    meta,
    destroy() {
      for (const t of textures.values()) t.destroy(false);
      base.destroy(true);
    },
  };
}
