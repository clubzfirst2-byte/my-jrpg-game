import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { tileFeet, areaAt, applyProgress, warpOpen } from '../../src/game/world/features.js';
import { COMBAT } from '../../src/game/entities/playerCombat.js';
import { FINAL_BOSS, SOURCE_PURIFIED, activeFinalBoss, resetSeats } from '../../src/game/entities/finalBoss.js';
import { activeBoss, PHASE2_WINDUP } from '../../src/game/entities/bosses.js';
import { lightSconce, unlightSconce, switchActive, lightSources } from '../../src/game/puzzles/switches.js';
import { slideCrate } from '../../src/game/puzzles/abilities.js';
import { hitEnemy } from '../../src/game/combat/damage.js';
import { countOf } from '../../src/game/items/inventory.js';
import { STEP_SEC } from '../../src/game/core/fixedStep.js';
import { sourceEntries, placeholderEntries, releaseEnemyEntries, atlasSizeFor, SOURCE_BUNDLE, SOURCE_REGIONS, REGION_ENTRIES } from '../../src/view/assets/placeholderPack.js';
import { readdirSync, readFileSync } from 'node:fs';
import { startDialogue, dialogueView, advance } from '../../src/game/npc/talk.js';
import { SOURCE_ACTIONS } from '../../src/view/assets/sourceArt.js';
import { sourceFrameKey } from '../../src/view/sourceView.js';

// v1.0 C5-C7 (docs/story/V1_STORY_PROPOSAL.md; C15 tests): the beach ring, the source's arena and
// the final boss 淀みの源 — invulnerable while inverted, four seats to wake, a stagger, three hits,
// purified for good.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false, ability: false };
const MS = STEP_SEC * 1000;
const SEATS = ['source-fire', 'source-light', 'source-weight', 'source-echo'];
const area = (id) => WORLD.areas.find((a) => a.id === id);
/** The arena's rows in the desert's own coordinates (tools/gen_world.py) → world rows. */
const OY = area('source_arena').ty - 36;
const at = (x, y) => ({ tx: x, ty: OY + y });
const run = (s, input, n) => {
  for (let i = 0; i < n; i++) stepGame(s, input);
};
function place(s, { tx, ty }, facing = 'up') {
  const f = tileFeet(s.map, tx, ty);
  const p = s.player;
  Object.assign(p, { x: f.x, y: f.y, prevX: f.x, prevY: f.y, vx: 0, vy: 0, knockMs: 0, swimming: false, climbing: false });
  p.z = p.prevZ = p.groundZ = s.map.elev[ty * s.map.width + tx];
  p.grounded = true;
  p.facing = facing;
  const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[facing];
  p.aimX = v[0];
  p.aimY = v[1];
}
/** A world with the player in the source's arena (tough enough to watch the whole fight). */
function arena(abilities = []) {
  const s = createGameState(WORLD);
  s.enemies = [];
  s.enemySpawns = [];
  s.progress.abilities = [...abilities];
  s.progress.ability = abilities[0] ?? null;
  s.player.maxHp = s.player.hp = 4000;
  place(s, at(104, 55));
  stepGame(s, none);
  expect(areaAt(s, s.player.x, s.player.y)?.id).toBe('source_arena');
  const b = s.enemies.find((e) => e.final);
  expect(b).toBeTruthy();
  place(s, at(104, 50)); // (away from the way out: a knock back must not carry the player out)
  return { s, b };
}
/** Full health, back at the usual spot (attacks knock the player around). */
const keepAlive = (s) => {
  s.player.hp = s.player.maxHp;
  s.player.dead = false;
  place(s, at(104, 50));
};
/** Steps with the player kept in place and alive. */
const hold = (s, n) => {
  for (let i = 0; i < n; i++) {
    keepAlive(s);
    stepGame(s, none);
  }
};
const shoot = (s) => {
  run(s, { ...none, bow: true }, Math.ceil((COMBAT.bowDrawMs / 1000) * 60) + 2);
  run(s, none, 60);
};
const swing = (s) => {
  stepGame(s, { ...none, attack: true });
  run(s, none, 40);
};
const useAbility = (s, id) => {
  s.progress.ability = id;
  s.abilityReadyAt = 0;
  stepGame(s, { ...none, ability: true });
  run(s, none, 2);
};
const objAt = (s, { tx, ty }) => s.env.objectAt.get(ty * s.map.width + tx);
const seatsOf = (b) => SEATS.filter((id) => b.seats[id]);

