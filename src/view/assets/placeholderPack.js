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
} from './placeholderArt.js';

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
  for (const [key, rows] of Object.entries({ ...beastFrames(), ...archerFrames() })) entries.push({ key, rows, anchor: FEET });
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
  for (const [key, rows] of Object.entries(itemIcons())) entries.push({ key, rows, anchor: FEET });
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
    ...[1, 2, 3, 4, 5].flatMap((look) => Object.entries(villagerFrames(look)).map(([key, rows]) => ({ key, rows, anchor: FEET }))),
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
const bossFrames = (/** @type {'root' | 'frost' | 'sand' | 'storm'} */ kind) => [0, 1].map((f) => ({ key: `enemy.boss_${kind}.${f}`, rows: bossSprite(kind, f), anchor: FEET }));
for (const [region, kind] of /** @type {const} */ ([['region:forest', 'root'], ['region:mountains', 'frost'], ['region:desert', 'sand'], ['region:lake', 'storm']])) {
  const make = REGION_ENTRIES[region];
  REGION_ENTRIES[region] = () => [...make(), ...bossFrames(kind)];
}

/** @param {string} name */
export function buildRegionPack(name) {
  return buildPlaceholderPack(REGION_ENTRIES[name](), atlasSizeFor(REGION_ENTRIES[name]()));
}

/** The smallest square atlas (64 .. 1024) the entries fit in, with the same shelf packing. @param {{ rows: string[] }[]} entries */
export function atlasSizeFor(entries) {
  for (const size of [64, 128, 256, 512, 1024]) {
    let x = 0;
    let y = 0;
    let shelf = 0;
    let fits = true;
    for (const e of entries) {
      const w = e.rows[0].length;
      const h = e.rows.length;
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
    if (fits) return size;
  }
  throw new Error('Too many sprites for one atlas');
}

/**
 * @param {{ key: string, rows: string[], anchor: [number, number] }[]} [entries]
 * @param {number} [atlasSize]
 * @returns {import('./assetManager.js').BuiltBundle}
 */
export function buildPlaceholderPack(entries = placeholderEntries(), atlasSize = 256) {
  const ATLAS = atlasSize;
  const PAD = 1;
  const canvas = document.createElement('canvas');
  canvas.width = ATLAS;
  canvas.height = ATLAS;
  const ctx = /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d'));

  /** @type {Map<string, { x: number, y: number, w: number, h: number }>} */
  const rects = new Map();
  let x = 0;
  let y = 0;
  let shelf = 0;
  for (const e of entries) {
    const w = e.rows[0].length;
    const h = e.rows.length;
    if (x + w > ATLAS) {
      x = 0;
      y += shelf + PAD;
      shelf = 0;
    }
    if (y + h > ATLAS) throw new Error('Placeholder atlas is full');
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
  /** @type {Map<string, Texture>} */
  const textures = new Map();
  /** @type {Map<string, import('./assetManager.js').SpriteMeta>} */
  const meta = new Map();
  for (const e of entries) {
    const r = /** @type {{ x: number, y: number, w: number, h: number }} */ (rects.get(e.key));
    textures.set(e.key, new Texture({ source: base.source, frame: new Rectangle(r.x, r.y, r.w, r.h) }));
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
