import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD, stitchWorld, outdoorAt, outdoorId, regionAt } from '../../src/game/world/world.js';
import { ISLAND } from '../../src/game/world/maps/island.js';
import { REGIONS } from '../../src/game/world/maps/regions.js';
import { parseMap } from '../../src/game/world/tilemap.js';
import { applyProgress, emptyProgress, respawnPoint, tileFeet } from '../../src/game/world/features.js';
import { computeWorldDiff } from '../../src/game/world/worldDiff.js';
import { travelTo, travelBlocked, mapModel, touchSurveys } from '../../src/game/world/survey.js';
import { makeEnvelope, chooseSave, migrate, fnv1a, SCHEMA_VERSION, MIGRATIONS } from '../../src/save/saveFormat.js';

// Volume phase 1, the foundation: more than two columns of regions, survey stones and the map,
// travel between record stones, and save format 4 (format 3 saves — not cleared, half way, cleared —
// load unchanged).

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false, ability: false };

describe('the world takes any number of columns', () => {
  // The world as it was: without the terrace (and without the plains' pass to it).
  const OLD = REGIONS.filter((r) => r.id !== 'terrace').map((r) => ({ ...r, passes: (r.passes ?? []).filter((p) => p.to.region !== 'terrace') }));
  const two = stitchWorld(ISLAND, OLD);

  it('the world of two columns is inside the wider world, tile for tile, at the same coordinates', () => {
    const w = two.ground[0].length;
    expect(w).toBe(256);
    expect(WORLD.ground.length).toBe(two.ground.length);
    expect(WORLD.ground.map((r) => r.slice(0, w))).toEqual(two.ground);
    expect(WORLD.height.map((r) => r.slice(0, w))).toEqual(two.height);
  });

  it('everything the old regions place keeps its coordinates (chests, stones, landmarks, items, people, doorways, objects)', () => {
    for (const key of ['chests', 'checkpoints', 'landmarks', 'pickups', 'npcs', 'envObjects', 'enemies', 'bosses', 'switches', 'areas', 'campfires']) {
      expect(WORLD[key].slice(0, two[key].length), key).toEqual(two[key]);
    }
    // (doorways are listed regions first, passes after: compared one by one)
    for (const w of two.warps) expect(WORLD.warps.find((x) => x.id === w.id), w.id).toEqual(w);
    expect(WORLD.finalBoss).toEqual(two.finalBoss);
    expect(WORLD.outdoors.slice(0, 2)).toEqual(two.outdoors);
    expect(WORLD.regions.slice(0, 6)).toEqual(two.regions);
  });

  it('a region may sit in column 3, 4, ...: each column has its own outdoors, on chunk boundaries', () => {
    const far = { ...REGIONS.find((r) => r.id === 'terrace'), id: 'far', col: 4, passes: [] };
    const w = stitchWorld(ISLAND, [...REGIONS, far]);
    expect(w.ground[0].length).toBe(128 * 5);
    expect(w.regions.find((r) => r.id === 'far')).toMatchObject({ tx: 512, ty: 0 });
    // Column 3 is empty: filled with nothing, and it has no outdoors.
    expect(w.outdoors.map((o) => [o.id, o.tx])).toEqual([['outdoor', 0], ['outdoor-east', 128], ['outdoor-col2', 256], ['outdoor-col4', 512]]);
    expect(outdoorId(0)).toBe('outdoor');
    expect(outdoorId(1)).toBe('outdoor-east');
    const map = parseMap(w);
    expect(map.width).toBe(640);
    expect(outdoorAt(w.outdoors, 400, 10)).toBe(null);
    expect(outdoorAt(w.outdoors, 520, 10)?.id).toBe('outdoor-col4');
    expect(new Set(w.ground.map((r) => r.slice(384, 512))).size).toBe(1);
  });

  it('a second region in a new column stacks below the first; a bad column is refused', () => {
    const t = REGIONS.find((r) => r.id === 'terrace');
    const w = stitchWorld(ISLAND, [...REGIONS, { ...t, id: 'below', passes: [] }]);
    expect(w.regions.find((r) => r.id === 'below')).toMatchObject({ tx: 256, ty: 96 });
    expect(() => stitchWorld(ISLAND, [{ ...t, col: -1 }])).toThrow(/column/);
    expect(() => stitchWorld(ISLAND, [{ ...t, col: 1.5 }])).toThrow(/column/);
  });

  it('the camera shows the terrace as its own outdoors', () => {
    const r = WORLD.regions.find((x) => x.id === 'terrace');
    expect(outdoorAt(WORLD.outdoors, r.tx + 10, r.ty + 46)).toMatchObject({ id: 'outdoor-col2', tx: 256, tw: 96, th: 96 });
  });
});