/** Wakes all four seats with their no-ability ways, the quick way (as the world would). */
function wakeAll(s) {
  lightSconce(s, objAt(s, at(100, 40))); // fire
  s.orb = { x: at(108, 39).tx * 16 + 8, y: at(108, 39).ty * 16 + 20, z: 10, untilMs: s.env.now + 5000 }; // light
  const crate = s.map.objects.find((o) => o.type === 'crate' && o.tx === 101 && o.ty === at(101, 54).ty);
  if (crate) slideCrate(s, crate, -1, 0, 5); // weight: onto the plate
  s.switchUntil['source-echo'] = s.env.now + 10_000; // resonance
  run(s, none, 2);
}

describe('C5: the small 星環 on the beach', () => {
  const ring = WORLD.warps.find((w) => w.id === 'source-gate');

  it('stands on the sand, 5+ tiles west of the start and the beach stone; walk up into it', () => {
    expect(ring).toBeTruthy();
    const beach = WORLD.checkpoints.find((c) => c.id === 'beach');
    const s = createGameState(WORLD);
    expect(Math.floor(s.map.spawn.x / 16) - ring.tx).toBeGreaterThanOrEqual(5);
    expect(beach.tx - ring.tx).toBeGreaterThanOrEqual(5);
    expect(ring.facing).toBe('up');
    expect(WORLD.envObjects.some((o) => o.type === 'star_ring' && o.tx === ring.tx && o.ty === ring.ty)).toBe(true);
    expect(ring.if).toEqual([{ flag: 'source_open' }, { flag: 'source_purified', is: false }]);
    // It leads into the antechamber, and the antechamber's way out leads to the sand in front of it.
    const into = { x: ring.toTx * 16 + 8, y: ring.toTy * 16 + 8 };
    expect(areaAt(s, into.x, into.y)?.id).toBe('source_gate');
    const out = WORLD.warps.find((w) => w.id === 'source-out');
    expect([out.toTx, out.toTy]).toEqual([ring.tx, ring.ty + 1]);
    expect(areaAt(s, out.tx * 16 + 8, out.ty * 16 + 8)?.id).toBe('source_gate');
  });

  /** Walks north into the ring from the sand in front of it; returns the area the player ends in. */
  const walkIn = (flags) => {
    const s = createGameState(WORLD);
    s.enemies = [];
    s.enemySpawns = [];
    Object.assign(s.progress.flags, flags);
    place(s, { tx: ring.tx, ty: ring.ty + 1 });
    run(s, { ...none, moveY: -1 }, 30);
    return areaAt(s, s.player.x, s.player.y)?.id ?? null;
  };
  it('the princess opens it: after the four cores, her all_cores talk sets source_open and the ring leads in', () => {
    const s = createGameState(WORLD);
    s.enemies = [];
    s.enemySpawns = [];
    s.progress.flags.princess_met = true;
    s.progress.quests.star_ring_call = 'active';
    s.progress.bosses.push('core_forest', 'core_mountains', 'core_desert', 'core_lake');
    expect(warpOpen(s, ring)).toBe(false);
    startDialogue(s, 'princess', 'princess_beach');
    expect(s.dialogue?.node).toBe('all_cores');
    for (let k = 0; k < 20 && s.dialogue; k++) advance(s, dialogueView(s)?.choices?.length ? 0 : undefined);
    expect(s.progress.flags.source_open).toBe(true);
    expect(warpOpen(s, ring)).toBe(true);
    place(s, { tx: ring.tx, ty: ring.ty + 1 });
    run(s, { ...none, moveY: -1 }, 30);
    expect(areaAt(s, s.player.x, s.player.y)?.id).toBe('source_gate');
  });

  it('is only a ring until source_open; then a gate; closed again once the source is purified', () => {
    expect(walkIn({})).toBe(null);
    expect(walkIn({ source_open: true })).toBe('source_gate');
    expect(walkIn({ source_open: true, source_purified: true })).toBe(null);
    const s = createGameState(WORLD);
    expect(warpOpen(s, ring)).toBe(false);
    s.progress.flags.source_open = true;
    expect(warpOpen(s, ring)).toBe(true);
  });
});

