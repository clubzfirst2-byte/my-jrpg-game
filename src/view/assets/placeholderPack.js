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
import { v3RegionOf } from './artV3.js';

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
 * @param {{ mirror?: MirrorOptions }} [opts] graphics v3 (buildPlaceholderPack)
 */
export function buildRegionPack(name, overrides, keep, opts = {}) {
  const entries = [...REGION_ENTRIES[name](), ...releaseBossEntries(name, overrides), ...releaseTerrainEntries(name, overrides), ...releaseV3RegionEntries(name, overrides)];
  return buildPlaceholderPack(keep ? entries.filter(keep) : entries, overrides, opts);
}

/**
 * Graphics v3 (artV3.js): the new kinds of v3 art (names with ".v3.": the plains' 4×4 grass picture, its
 * trees, flowers and the stone house) get a slot in their region's bundle only when such art is given,
 * so they are loaded and released with the region (STYLE.md 10.1 (1)). Ground tiles keep the 16 px grid.
 * @param {string} region bundle name @param {Map<string, ArtSource>} [overrides] (only the names are read)
 */
export function releaseV3RegionEntries(region, overrides) {
  if (!overrides?.size) return [];
  return [...overrides.keys()]
    .filter((k) => v3RegionOf(k) === region)
    .sort()
    .map((key) => (/\.v3\.\d\d$/.test(key) ? { key, rows: Array(16).fill('.'.repeat(16)), anchor: TOP_LEFT } : { key, rows: ['.'], anchor: FEET }));
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
 * where the frame sits on it, in its pixels. `density`: art px per game px when it is not ART_SCALE
 * (graphics v3: 4, artV3.js).
 * @typedef {{ sheet: CanvasImageSource | SheetRef, x: number, y: number, w: number, h: number, density?: number }} SheetFrame
 */
/**
 * Where a sprite's art comes from: its own PNG's URL, its place on a packed sheet, or (graphics v3 in
 * the dev server) its PNG's URL with its density.
 * @typedef {string | SheetFrame | { url: string, density: number }} ArtSource
 */

/** Art pixels per game pixel of an art source (ART_SCALE unless it says otherwise). @param {ArtSource} src */
export const densityOf = (src) => (typeof src === 'string' ? ART_SCALE : (src.density ?? ART_SCALE));

/**
 * Copies a frame off its sheet into its own canvas, pixel for pixel, so it is drawn exactly as its
 * own PNG would be. @param {SheetFrame} f @param {CanvasImageSource} [sheet] the sheet's image (a SheetRef's, acquired)
 * @returns {HTMLCanvasElement}
 */
export function cutSheetFrame(f, sheet = /** @type {CanvasImageSource} */ (f.sheet instanceof SheetRef ? f.sheet.image : f.sheet)) {
  const canvas = document.createElement('canvas');
  canvas.width = f.w;
  canvas.height = f.h;
  const ctx = /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d'));
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(sheet, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
  return canvas;
}

/**
 * Graphics v3 (memory, STYLE.md 10.1 (6)): a packed release sheet whose decoded image is kept only while
 * a bundle is being cut from it (acquireSheet / releaseSheet), and loaded again from its URL (the
 * browser's cache) the next time one is. It answers `src` / `naturalWidth` / `naturalHeight` like the
 * image did (the menus' icons point into the sheet by URL: objectsArt.iconBackground).
 */
export class SheetRef {
  /** @param {HTMLImageElement} image */
  constructor(image) {
    this.src = image.src;
    this.naturalWidth = image.naturalWidth;
    this.naturalHeight = image.naturalHeight;
    /** @type {HTMLImageElement | null} */
    this.image = image;
    /** @type {Promise<HTMLImageElement> | null} */
    this.loading = null;
    this.users = 0;
  }
}

/** The image to cut from (a SheetRef's, loaded again if it was let go; one more user). @param {CanvasImageSource | SheetRef} sheet @returns {Promise<CanvasImageSource>} */
export async function acquireSheet(sheet) {
  if (!(sheet instanceof SheetRef)) return sheet;
  sheet.users++;
  if (sheet.image) return sheet.image;
  sheet.loading ??= loadImage(sheet.src).finally(() => {
    sheet.loading = null;
  });
  const img = await sheet.loading;
  if (sheet.users > 0) sheet.image = img;
  return img;
}

/** One user fewer; with none left, a SheetRef lets its decoded image go. @param {CanvasImageSource | SheetRef} sheet */
export function releaseSheet(sheet) {
  if (!(sheet instanceof SheetRef)) return;
  sheet.users = Math.max(0, sheet.users - 1);
  if (sheet.users === 0) sheet.image = null;
}

/**
 * P11.5: puts the real art (src/art/<name>.png) in place of the placeholder where there is one.
 * A tile of the wrong size is left as the placeholder (it would not fit the grid) and reported.
 * @param {{ key: string, rows: string[], anchor: [number, number] }[]} entries
 * @param {Map<string, ArtSource>} overrides logical name → PNG URL (artOverrides.js) or sheet frame
 * @returns {Promise<{ key: string, rows: string[], anchor: [number, number], image?: HTMLImageElement | HTMLCanvasElement, density?: number }[]>}
 */
export async function withOverrides(entries, overrides) {
  if (overrides.size === 0) return entries;
  return Promise.all(
    entries.map(async (e) => {
      const url = overrides.get(e.key);
      if (!url) return e;
      try {
        let image;
        if (typeof url === 'string') image = await loadImage(url);
        else if ('url' in url) image = await loadImage(url.url);
        else {
          const sheet = await acquireSheet(url.sheet);
          try {
            image = cutSheetFrame(url, sheet);
          } finally {
            releaseSheet(url.sheet);
          }
        }
        const density = densityOf(url);
        const [w, h] = [e.rows[0].length * density, e.rows.length * density];
        if (mustKeepSize(e.anchor) && (image.width !== w || image.height !== h)) {
          console.warn(`art: ${e.key}.png must be ${w}x${h} (is ${image.width}x${image.height}); using the placeholder`);
          return e;
        }
        return density === ART_SCALE ? { ...e, image } : { ...e, image, density };
      } catch (err) {
        console.warn(`art: ${String(err)}; using the placeholder`);
        return e;
      }
    }),
  );
}

/**
 * Graphics v3 (artV3.js, memory: STYLE.md 10.1 (3)): the pack options that mirror left-facing frames
 * instead of keeping them. `same(left, right)` tells whether a left frame is its right frame mirrored,
 * pixel for pixel (main.js compares on a canvas).
 * @typedef {{ same: (left: CanvasImageSource & { width: number, height: number }, right: CanvasImageSource & { width: number, height: number }) => boolean }} MirrorOptions
 */

/**
 * Graphics v3: which left-facing frames are drawn as their right frame mirrored (left out of the atlas):
 * those whose right frame is in the same pack, drawn from the real art, and either finer (a v3 right
 * frame wins over a v1 left one, so a direction never shows the old art beside the new) or the very
 * same picture mirrored. Pure apart from `same`.
 * @template {{ key: string, image?: any, density?: number }} E
 * @param {E[]} all @param {MirrorOptions} mirror
 * @returns {Map<string, string>} left key → right key
 */
export function mirroredFrames(all, mirror) {
  const byKey = new Map(all.map((e) => [e.key, e]));
  /** @type {Map<string, string>} */
  const out = new Map();
  for (const e of all) {
    if (!e.image || !e.key.includes('.left.')) continue;
    const right = byKey.get(e.key.replace('.left.', '.right.'));
    if (!right?.image) continue;
    const dl = e.density ?? ART_SCALE;
    const dr = right.density ?? ART_SCALE;
    if (dr > dl || (dr === dl && right.image.width === e.image.width && right.image.height === e.image.height && mirror.same(e.image, right.image))) out.set(e.key, right.key);
  }
  return out;
}

/**
 * @param {{ key: string, rows: string[], anchor: [number, number] }[]} [entries]
 * @param {Map<string, ArtSource>} [overrides] the real art (P11.5), by logical name
 * @param {{ tallestFirst?: boolean, mirror?: MirrorOptions }} [opts] tallestFirst: pack the real art
 *   tallest first (gfx W1); mirror: graphics v3, left frames drawn as their right frames mirrored
 * @returns {Promise<import('./assetManager.js').BuiltBundle>}
 */
export async function buildPlaceholderPack(entries = placeholderEntries(), overrides = new Map(), { tallestFirst = false, mirror } = {}) {
  let all = await withOverrides(entries, overrides);
  const mirrored = mirror ? mirroredFrames(all, mirror) : new Map();
  if (mirrored.size) all = all.filter((e) => !mirrored.has(e.key));
  // The placeholders and the real art are packed apart: the real art's atlas has 2 pixels per unit
  // (graphics v3: and the v3 art's, 4, on an atlas of its own; artV3.js).
  const plain = all.filter((e) => !e.image);
  const packs = [packAtlas(plain, atlasSizeFor(plain), 1)];
  const densities = [...new Set(all.filter((e) => e.image).map((e) => e.density ?? ART_SCALE))].sort((a, b) => a - b);
  for (const d of densities) {
    const of = all.filter((e) => e.image && (e.density ?? ART_SCALE) === d);
    const real = tallestFirst ? tallestFirstOrder(of) : of;
    packs.push(packAtlas(real, atlasSizeFor(real), d));
  }
  const pack = mergePacks(packs);
  // a mirrored left frame: its right frame's texture, flipped by the view (SpriteMeta.flipX)
  for (const [left, right] of mirrored) {
    const t = pack.textures.get(right);
    const m = pack.meta.get(right);
    if (!t || !m) continue;
    pack.textures.set(left, t);
    pack.meta.set(left, { anchor: [1 - m.anchor[0], m.anchor[1]], flipX: true });
  }
  return pack;
}

/** @param {import('./assetManager.js').BuiltBundle[]} packs @returns {import('./assetManager.js').BuiltBundle} */
function mergePacks(packs) {
  if (packs.length === 1) return packs[0];
  return {
    textures: new Map(packs.flatMap((p) => [...p.textures])),
    meta: new Map(packs.flatMap((p) => [...p.meta])),
    canvases: packs.flatMap((p) => p.canvases ?? []),
    destroy() {
      for (const p of packs) p.destroy();
    },
  };
}

/**
 * @param {{ key: string, rows: string[], anchor: [number, number], image?: HTMLImageElement | HTMLCanvasElement }[]} entries
 * @param {{ width: number, height: number }} atlasSize from atlasSizeFor
 * @param {number} resolution pixels per game pixel (1 for placeholders, ART_SCALE for the real art)
 * @returns {import('./assetManager.js').BuiltBundle}
 */
function packAtlas(entries, atlasSize, resolution) {
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
  for (const e of entries) {
    const { w, h } = sizeOf(e);
    if (x + w > ATLAS_W) {
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
    canvases: [{ canvas, source: base.source }],
    destroy() {
      for (const t of textures.values()) t.destroy(false);
      base.destroy(true);
    },
  };
}