describe('survey stones and the map', () => {
  it('every region has one survey stone, on ground that can be stood beside', () => {
    expect(WORLD.surveys.map((s) => s.region).sort()).toEqual(WORLD.regions.map((r) => r.id).sort());
    const s = createGameState(WORLD);
    for (const sv of WORLD.surveys) {
      const r = regionAt(WORLD.regions, sv.tx, sv.ty);
      expect(r?.id, sv.id).toBe(sv.region);
      expect(s.map.solid[sv.ty * s.map.width + sv.tx], sv.id).toBe(1);
      expect(s.map.solid[(sv.ty + 1) * s.map.width + sv.tx], `${sv.id}: the tile south of it`).toBe(0);
    }
  });

  it('touching a survey stone draws its region (once), asks for a save, and tells the view', () => {
    const s = createGameState(WORLD);
    s.enemies = [];
    const sv = WORLD.surveys.find((x) => x.region === 'plains');
    const f = tileFeet(s.map, sv.tx, sv.ty + 1);
    Object.assign(s.player, { x: f.x, y: f.y, prevX: f.x, prevY: f.y });
    s.player.z = s.player.groundZ = s.map.elev[(sv.ty + 1) * s.map.width + sv.tx];
    s.saveRequested = false;
    stepGame(s, none);
    expect(s.progress.surveyed).toEqual(['plains']);
    expect(s.saveRequested).toBe(true);
    expect(s.events.filter((e) => e.type === 'survey').map((e) => e.id)).toEqual(['plains']);
    for (let i = 0; i < 30; i++) stepGame(s, none);
    expect(s.progress.surveyed).toEqual(['plains']);
    expect(s.events.filter((e) => e.type === 'survey')).toHaveLength(1);
  });

  it('far from a stone, or on another level, nothing is read', () => {
    const s = createGameState(WORLD);
    stepGame(s, none);
    expect(s.progress.surveyed).toEqual([]);
    const sv = WORLD.surveys.find((x) => x.region === 'terrace');
    const f = tileFeet(s.map, sv.tx, sv.ty + 1);
    Object.assign(s.player, { x: f.x, y: f.y, z: 0, groundZ: 0, grounded: true });
    touchSurveys(s); // (below the knoll, at the stone's place on the map)
    expect(s.progress.surveyed).toEqual([]);
  });

  it('the map model: unsurveyed regions show only the record stones touched; surveyed ones their landmarks too', () => {
    const s = createGameState(WORLD);
    s.progress.checkpoints = ['beach', 'plains', 'source'];
    s.progress.checkpoint = 'plains';
    s.progress.landmarks = ['village', 'windmill', 'mesa'];
    s.progress.surveyed = ['plains'];
    const m = mapModel(s);
    expect(m.regions.map((r) => r.id)).toEqual(['island', 'plains', 'desert', 'mountains', 'forest', 'lake', 'terrace']);
    const by = Object.fromEntries(m.regions.map((r) => [r.id, r]));
    expect(by.plains.surveyed).toBe(true);
    expect(by.plains.landmarks.map((l) => l.id)).toEqual(['village', 'windmill']);
    expect(by.plains.checkpoints).toEqual([expect.objectContaining({ id: 'plains', active: true, outdoors: true })]);
    expect(by.desert.surveyed).toBe(false);
    expect(by.desert.landmarks).toEqual([]); // found, but the desert is not drawn yet
    // The source's record stone is in a room of the desert's strip: listed, without a place on the drawing.
    expect(by.desert.checkpoints).toEqual([expect.objectContaining({ id: 'source', outdoors: false })]);
    expect(by.island.checkpoints.map((c) => c.id)).toEqual(['beach']);
    expect(by.island.current).toBe(true);
    expect(m.player.region).toBe('island');
    expect(by.terrace.tw).toBe(96);
    expect(m.blocked).toBe(null);
  });
});