describe('C6: the arena in the desert strip', () => {
  it('antechamber (record stone) and arena in the west column below the dark trial; the four cores unchanged', () => {
    const gate = area('source_gate');
    const ar = area('source_arena');
    const desert = WORLD.regions.find((r) => r.id === 'desert');
    for (const a of [gate, ar]) {
      expect(a.tx).toBeGreaterThanOrEqual(98);
      expect(a.tx + a.tw - 1).toBeLessThanOrEqual(110);
      expect(a.ty - desert.ty).toBeGreaterThanOrEqual(18);
      expect(a.ty + a.th).toBeLessThanOrEqual(desert.ty + desert.th);
    }
    const stone = WORLD.checkpoints.find((c) => c.id === 'source');
    const s = createGameState(WORLD);
    expect(areaAt(s, stone.tx * 16 + 8, stone.ty * 16 + 8)?.id).toBe('source_gate');
    expect(WORLD.bosses).toHaveLength(4);
    expect(WORLD.bosses.some((b) => b.id === 'source')).toBe(false);
    expect(WORLD.finalBoss.id).toBe('source');
  });

  it('four seats: fire, light, weight, resonance; the light seat 3+ tiles from every brazier and sconce', () => {
    const seats = WORLD.switches.filter((x) => x.seat);
    expect(seats.map((x) => x.id).sort()).toEqual([...SEATS].sort());
    expect(Object.fromEntries(seats.map((x) => [x.id, x.accepts]))).toEqual({
      'source-fire': ['fire'],
      'source-light': ['light'],
      'source-weight': ['weight'],
      'source-echo': ['resonance', 'shock'],
    });
    const light = seats.find((x) => x.id === 'source-light');
    const ar = area('source_arena');
    const flames = WORLD.envObjects.filter((o) => ['brazier', 'sconce', 'campfire'].includes(o.type) && o.tx >= ar.tx && o.tx < ar.tx + ar.tw && o.ty >= ar.ty && o.ty < ar.ty + ar.th);
    expect(flames.length).toBeGreaterThanOrEqual(3);
    for (const f of flames) expect(Math.max(Math.abs(f.tx - light.tx), Math.abs(f.ty - light.ty))).toBeGreaterThanOrEqual(3);
  });

  it('the light seat is dark at the start; no seat is awake when the fight begins', () => {
    const { s, b } = arena();
    run(s, none, 30);
    expect(s.switchActive['source-light']).toBe(false);
    expect(SEATS.map((id) => s.switchActive[id])).toEqual([false, false, false, false]);
    expect(seatsOf(b)).toEqual([]);
    // (The braziers do give light — just not as far as the seat.)
    expect(lightSources(s).length).toBeGreaterThan(0);
  });

  it('the weight seat is out of the ring\'s reach, and the ring itself never counts as weight', () => {
    const { s, b } = arena();
    const plate = s.switches.find((x) => x.id === 'source-weight');
    for (let t = 0; t < 60_000; t += MS) {
      keepAlive(s);
      stepGame(s, none);
      expect(Math.hypot(b.x - (plate.tx * 16 + 8), b.y - (plate.ty * 16 + 8))).toBeGreaterThan(b.r + 16);
    }
    // Even put right onto the plate, it does not press it.
    place(s, at(104, 55));
    b.x = b.prevX = plate.tx * 16 + 8;
    b.y = b.prevY = plate.ty * 16 + 10;
    expect(switchActive(s, plate, [])).toBe(false);
    s.enemies.push({ ...b, final: false, id: 999 }); // (an ordinary enemy there would)
    expect(switchActive(s, plate, [])).toBe(true);
  });

  it('seats are never doors or gates', () => {
    const { s } = arena();
    wakeAll(s);
    run(s, none, 10);
    expect(s.progress.gates).toEqual([]);
    expect(s.events.some((e) => e.type === 'gateOpen')).toBe(false);
  });
});

