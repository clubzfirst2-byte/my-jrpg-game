import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { applyProgress, emptyProgress, respawnPoint } from '../../src/game/world/features.js';
import { computeWorldDiff } from '../../src/game/world/worldDiff.js';
import { makeEnvelope, chooseSave, migrate, fnv1a, SCHEMA_VERSION } from '../../src/save/saveFormat.js';
import { LEGACY_OBJECTS } from '../../src/save/legacyObjects.js';
import { countOf } from '../../src/game/items/inventory.js';
import LEGACY_IDS from '../fixtures/legacy-ids.json';

// P10.6 completion check (DESIGN.md roadmap): save compatibility. Saves from every version since
// saving began (P3.5) load into today's world: nothing they name has disappeared, old shapes are
// migrated, and the game runs on from them.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false, ability: false };

describe('nothing a save can name has gone missing', () => {
  const now = {
    chests: new Set(WORLD.chests.map((c) => c.id)),
    checkpoints: new Set(WORLD.checkpoints.map((c) => c.id)),
    landmarks: new Set(WORLD.landmarks.map((l) => l.id)),
    pickups: new Set(WORLD.pickups.map((p) => p.id)),
    links: new Set([...WORLD.envObjects.filter((o) => o.link).map((o) => o.link), ...(WORLD.switches ?? []).map((s) => s.link)]),
  };
  for (const [version, ids] of Object.entries(LEGACY_IDS)) {
    it(`${version}: chests, checkpoints, landmarks, items and doors still exist`, () => {
      for (const [kind, list] of Object.entries(ids)) {
        const missing = list.filter((id) => !now[kind].has(id));
        expect(missing, `${version} ${kind}`).toEqual([]);
      }
    });
  }
});

/** Loads a saved envelope the way the game does and runs a few seconds from it. */
function boot(envelope) {
  const choice = chooseSave(envelope, null);
  expect(choice.status).toBe('ok');
  const s = createGameState(WORLD);
  applyProgress(s, choice.data);
  // Back at the checkpoint, as つづきから does.
  const at = respawnPoint(s);
  Object.assign(s.player, { x: at.x, y: at.y, prevX: at.x, prevY: at.y });
  for (let i = 0; i < 120; i++) stepGame(s, none);
  expect(s.player.dead).toBe(false);
  return s;
}
const checksumFor = (e) => fnv1a(JSON.stringify([e.schemaVersion, e.gameVersion, e.savedAt, e.seq, e.data]));
/** An envelope as an older version wrote it: its schema, and a checksum over that. */
const old = (schemaVersion, data) => {
  const e = { ...makeEnvelope(data, '0.0.1', 3, 1_700_000_000_000), schemaVersion };
  e.checksum = checksumFor(e);
  return e;
};