describe('travel between record stones', () => {
  const ready = () => {
    const s = createGameState(WORLD);
    s.enemies = s.enemies.filter((e) => e.boss);
    s.enemySpawns = [];
    s.progress.checkpoints = ['beach', 'forest', 'terrace_east'];
    s.progress.checkpoint = 'beach';
    stepGame(s, none);
    return s;
  };

  it('moves the player beside a touched stone, makes it the place to come back to life, and asks for a save', () => {
    const s = ready();
    s.saveRequested = false;
    expect(travelTo(s, 'terrace_east')).toBe(true);
    const c = WORLD.checkpoints.find((x) => x.id === 'terrace_east');
    expect(Math.floor(s.player.x / 16)).toBe(c.tx);
    expect(Math.floor(s.player.y / 16)).toBe(c.ty + 1);
    expect(s.player.grounded).toBe(true);
    expect(s.progress.checkpoint).toBe('terrace_east');
    expect(respawnPoint(s)).toEqual(tileFeet(s.map, c.tx, c.ty + 1));
    expect(s.saveRequested).toBe(true);
    expect(s.events.at(-1)).toMatchObject({ type: 'travel', id: 'terrace_east' });
    for (let i = 0; i < 120; i++) stepGame(s, none);
    expect(s.player.dead).toBe(false);
    expect(regionAt(s.regions, Math.floor(s.player.x / 16), Math.floor(s.player.y / 16)).id).toBe('terrace');
  });

  it('never to a stone not touched yet, or one the world does not have', () => {
    const s = ready();
    const at = { x: s.player.x, y: s.player.y };
    expect(travelTo(s, 'lake')).toBe(false);
    expect(travelTo(s, 'nowhere')).toBe(false);
    expect({ x: s.player.x, y: s.player.y }).toEqual(at);
    expect(s.progress.checkpoint).toBe('beach');
  });

  it('not in the air, in water, in a conversation, while down, or with a core awake', () => {
    const s = ready();
    s.player.grounded = false;
    expect(travelBlocked(s)).toBe('air');
    s.player.grounded = true;
    s.player.swimming = true;
    expect(travelBlocked(s)).toBe('air');
    s.player.swimming = false;
    s.dialogue = { id: 'x', npc: null, node: 'a', line: 0 };
    expect(travelBlocked(s)).toBe('busy');
    s.dialogue = null;
    s.player.dead = true;
    expect(travelBlocked(s)).toBe('dead');
    s.player.dead = false;
    const boss = s.enemies.find((e) => e.boss);
    boss.awake = true;
    expect(travelBlocked(s)).toBe('fight');
    expect(travelTo(s, 'forest')).toBe(false);
    boss.awake = false;
    expect(travelBlocked(s)).toBe(null);
    expect(travelTo(s, 'forest')).toBe(true);
  });
});