describe('C7: 淀みの源', () => {
  it('is not one of the cores: not in the bosses list, appears only in its arena', () => {
    const s = createGameState(WORLD);
    stepGame(s, none);
    expect(s.enemies.some((e) => e.final)).toBe(false);
    expect(s.enemies.filter((e) => e.boss)).toHaveLength(4);
    const { s: t, b } = arena();
    expect(b.boss).toBeFalsy();
    expect(b.name).toBe(FINAL_BOSS.name);
    expect(t.progress.bosses).toEqual([]);
    run(t, none, 2);
    expect(b.awake).toBe(true);
    expect(activeFinalBoss(t)).toBe(b);
    expect(activeBoss(t)).toBe(b); // (the HUD's boss bar)
    expect(t.events.some((e) => e.type === 'sourceAwake')).toBe(true);
  });

  it('cannot be hurt while inverted: sword, arrows, fire, anything', () => {
    const { s, b } = arena();
    for (const hit of [
      { kind: 'melee', damage: 50 },
      { kind: 'projectile', damage: 50, element: 'fire' },
      { kind: 'projectile', damage: 8 },
    ]) {
      expect(hitEnemy(s, b, { owner: 'player', id: `t${Math.random()}`, from: { x: b.x, y: b.y + 20 }, ...hit })).toBe(false);
    }
    // A real sword swing in reach.
    place(s, { tx: Math.floor(b.x / 16), ty: Math.floor(b.y / 16) + 1 });
    swing(s);
    expect(b.hp).toBe(b.maxHp);
    expect(s.events.some((e) => e.type === 'sourceGuard')).toBe(true);
  });

  it('all four seats awake → it staggers for 8 s and can be hit; each hit takes a third; three purify it', () => {
    const { s, b } = arena();
    const shards = countOf(s.progress.inv, 'star_shard');
    const money = s.progress.inv.money;
    const hpAfter = [];
    for (let round = 0; round < 3; round++) {
      keepAlive(s);
      hold(s, 120); // (the last wave has passed)
      wakeAll(s);
      expect(b.state, `round ${round}`).toBe('stagger');
      expect(s.events.some((e) => e.type === 'sourceStagger')).toBe(true);
      expect(hitEnemy(s, b, { owner: 'player', id: `r${round}`, damage: 1, from: { x: b.x, y: b.y + 20 }, kind: 'melee' })).toBe(true);
      hpAfter.push(b.hp);
      s.orb = null; // (the light orb would wake the light seat again right after the wave)
      if (round < 2) {
        // It inverts again at once: a wave is coming, and it is invulnerable again.
        expect(b.state).toBe('windup');
        expect(b.pattern).toBe('wave');
        expect(hitEnemy(s, b, { owner: 'player', id: `r${round}b`, damage: 99, from: { x: b.x, y: b.y + 20 }, kind: 'melee' })).toBe(false);
        hold(s, Math.ceil(b.windupMs / MS) + 2);
        expect(seatsOf(b)).toEqual([]);
      }
    }
    expect(hpAfter).toEqual([60, 30, 0]);
    expect(b.state).toBe('dead');
    stepGame(s, none);
    expect(s.progress.flags[SOURCE_PURIFIED]).toBe(true);
    expect(s.events.filter((e) => e.type === 'sourcePurified')).toHaveLength(1);
    expect(s.saveRequested).toBe(true);
    // No star shard, no money, and it is not counted among the cores.
    expect(countOf(s.progress.inv, 'star_shard')).toBe(shards);
    expect(s.progress.inv.money).toBe(money);
    expect(s.progress.bosses).toEqual([]);
    // Gone after its defeat frames, and never again: not on stepping back in, not from a save.
    hold(s, Math.ceil(FINAL_BOSS.defeatMs / MS) + 2);
    expect(s.enemies.some((e) => e.final)).toBe(false);
    place(s, at(104, 22)); // (out into the antechamber)
    run(s, none, 5);
    place(s, at(104, 55));
    run(s, none, 30);
    expect(s.enemies.some((e) => e.final)).toBe(false);
    expect(s.events.filter((e) => e.type === 'sourcePurified')).toHaveLength(1);
    const t = createGameState(WORLD);
    applyProgress(t, JSON.parse(JSON.stringify(s.progress)));
    place(t, at(104, 55));
    run(t, none, 30);
    expect(t.enemies.some((e) => e.final)).toBe(false);
  });

  it('the stagger ends after 8 s without a hit: a wave puts the seats out', () => {
    const { s, b } = arena();
    hold(s, 60);
    wakeAll(s);
    expect(b.state).toBe('stagger');
    hold(s, Math.floor((FINAL_BOSS.staggerMs - 100) / MS));
    expect(b.state).toBe('stagger');
    hold(s, 10);
    expect([b.state, b.pattern]).toEqual(['windup', 'wave']);
    expect(b.hp).toBe(b.maxHp);
    hold(s, Math.ceil(b.windupMs / MS) + 2);
    expect(s.events.some((e) => e.type === 'sourceWave')).toBe(true);
    expect(seatsOf(b)).toEqual([]);
  });

  it('phase 2 below half health: shorter wind-ups', () => {
    const { s, b } = arena();
    for (let round = 0; round < 2; round++) {
      keepAlive(s);
      hold(s, 120);
      wakeAll(s);
      hitEnemy(s, b, { owner: 'player', id: `p${round}`, damage: 1, from: { x: b.x, y: b.y + 20 }, kind: 'melee' });
      if (round === 0) expect(b.phase).toBe(1);
    }
    expect(b.phase).toBe(2);
    expect(s.events.some((e) => e.type === 'sourcePhase')).toBe(true);
    expect(b.windupMs).toBe(Math.round(FINAL_BOSS.waveWindupMs * PHASE2_WINDUP));
    // The next attack after the wave: its wind-up is shorter too.
    for (let t = 0; t < 8000 && !(b.state === 'windup' && b.pattern !== 'wave'); t += MS) hold(s, 1);
    expect(b.state).toBe('windup');
    expect(b.windupMs).toBe(Math.round(FINAL_BOSS.windupMs * PHASE2_WINDUP));
  });

  it('attacks: the fan, the ring of orbs, the slam, and the inversion wave (all telegraphed)', () => {
    const { s, b } = arena();
    const seen = new Set();
    for (let t = 0; t < 40_000; t += MS) {
      keepAlive(s);
      const prev = b.state;
      const shotsBefore = s.projectiles.length;
      stepGame(s, none);
      if (prev === 'windup' && b.state === 'attack') {
        seen.add(b.pattern);
        if (b.pattern === 'volley') expect(s.projectiles.length - shotsBefore).toBeGreaterThanOrEqual(FINAL_BOSS.volleyShots - 1);
        if (b.pattern === 'ring') expect(s.projectiles.length - shotsBefore).toBeGreaterThanOrEqual(FINAL_BOSS.ringShots - 2);
      }
    }
    expect([...seen].sort()).toEqual(['ring', 'slam', 'volley', 'wave']);
  });

  it('the slam and the wave hurt on the ground nearby, not a player in the air', () => {
    const run2 = (jump) => {
      const { s, b } = arena();
      b.patternIndex = FINAL_BOSS.phase1.indexOf('wave');
      const hp0 = s.player.hp;
      for (let t = 0; t < 4000; t += MS) {
        place(s, { tx: Math.floor(b.x / 16), ty: Math.floor(b.y / 16) + 2 });
        if (jump) Object.assign(s.player, { z: s.player.groundZ + 20, grounded: false, vz: 0, invulnMs: 0 });
        else s.player.invulnMs = 0;
        stepGame(s, none);
        if (b.pattern === 'wave' && b.state === 'recover') break;
      }
      return hp0 - s.player.hp;
    };
    expect(run2(false)).toBeGreaterThan(0);
    expect(run2(true)).toBe(0);
  });
});