describe('saves from every era load and play on', () => {
  it('P3.5-P5 (schema 1): chests, checkpoints, the vault door; treasures become money', () => {
    const s = boot(old(1, { openedChests: ['ledge', 'camp'], checkpoints: ['beach', 'hill'], checkpoint: 'hill', landmarks: ['tower', 'smoke'], treasures: 2, maxHp: 16, gates: ['vault'], worldMs: 9 * 60_000 }));
    expect(s.progress.openedChests).toEqual(['ledge', 'camp']);
    expect(s.progress.inv.money).toBeGreaterThanOrEqual(100);
    expect(s.player.maxHp).toBe(16);
    const cp = WORLD.checkpoints.find((c) => c.id === 'hill');
    expect(Math.abs(s.player.y - (cp.ty + 1) * 16) < 40).toBe(true);
    expect(s.map.objects.filter((o) => o.type === 'door' && o.link === 'vault').every((o) => o.gone)).toBe(true);
  });

  it('P6-P7 (schema 2): the bag, map items taken, abilities, trials opened', () => {
    const s = boot(old(2, {
      ...emptyProgress(),
      openedChests: ['cave', 'trial_light'],
      checkpoints: ['beach'],
      checkpoint: 'beach',
      inv: { money: 35, items: { mushroom: 3, arrow: 12 }, weapons: [{ id: 'wood_sword', dur: 20, lvl: 0 }, { id: 'ember_sword', dur: 9, lvl: 1 }], bows: [], equip: { weapon: 1, bow: -1, head: null, body: null, legs: null }, recipes: [] },
      picked: { mushroom0: 2 * 60_000, arrows1: 3 * 60_000 },
      abilities: ['light', 'telekinesis'],
      ability: 'light',
      gates: ['trial_light'],
      worldMs: 30 * 60_000,
    }));
    expect(countOf(s.progress.inv, 'mushroom')).toBe(3);
    expect(s.progress.inv.weapons[s.progress.inv.equip.weapon].id).toBe('ember_sword');
    expect(s.progress.abilities).toEqual(['light', 'telekinesis']);
    expect(s.map.objects.filter((o) => o.type === 'door' && o.link === 'trial_light').every((o) => o.gone)).toBe(true);
  });

  for (const era of ['p8', 'p9', 'p10']) {
    it(`${era.toUpperCase()} (schema 2, world differences by list index): a broken jar stays broken`, () => {
      const list = LEGACY_OBJECTS[era].split(' ');
      const k = list.findIndex((id) => id.startsWith('jar@'));
      const [tx, ty] = list[k].split('@')[1].split(',').map(Number);
      const chunk = `${Math.floor(tx / 32)},${Math.floor(ty / 32)}`;
      const s = boot(old(2, { ...emptyProgress(), flags: { elder_met: true }, quests: { lost_charm: 'active' }, worldDiff: { [chunk]: { [k]: { gone: true } } }, worldMs: 50 * 60_000 }));
      const jar = s.map.objects.find((o) => o.type === 'jar' && o.tx === tx && o.ty === ty);
      // Converted when the old lists agree, otherwise safely dropped — never a different object.
      expect(s.map.objects.filter((o) => o.gone && o !== jar)).toEqual([]);
      expect(s.progress.quests.lost_charm).toBe('active');
    });
  }

  it(`today's saves (schema ${SCHEMA_VERSION}): everything comes back exactly`, () => {
    const s = createGameState(WORLD);
    stepGame(s, none);
    s.progress.openedChests.push('summit');
    s.progress.checkpoints.push('lake');
    s.progress.checkpoint = 'lake';
    s.progress.bosses.push('core_forest');
    s.progress.gates.push('trial_twin');
    s.progress.quests.lost_charm = 'done';
    s.progress.inv.money = 777;
    const tree = s.map.objects.find((o) => o.type === 'tree' && o.tx > 128);
    tree.type = 'stump';
    const saved = JSON.parse(JSON.stringify({ ...s.progress, worldMs: Math.round(s.env.now), worldDiff: computeWorldDiff(s) }));
    const t = boot(makeEnvelope(saved, '0.0.1', 9, 1_800_000_000_000));
    expect(t.progress.openedChests).toEqual(s.progress.openedChests);
    expect(t.progress.bosses).toEqual(['core_forest']);
    expect(t.enemies.some((e) => e.bossId === 'core_forest')).toBe(false);
    expect(t.progress.inv.money).toBe(777);
    expect(t.map.objects.find((o) => o.tx === tree.tx && o.ty === tree.ty).type).toBe('stump');
    expect(t.map.objects.filter((o) => o.link === 'trial_twin').every((o) => o.gone)).toBe(true);
  });

  it('a save naming a checkpoint the world no longer has starts at the beginning instead', () => {
    const s = boot(old(2, { ...emptyProgress(), checkpoints: ['gone_forever'], checkpoint: 'gone_forever' }));
    expect(respawnPoint(s)).toEqual(s.map.spawn);
  });

  it('a save from a newer version than this one is refused, not misread', () => {
    const e = makeEnvelope(emptyProgress(), '9.9.9', 1, 0);
    const newer = { ...e, schemaVersion: SCHEMA_VERSION + 1 };
    newer.checksum = checksumFor(newer);
    expect(chooseSave(newer, null).status).toBe('newer');
    expect(migrate(newer).ok).toBe(false);
  });
});