// ---- save format 4 ----
const checksumFor = (e) => fnv1a(JSON.stringify([e.schemaVersion, e.gameVersion, e.savedAt, e.seq, e.data]));
/** An envelope as v1.0 wrote it (format 3). */
const v3 = (data) => {
  const e = { ...makeEnvelope(data, '1.0.0', 12, 1_790_000_000_000), schemaVersion: 3 };
  e.checksum = checksumFor(e);
  return e;
};
/** Progress as v1.0 saved it: no `surveyed`. */
const v1Progress = (over) => {
  const { surveyed, ...rest } = emptyProgress();
  void surveyed;
  return JSON.parse(JSON.stringify({ ...rest, worldMs: 20 * 60_000, worldDiff: {}, ...over }));
};
const inv = (money, extra = {}) => ({ money, items: { arrow: 14, red_berry: 2, ...extra }, weapons: [{ id: 'travel_sword', dur: 21, lvl: 1 }], bows: [{ id: 'wood_bow', dur: 17, lvl: 0 }], equip: { weapon: 0, bow: 0, head: null, body: 'bark_vest', legs: null }, recipes: ['grilled_meat'] });
const V1_SAVES = {
  'not cleared, early (the island only, the princess not met)': v1Progress({
    openedChests: ['ledge'], checkpoints: ['beach', 'hill'], checkpoint: 'hill', landmarks: ['tower'], maxHp: 12, inv: inv(40), abilities: ['light'], ability: 'light', gates: ['trial_light'],
  }),
  'half way (two cores purified, a quest running, world differences)': v1Progress({
    openedChests: ['ledge', 'camp', 'windmill', 'trial_twin'], checkpoints: ['beach', 'hill', 'plains', 'forest', 'mountains'], checkpoint: 'forest',
    landmarks: ['tower', 'village', 'windmill', 'great_tree', 'core_forest', 'core_mountains'], maxHp: 20, maxStamina: 120, inv: inv(520, { star_shard: 1 }),
    abilities: ['light', 'telekinesis', 'vine'], ability: 'vine', gates: ['trial_light', 'trial_twin', 'vault'],
    flags: { princess_met: true, elder_met: true }, quests: { star_ring_call: 'active', lost_charm: 'done' }, bosses: ['core_forest', 'core_mountains'],
    picked: { plains0: 15 * 60_000 },
  }),
  'cleared (the ending seen)': v1Progress({
    openedChests: ['ledge', 'camp', 'windmill', 'mesa', 'summit', 'thicket', 'far_islet', 'mine'], checkpoints: ['beach', 'hill', 'camp', 'plains', 'desert', 'mountains', 'forest', 'lake', 'source'], checkpoint: 'plains',
    landmarks: WORLD.landmarks.filter((l) => !l.id.startsWith('terrace') && !['trial_vane', 'trial_rise', 'trial_winds'].includes(l.id)).map((l) => l.id), maxHp: 24, maxStamina: 140, inv: inv(1480),
    abilities: ['light', 'telekinesis', 'vine', 'resonance'], ability: 'resonance', gates: ['trial_light', 'trial_twin', 'trial_dark', 'trial_water', 'vault', 'mine_1', 'mine_2', 'mine_3'],
    flags: { princess_met: true, elder_met: true, source_open: true, source_purified: true, ending_seen: true }, quests: { star_ring_call: 'done', source_of_murk: 'done', lost_charm: 'done' },
    bosses: ['core_forest', 'core_mountains', 'core_desert', 'core_lake'],
  }),
};
function boot(envelope) {
  const choice = chooseSave(envelope, null);
  expect(choice.status).toBe('ok');
  const s = createGameState(WORLD);
  applyProgress(s, choice.data);
  const at = respawnPoint(s);
  Object.assign(s.player, { x: at.x, y: at.y, prevX: at.x, prevY: at.y });
  for (let i = 0; i < 120; i++) stepGame(s, none);
  return { s, data: choice.data };
}