describe('the seats can be woken again and again (C15)', () => {
  it('awake → stagger → the wave puts them out (sconce dark, crate home, stone silent) → awake again', () => {
    const { s, b } = arena();
    const sconce = objAt(s, at(100, 40));
    for (let round = 0; round < 3; round++) {
      keepAlive(s);
      hold(s, 60);
      s.orb = null;
      wakeAll(s);
      expect(b.state, `round ${round}`).toBe('stagger');
      expect(sconce.lit).toBe(true);
      expect(objAt(s, at(99, 54))?.type).toBe('crate');
      hold(s, Math.ceil(FINAL_BOSS.staggerMs / MS) + 2);
      s.orb = null; // (the light orb fades by itself; here it is put away before the wave)
      hold(s, Math.ceil(b.windupMs / MS) + 2);
      expect(sconce.lit).toBe(false);
      expect(objAt(s, at(101, 54))?.type).toBe('crate');
      expect(objAt(s, at(99, 54))).toBe(undefined);
      expect(s.switchUntil['source-echo']).toBe(undefined);
      hold(s, 2);
      expect(seatsOf(b)).toEqual([]);
      expect(SEATS.map((id) => s.switchActive[id])).toEqual([false, false, false, false]);
    }
    expect(b.staggers).toBe(3);
    expect(b.hp).toBe(b.maxHp);
  });

  it('unlightSconce puts a sconce out (and only a lit one)', () => {
    const { s } = arena();
    const o = objAt(s, at(100, 40));
    const v = s.env.version;
    unlightSconce(s, o);
    expect(s.env.version).toBe(v);
    lightSconce(s, o);
    expect(o.lit).toBe(true);
    unlightSconce(s, o);
    expect(o.lit).toBe(false);
    expect(s.events.some((e) => e.type === 'sconceOut')).toBe(true);
    resetSeats(s, s.enemies.find((e) => e.final)); // (nothing to put out: harmless)
    expect(o.lit).toBe(false);
  });
});

describe('every seat wakes in two ways or more, one without any 星環 ability', () => {
  const awakeAfter = (s, id) => {
    run(s, none, 3);
    return !!s.enemies.find((e) => e.final).seats[id];
  };

  it('fire, way 1 (no ability): a fire arrow shot north through the brazier', () => {
    const { s } = arena();
    place(s, at(100, 47), 'up');
    shoot(s);
    expect(objAt(s, at(100, 40)).lit).toBe(true);
    expect(awakeAfter(s, 'source-fire')).toBe(true);
  });
  it('fire, way 2 (no ability): the fire blade swung at the sconce', () => {
    const { s } = arena();
    s.progress.inv.weapons.push({ id: 'ember_sword', dur: 22, lvl: 0 });
    s.progress.inv.equip.weapon = s.progress.inv.weapons.length - 1;
    place(s, at(101, 40), 'left');
    swing(s);
    expect(awakeAfter(s, 'source-fire')).toBe(true);
  });

  it('light, way 1 (no ability): a fire arrow through the east brazier sets the grass under the wall alight', () => {
    const { s } = arena();
    place(s, at(108, 46), 'up');
    shoot(s);
    const grass = at(108, 37);
    expect(s.env.burning.has(grass.ty * s.map.width + grass.tx)).toBe(true);
    expect(awakeAfter(s, 'source-light')).toBe(true);
  });
  it('light, way 2 (灯火): a light orb by the seat', () => {
    const { s } = arena(['light']);
    place(s, at(108, 41), 'up');
    useAbility(s, 'light');
    expect(awakeAfter(s, 'source-light')).toBe(true);
  });

  it('weight, way 1 (no ability): sword hits push the crate onto the plate', () => {
    const { s } = arena();
    place(s, at(102, 54), 'left');
    swing(s);
    place(s, at(101, 54), 'left');
    swing(s);
    expect(objAt(s, at(99, 54))?.type).toBe('crate');
    expect(awakeAfter(s, 'source-weight')).toBe(true);
  });
  it('weight, way 2 (no ability): standing on the plate', () => {
    const { s } = arena();
    place(s, at(99, 54), 'up');
    expect(awakeAfter(s, 'source-weight')).toBe(true);
  });
  it('weight, way 3 (念動): the crate slides onto the plate', () => {
    const { s } = arena(['telekinesis']);
    place(s, at(102, 54), 'left');
    useAbility(s, 'telekinesis');
    expect(objAt(s, at(99, 54))?.type).toBe('crate');
    expect(awakeAfter(s, 'source-weight')).toBe(true);
  });

  it('resonance, way 1 (no ability): strike the crystal; the current runs along the metal floor to the stone', () => {
    const { s } = arena();
    place(s, at(105, 54), 'right');
    swing(s);
    expect(s.events.some((e) => e.type === 'discharge')).toBe(true);
    expect(awakeAfter(s, 'source-echo')).toBe(true);
  });
  it('resonance, way 2 (共鳴): a resonance pulse', () => {
    const { s } = arena(['resonance']);
    place(s, at(107, 52), 'right');
    useAbility(s, 'resonance');
    expect(awakeAfter(s, 'source-echo')).toBe(true);
  });

  it('one seat alone is not enough (no stagger)', () => {
    const { s, b } = arena();
    place(s, at(99, 54), 'up');
    run(s, none, 60);
    expect(seatsOf(b)).toEqual(['source-weight']);
    expect(b.state).not.toBe('stagger');
  });
});