describe(`save format ${SCHEMA_VERSION}: v1.0 saves (format 3) load unchanged`, () => {
  it('the format is 4, and the step from 3 only adds an empty `surveyed`', () => {
    expect(SCHEMA_VERSION).toBe(4);
    const before = V1_SAVES['half way (two cores purified, a quest running, world differences)'];
    const after = MIGRATIONS[3](JSON.parse(JSON.stringify(before)));
    expect(after).toEqual({ ...before, surveyed: [] });
    // (a format 4 save that is run through it again keeps what it has)
    expect(MIGRATIONS[3]({ ...before, surveyed: ['plains'] }).surveyed).toEqual(['plains']);
  });

  for (const [name, data] of Object.entries(V1_SAVES)) {
    it(`${name}: every field comes back, the game runs on, and nothing new is set`, () => {
      const { s, data: loaded } = boot(v3(data));
      expect(loaded).toEqual({ ...data, surveyed: [] });
      const pr = s.progress;
      for (const key of ['openedChests', 'checkpoints', 'checkpoint', 'maxHp', 'gates', 'abilities', 'ability', 'maxStamina', 'flags', 'quests', 'bosses']) expect(pr[key], key).toEqual(data[key]);
      expect(pr.landmarks).toEqual(expect.arrayContaining(data.landmarks)); // (standing at the stone for two seconds may show one more)
      expect(pr.inv.money).toBe(data.inv.money);
      expect(pr.inv.weapons).toEqual(data.inv.weapons);
      expect(pr.surveyed).toEqual([]);
      expect(s.player.dead).toBe(false);
      expect(s.player.maxHp).toBe(data.maxHp);
      // Back at the same record stone as before.
      const c = WORLD.checkpoints.find((x) => x.id === data.checkpoint);
      expect(respawnPoint(s)).toEqual(tileFeet(s.map, c.tx, c.ty + 1));
      // Purified cores stay gone; the others wait.
      expect(s.enemies.filter((e) => e.boss).map((e) => e.bossId).sort()).toEqual(WORLD.bosses.map((b) => b.id).filter((id) => !data.bosses.includes(id)).sort());
      // Opened doors stay open.
      for (const link of data.gates) expect(s.map.objects.filter((o) => o.type === 'door' && o.link === link).every((o) => o.gone), link).toBe(true);
      // Every id the save names still exists.
      const ids = { openedChests: WORLD.chests, checkpoints: WORLD.checkpoints, landmarks: WORLD.landmarks, bosses: WORLD.bosses };
      for (const [key, list] of Object.entries(ids)) for (const id of data[key]) expect(list.some((x) => x.id === id), `${key} ${id}`).toBe(true);
    });

    it(`${name}: saved again it is format 4, and loads to the same progress`, () => {
      const { s } = boot(v3(data));
      const again = JSON.parse(JSON.stringify({ ...s.progress, worldMs: Math.round(s.env.now), worldDiff: computeWorldDiff(s) }));
      const e = makeEnvelope(again, '1.1.0', 13, 1_800_000_000_000);
      expect(e.schemaVersion).toBe(4);
      const { s: t } = boot(e);
      for (const key of ['openedChests', 'checkpoints', 'checkpoint', 'landmarks', 'gates', 'abilities', 'flags', 'quests', 'bosses', 'surveyed']) expect(t.progress[key], key).toEqual(s.progress[key]);
    });

    it(`${name}: the terrace is open to it — travel to a touched stone, then walk through the pass`, () => {
      const { s } = boot(v3(data));
      s.enemies = [];
      s.enemySpawns = [];
      if (data.checkpoints.includes('plains')) expect(travelTo(s, 'plains')).toBe(true);
      // (an early save has not reached the plains: the pass itself has no condition)
      const w = WORLD.warps.find((x) => x.id === 'pass-terrace');
      expect(w.if).toBeUndefined();
      const f = tileFeet(s.map, w.tx - 3, w.ty);
      Object.assign(s.player, { x: f.x, y: f.y, prevX: f.x, prevY: f.y, z: 0, groundZ: 0, grounded: true });
      for (let i = 0; i < 180 && regionAt(s.regions, Math.floor(s.player.x / 16), Math.floor(s.player.y / 16))?.id !== 'terrace'; i++) stepGame(s, { ...none, moveX: 1 });
      expect(regionAt(s.regions, Math.floor(s.player.x / 16), Math.floor(s.player.y / 16))?.id).toBe('terrace');
      // The story stays as it was (no flag set or cleared by entering).
      expect(s.progress.flags).toEqual(data.flags);
      expect(s.progress.quests).toEqual(data.quests);
    });
  }

  it('a world difference of a v1.0 save (a burnt tree of the plains, a moved crate) is applied as before', () => {
    const src = createGameState(WORLD);
    const tree = src.map.objects.find((o) => o.type === 'tree' && o.ty > 80 && o.tx < 96);
    tree.type = 'stump';
    const diff = JSON.parse(JSON.stringify(computeWorldDiff(src)));
    const { s } = boot(v3(v1Progress({ worldDiff: diff })));
    expect(s.map.objects.find((o) => o.tx === tree.tx && o.ty === tree.ty).type).toBe('stump');
    expect(s.map.objects.filter((o) => o.type === 'stump')).toHaveLength(1);
  });

  it('a format 4 save is refused by a game that only knows format 3 (as v1.0 does: "newer")', () => {
    const e = makeEnvelope({ ...emptyProgress(), surveyed: ['plains'] }, '1.1.0', 2, 0);
    expect(e.schemaVersion).toBe(4);
    // v1.0's rule (saveFormat.js migrate): a schema above its own is 'newer', never read.
    const v1Migrate = (env) => (env.schemaVersion > 3 ? { ok: false, reason: 'newer' } : { ok: true });
    expect(v1Migrate(e)).toEqual({ ok: false, reason: 'newer' });
    const newer = { ...e, schemaVersion: SCHEMA_VERSION + 1 };
    newer.checksum = checksumFor(newer);
    expect(migrate(newer)).toEqual({ ok: false, reason: 'newer' });
  });
});