describe('the art (placeholders under the release art\'s names)', () => {
  it('every frame of enemy.boss_source.* (64 × 64, feet at the bottom) in its own bundle; the beach ring in the base one', () => {
    const entries = sourceEntries();
    const keys = new Set(entries.map((e) => e.key));
    for (const [action, n] of Object.entries(SOURCE_ACTIONS)) for (let f = 0; f < n; f++) expect(keys.has(`enemy.boss_source.${action}.${f}`)).toBe(true);
    const base = new Set(placeholderEntries().map((e) => e.key));
    expect(base.has('obj.star_ring.on') && base.has('obj.star_ring.off')).toBe(true);
    expect([...keys].every((k) => k.startsWith('enemy.boss_source.'))).toBe(true);
    for (const e of entries) {
      for (const r of e.rows) expect(r.length, e.key).toBe(e.rows[0].length);
      if (e.key.startsWith('enemy.')) expect([e.rows[0].length, e.rows.length]).toEqual([64, 64]);
      expect(e.anchor).toEqual([0.5, 1]);
    }
    expect(atlasSizeFor(entries)).toBeLessThanOrEqual(512);
    expect(SOURCE_BUNDLE in REGION_ENTRIES).toBe(false); // (its own: loaded only near the arena)
    // The arena (and the antechamber) lie in a region whose presence loads the bundle.
    const ar = WORLD.areas.find((a) => a.id === 'source_arena');
    const r = WORLD.regions.find((x) => ar.tx >= x.tx && ar.tx < x.tx + x.tw && ar.ty >= x.ty && ar.ty < x.ty + x.th);
    expect(SOURCE_REGIONS).toContain(r.id);
    expect(SOURCE_REGIONS).not.toContain('island');
  });

  it('the release art (src/art-release/enemy) has every frame under the same names and size, and it goes in the source\'s bundle', () => {
    const dir = new URL('../../src/art-release/enemy/', import.meta.url);
    const files = readdirSync(dir).filter((f) => f.startsWith('enemy.boss_source.') && f.endsWith('.png'));
    const art = new Map(files.map((f) => [f.slice(0, -4), f]));
    const ours = sourceEntries();
    for (const e of ours) {
      expect(art.has(e.key), e.key).toBe(true);
      const png = readFileSync(new URL(/** @type {string} */ (art.get(e.key)), dir));
      // 2 art pixels per game pixel: 128 × 128 for the 64 × 64 placeholder.
      expect([png.readUInt32BE(16), png.readUInt32BE(20)], e.key).toEqual([e.rows[0].length * 2, e.rows.length * 2]);
    }
    // Only the tendril frames are not used (yet).
    expect([...art.keys()].filter((k) => !ours.some((e) => e.key === k)).every((k) => k.includes('.tendril.'))).toBe(true);
    // Not in the base atlas.
    expect(releaseEnemyEntries(new Map([...art.keys()].map((k) => [k, 'x.png']))).length).toBe(0);
  });

  it('a frame for each state of the fight, falling back to idle when a frame is missing', () => {
    const all = () => true;
    const e = { state: 'idle', phase: 1, pattern: null, t: 0, clock: 0, transformUntil: 0, transformFrom: 0 };
    expect(sourceFrameKey(e, 0, all)).toBe('enemy.boss_source.idle.0');
    expect(sourceFrameKey({ ...e, phase: 2 }, 0, all)).toBe('enemy.boss_source.idle2.0');
    expect(sourceFrameKey({ ...e, state: 'windup', pattern: 'wave' }, 0, all)).toBe('enemy.boss_source.windup_charge.0');
    expect(sourceFrameKey({ ...e, state: 'attack', pattern: 'ring' }, 0, all)).toBe('enemy.boss_source.attack_ring.0');
    expect(sourceFrameKey({ ...e, state: 'stagger' }, 0, all)).toBe('enemy.boss_source.hurt.0');
    expect(sourceFrameKey({ ...e, state: 'dead', t: FINAL_BOSS.defeatMs }, 0, all)).toBe('enemy.boss_source.defeat.5');
    expect(sourceFrameKey({ ...e, clock: 300, transformFrom: 0, transformUntil: 1000 }, 0, all)).toBe('enemy.boss_source.transform.1');
    expect(sourceFrameKey({ ...e, state: 'stagger' }, 0, (k) => k.includes('.idle.'))).toBe('enemy.boss_source.idle.0');
  });
});

describe('three rounds with real inputs only, no abilities (review 中-1)', () => {
  it('fire arrows through the braziers, the sword on the crate and the crystal, a blow in each stagger: purified', () => {
    const s = createGameState(WORLD);
    s.enemies = [];
    s.enemySpawns = [];
    s.player.maxHp = s.player.hp = 4000;
    // The player stands where each action is done (attacks would knock them around otherwise).
    let spot = at(104, 55);
    let facing = 'up';
    const step = (input = none) => {
      s.player.hp = s.player.maxHp;
      s.player.dead = false;
      place(s, spot, facing);
      stepGame(s, input);
    };
    const go = (p, f) => {
      spot = p;
      facing = f;
      step();
    };
    const wait = (n, input = none) => {
      for (let i = 0; i < n; i++) step(input);
    };
    const fire = () => {
      wait(Math.ceil((COMBAT.bowDrawMs / 1000) * 60) + 2, { ...none, bow: true });
      wait(60);
    };
    const cut = () => {
      step({ ...none, attack: true });
      wait(40);
    };
    wait(2);
    const b = s.enemies.find((e) => e.final);
    const arrows0 = countOf(s.progress.inv, 'arrow');
    const roundMs = [];
    for (let round = 0; round < 3; round++) {
      const t0 = s.env.now;
      for (let tries = 0; tries < 4 && b.state !== 'stagger'; tries++) {
        go(at(108, 46), 'up'); // light: a fire arrow through the east brazier sets the grass alight
        fire();
        go(at(100, 47), 'up'); // fire: a fire arrow through the west brazier onto the sconce
        fire();
        go(at(102, 54), 'left'); // weight: two sword hits push the crate onto the plate
        cut();
        go(at(101, 54), 'left');
        cut();
        go(at(105, 54), 'right'); // resonance: strike the crystal
        cut();
        wait(3);
      }
      expect(b.state, `round ${round}`).toBe('stagger');
      for (let k = 0; k < 20 && b.state === 'stagger'; k++) {
        go({ tx: Math.floor(b.x / 16), ty: Math.floor(b.y / 16) + 1 }, 'up');
        cut();
      }
      expect(b.hp, `round ${round}`).toBe(FINAL_BOSS.hp - 30 * (round + 1));
      roundMs.push(s.env.now - t0);
      go(at(104, 50), 'up');
      wait(200); // the wave passes
    }
    expect(s.progress.flags[SOURCE_PURIFIED]).toBe(true);
    // Each round is a matter of seconds (no waiting for burnt grass to grow back).
    for (const ms of roundMs) expect(ms).toBeLessThan(40_000);
    expect(arrows0 - countOf(s.progress.inv, 'arrow')).toBeLessThanOrEqual(12);
  }, 60_000);

  it('the wave makes the light seat\'s grass whole again (put out, no ash); nothing else', () => {
    const { s, b } = arena();
    const grass = [107, 108, 109].map((x) => at(x, 37)).map(({ tx, ty }) => ty * s.map.width + tx);
    const elsewhere = at(104, 50).ty * s.map.width + 30; // (an outdoor tile, far away)
    s.env.cells.set(elsewhere, { burnMs: 0, at: 0, wetUntil: 0, ashUntil: s.env.now + 99_000 });
    s.env.cells.set(grass[0], { burnMs: 0, at: 0, wetUntil: 0, ashUntil: s.env.now + 99_000 });
    s.env.cells.set(grass[1], { burnMs: 2000, at: s.env.now, wetUntil: 0, ashUntil: 0 });
    s.env.burning.add(grass[1]);
    resetSeats(s, b);
    expect(grass.every((i) => !s.env.burning.has(i) && (s.env.cells.get(i)?.ashUntil ?? 0) === 0)).toBe(true);
    expect(s.env.cells.get(elsewhere).ashUntil).toBeGreaterThan(s.env.now);
  });
});

describe('arrows by the source (review 中-2)', () => {
  it('a quiver in the antechamber comes back a minute after it is taken', () => {
    const d = WORLD.pickups.find((p) => p.id === 'source_arrows');
    expect(d).toMatchObject({ item: 'arrow', regrowMs: 60_000 });
    const s = createGameState(WORLD);
    expect(areaAt(s, d.tx * 16 + 8, d.ty * 16 + 8)?.id).toBe('source_gate');
    s.enemies = [];
    s.enemySpawns = [];
    stepGame(s, none);
    const n0 = countOf(s.progress.inv, 'arrow');
    place(s, { tx: d.tx, ty: d.ty });
    stepGame(s, none);
    expect(countOf(s.progress.inv, 'arrow')).toBe(n0 + d.count);
    place(s, { tx: d.tx + 2, ty: d.ty });
    run(s, none, Math.ceil(30_000 / MS));
    expect(s.pickups.some((p) => p.mapId === d.id)).toBe(false);
    run(s, none, Math.ceil(31_000 / MS));
    expect(s.pickups.some((p) => p.mapId === d.id)).toBe(true);
    place(s, { tx: d.tx, ty: d.ty });
    stepGame(s, none);
    expect(countOf(s.progress.inv, 'arrow')).toBe(n0 + 2 * d.count);
  }, 30_000);
});
