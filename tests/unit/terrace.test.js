import { describe, it, expect } from 'vitest';
import { stepGame } from '../../src/game/state.js';
import { WORLD, regionAt } from '../../src/game/world/world.js';
import { areaAt, applyProgress, emptyProgress } from '../../src/game/world/features.js';
import { COMBAT } from '../../src/game/entities/playerCombat.js';
import { Ground } from '../../src/game/world/tilemap.js';
import { windReaches, laneWindAt, updraftAt, WIND } from '../../src/game/env/wind.js';
import { AIR_ROUTES, flyRoute, terraceState, T, place, none, run } from './terraceRoutes.js';

// Volume phase 1: 風切りの段丘 (the 奥地 of the plains). Everything here is done with the real game
// step and real inputs: the glides over the rifts, the wind lanes, the updrafts and the three wind
// trials (each solved in at least two ways).

describe('風切りの段丘: where it is', () => {
  it('is a region in a column of its own, dressed in the plains art, joined to the plains by a pass both ways', () => {
    const r = WORLD.regions.find((x) => x.id === 'terrace');
    expect(r).toMatchObject({ name: '風切りの段丘', tx: 256, ty: 0, bundle: 'region:plains', art: 'plains', parent: 'plains', climate: 'temperate' });
    for (const [id, to, dx] of [['pass-terrace', 'terrace', 1], ['pass-terrace-back', 'plains', -1]]) {
      const s = terraceState();
      const w = WORLD.warps.find((x) => x.id === id);
      const p = s.player;
      place(s, { tx: w.tx - dx * 3, ty: w.ty }, dx > 0 ? 'right' : 'left');
      for (let i = 0; i < 180 && regionAt(s.regions, Math.floor(p.x / 16), Math.floor(p.y / 16))?.id !== to; i++) stepGame(s, { ...none, moveX: dx });
      expect(regionAt(s.regions, Math.floor(p.x / 16), Math.floor(p.y / 16))?.id, id).toBe(to);
      expect(p.grounded).toBe(true);
    }
  });

  it('has two record stones, a survey stone, chests, a camp, at most three kinds of enemies, and three wind trials', () => {
    const r = WORLD.regions.find((x) => x.id === 'terrace');
    const inside = (o) => o.tx >= r.tx && o.tx < r.tx + r.tw && o.ty >= r.ty && o.ty < r.ty + r.th;
    expect(WORLD.checkpoints.filter(inside).map((c) => c.id)).toEqual(['terrace', 'terrace_east']);
    expect(WORLD.surveys.filter(inside).map((c) => c.region)).toEqual(['terrace']);
    expect(WORLD.chests.filter(inside).map((c) => c.id).sort()).toEqual(['terrace_camp', 'terrace_high', 'terrace_mound', 'terrace_west', 'trial_rise', 'trial_vane', 'trial_winds']);
    expect(WORLD.campfires.filter(inside)).toHaveLength(1);
    const kinds = new Set(WORLD.enemies.filter(inside).map((e) => e.kind));
    expect(WORLD.enemies.filter(inside).length).toBe(10);
    expect(kinds.size).toBeLessThanOrEqual(3);
    for (const k of kinds) expect(['beast', 'archer', 'slime', 'sentinel']).toContain(k); // the enemies there already are
    expect(WORLD.areas.filter((a) => inside(a)).map((a) => a.id)).toEqual(['trial_vane', 'trial_rise', 'trial_winds']);
  });

  it('the rifts are pits from edge to edge: no walking round them', () => {
    const s = terraceState();
    const r = WORLD.regions.find((x) => x.id === 'terrace');
    for (const [x0, x1] of [[28, 34], [59, 71]]) {
      for (let y = 0; y < 96; y++) for (let x = x0; x <= x1; x++) expect(s.map.ground[(r.ty + y) * s.map.width + r.tx + x], `${x},${y}`).toBe(Ground.PIT);
    }
    // The tableland ends in pits all round (no sea to swim).
    for (let y = 0; y < 96; y++) for (const x of [0, 95]) if (!(x === 0 && y >= 46 && y <= 48)) expect(s.map.ground[(r.ty + y) * s.map.width + r.tx + x]).toBe(Ground.PIT);
  });

  it('walking into a rift puts the player back at the edge (half a heart)', () => {
    const s = terraceState();
    place(s, T(26, 60), 'right');
    const hp = s.player.hp;
    for (let i = 0; i < 120 && !s.events.some((e) => e.type === 'fell'); i++) stepGame(s, { ...none, moveX: 1 });
    expect(s.events.some((e) => e.type === 'fell')).toBe(true);
    expect(s.player.hp).toBe(hp - 2);
    expect(Math.floor(s.player.x / 16) - 256).toBeLessThanOrEqual(27);
  });
});

describe('風切りの段丘: every way through the air works (real physics)', () => {
  it('walking off the knoll (no jump) is not "falling in": the glider opens in the air and carries over the rift', () => {
    const s = terraceState();
    place(s, T(26, 46), 'right');
    const move = { ...none, moveX: 1 };
    for (let i = 0; i < 240 && s.player.grounded; i++) stepGame(s, move);
    expect(s.player.grounded).toBe(false);
    expect(s.events.some((e) => e.type === 'fell')).toBe(false);
    run(s, move, 8);
    stepGame(s, { ...move, jump: true });
    expect(s.player.gliding).toBe(true);
    for (let i = 0; i < 600 && !s.player.grounded; i++) stepGame(s, move);
    expect(s.events.some((e) => e.type === 'fell')).toBe(false);
    expect(Math.floor(s.player.x / 16) - 256).toBeGreaterThanOrEqual(35);
  });

  it('walking off it without opening the glider drops into the rift: back at the edge, half a heart', () => {
    const s = terraceState();
    place(s, T(26, 46), 'right');
    const hp = s.player.hp;
    for (let i = 0; i < 400 && !s.events.some((e) => e.type === 'fell'); i++) stepGame(s, { ...none, moveX: 1 });
    expect(s.events.some((e) => e.type === 'fell')).toBe(true);
    expect(s.player.hp).toBeLessThan(hp);
    expect(Math.floor(s.player.x / 16) - 256).toBeLessThanOrEqual(27);
    expect(s.player.z).toBe(48);
  });

  for (const route of AIR_ROUTES) {
    it(`${route.id}: ${route.note}`, () => {
      const r = flyRoute(route);
      expect(r.fell, 'fell into the rift').toBe(false);
      expect(r.landed, `landed at ${r.at.tx},${r.at.ty} (z ${r.z})`).toBe(true);
    });
  }

  it('without its wind lane the second rift is too wide (the lane is what carries the glider over)', () => {
    const route = AIR_ROUTES.find((x) => x.id === 'K3-east');
    const r = flyRoute(route, { winds: false });
    expect(r.landed).toBe(false);
    expect(r.fell).toBe(true);
  });

  it('without the updraft the high terrace is out of reach: its rim of old stone cannot be climbed', () => {
    const route = AIR_ROUTES.find((x) => x.id === 'U1-high');
    const r = flyRoute(route, { updrafts: false });
    expect(r.landed).toBe(false);
    // Pushing into its south wall from the ground never grabs it.
    const s = terraceState();
    place(s, T(82, 37), 'up');
    run(s, { ...none, moveY: -1 }, 240);
    expect(s.player.climbing).toBeFalsy();
    expect(s.player.z).toBe(0);
  });
});

describe('wind lanes, updrafts and vanes (the parts)', () => {
  it('a lane pushes a glider its way at WIND.laneSpeed, and nothing outside it', () => {
    const s = terraceState();
    const w = WORLD.winds.find((x) => x.id === 'terrace-east');
    expect(laneWindAt(s, (w.tx + 2) * 16, (w.ty + 2) * 16)).toEqual({ x: WIND.laneSpeed, y: 0 });
    expect(laneWindAt(s, (w.tx + 2) * 16, (w.ty - 3) * 16)).toEqual({ x: 0, y: 0 });
    // Only a glider is carried: a player on the ground stands still in the lane.
    place(s, { tx: w.tx + 1, ty: w.ty + 3 }, 'down');
    const x = s.player.x;
    run(s, none, 60);
    expect(s.player.x).toBe(x);
  });

  it('an updraft under a roof lifts only as high as its `lift`', () => {
    const s = terraceState();
    const u = WORLD.updrafts.find((x) => x.id === 'trial-rise-near');
    expect(u.lift).toBe(40);
    expect(updraftAt(s, (u.tx + 1) * 16, (u.ty + 1) * 16)?.id).toBe('trial-rise-near');
    expect(updraftAt(s, (u.tx - 2) * 16, (u.ty + 1) * 16)).toBe(null);
  });

  it('the wind of a lane is stopped by what blocks movement, and comes back when that is gone', () => {
    const s = terraceState();
    const sw = WORLD.switches.find((x) => x.id === 'vane-a');
    expect(windReaches(s, sw.tx, sw.ty)).toBe(false);
    for (const o of s.map.objects) {
      if ((o.type === 'crate' || o.type === 'bramble') && o.ty === sw.ty && Math.abs(o.tx - sw.tx) < 11) {
        o.gone = true;
        s.map.solid[o.ty * s.map.width + o.tx] = 0;
      }
    }
    expect(windReaches(s, sw.tx, sw.ty)).toBe(true);
  });
});

// ---- the three wind trials: each in at least two ways ----
const area = (id) => WORLD.areas.find((a) => a.id === id);
function room(id, abilities = []) {
  const s = terraceState();
  s.progress.abilities = [...abilities];
  s.progress.ability = abilities[0] ?? null;
  const a = area(id);
  const at = (x, y) => ({ tx: a.tx - 98 + x, ty: a.ty + y });
  place(s, at(104, 11), 'up');
  stepGame(s, none);
  expect(areaAt(s, s.player.x, s.player.y)?.id).toBe(id);
  return { s, at };
}
const ability = (s, id, wait = 100) => {
  s.progress.ability = id;
  stepGame(s, { ...none, ability: true });
  run(s, none, wait);
};
const shoot = (s) => {
  run(s, { ...none, bow: true }, Math.ceil((COMBAT.bowDrawMs / 1000) * 60) + 2);
  run(s, none, 60);
};
const swing = (s) => {
  stepGame(s, { ...none, attack: true });
  run(s, none, 40);
};
const opened = (s, id) => s.progress.gates.includes(id);
const giveBow = (s) => {
  if (s.progress.inv.bows.length === 0) {
    s.progress.inv.bows.push({ id: 'wood_bow', dur: 30, lvl: 0 });
    s.progress.inv.equip.bow = 0;
  }
  s.progress.inv.items.arrow = 20;
};

describe('風車の試練: the vane must turn', () => {
  const t = 'trial_vane';
  it('way 1: clear the wind\'s row — cut the brambles, push the crate out with the sword', () => {
    const { s, at } = room(t);
    place(s, at(100, 7), 'right');
    for (let k = 0; k < 3; k++) swing(s);
    expect(opened(s, t)).toBe(false); // the crate still stands in the wind
    place(s, at(106, 8), 'up');
    swing(s);
    run(s, none, 10);
    expect(opened(s, t)).toBe(true);
  });

  it('way 1b: 念動 sends the crate out of the row (the brambles cut)', () => {
    const { s, at } = room(t, ['telekinesis']);
    place(s, at(100, 7), 'right');
    for (let k = 0; k < 3; k++) swing(s);
    place(s, at(106, 9), 'up');
    ability(s, 'telekinesis');
    expect(opened(s, t)).toBe(true);
  });

  it('way 2: a fire arrow through the brazier sets the grass beside the vane alight (hot air turns it)', () => {
    const { s, at } = room(t);
    giveBow(s);
    place(s, at(100, 8), 'right');
    shoot(s);
    run(s, none, 30);
    expect(opened(s, t)).toBe(true);
  });

  it('nothing done: it stays shut', () => {
    const { s } = room(t);
    run(s, none, 600);
    expect(opened(s, t)).toBe(false);
  });
});

describe('吹き上げの試練: the prize is across a rift', () => {
  const t = 'trial_rise';
  const chest = () => WORLD.chests.find((c) => c.id === t);
  const across = (s, at) => Math.floor(s.player.y / 16) <= at(0, 2).ty && s.player.grounded;
  it('way 1: jump into the rising air, open the glider, and it carries over; and back again', () => {
    const { s, at } = room(t);
    place(s, at(104, 10), 'up');
    stepGame(s, { ...none, moveY: -1, jump: true });
    run(s, { ...none, moveY: -1 }, 11);
    stepGame(s, { ...none, moveY: -1, jump: true });
    expect(s.player.gliding).toBe(true);
    for (let i = 0; i < 400 && !across(s, at); i++) stepGame(s, { ...none, moveY: -1 });
    expect(s.events.some((e) => e.type === 'fell')).toBe(false);
    expect(across(s, at)).toBe(true);
    // Back: from the far edge, the same way south.
    place(s, at(104, 2), 'down');
    stepGame(s, { ...none, moveY: 1, jump: true });
    run(s, { ...none, moveY: 1 }, 11);
    stepGame(s, { ...none, moveY: 1, jump: true });
    for (let i = 0; i < 400 && !(s.player.grounded && Math.floor(s.player.y / 16) >= at(0, 10).ty); i++) stepGame(s, { ...none, moveY: 1 });
    expect(s.events.some((e) => e.type === 'fell')).toBe(false);
    expect(Math.floor(s.player.y / 16)).toBeGreaterThanOrEqual(at(0, 10).ty);
  });

  it('without the rising air a jump and a glide fall short', () => {
    const { s, at } = room(t);
    s.updrafts = [];
    place(s, at(104, 10), 'up');
    stepGame(s, { ...none, moveY: -1, jump: true });
    run(s, { ...none, moveY: -1 }, 11);
    stepGame(s, { ...none, moveY: -1, jump: true });
    for (let i = 0; i < 400 && !across(s, at) && !s.events.some((e) => e.type === 'fell'); i++) stepGame(s, { ...none, moveY: -1 });
    expect(s.events.some((e) => e.type === 'fell')).toBe(true);
  });

  it('way 2: 蔓結び grows a bridge, a tile at a time', () => {
    const { s, at } = room(t, ['vine']);
    place(s, at(104, 10), 'up');
    for (let k = 0; k < 9 && !across(s, at); k++) {
      ability(s, 'vine', 25);
      run(s, { ...none, moveY: -1 }, 14);
      run(s, none, 2);
    }
    run(s, { ...none, moveY: -1 }, 30);
    expect(s.events.some((e) => e.type === 'fell')).toBe(false);
    expect(across(s, at)).toBe(true);
    expect(chest().reward).toBe('item');
  });
});

describe('二つ風の試練: both vanes at once', () => {
  const t = 'trial_winds';
  const clearEast = (s, at) => {
    // The crate in the east wind's row: pushed out north with the sword.
    place(s, at(103, 7), 'up');
    swing(s);
  };
  const clearWest = (s, at) => {
    for (const stand of [107, 106]) {
      place(s, at(stand, 9), 'left');
      for (let k = 0; k < 3; k++) swing(s);
    }
  };
  it('way 1: clear both rows (push the crate, cut the brambles)', () => {
    const { s, at } = room(t);
    clearEast(s, at);
    run(s, none, 10);
    expect(opened(s, t)).toBe(false); // one vane is not enough
    clearWest(s, at);
    run(s, none, 10);
    expect(opened(s, t)).toBe(true);
  });

  it('way 2: clear the east row; a fire arrow through the brazier turns the west vane with hot air', () => {
    const { s, at } = room(t);
    giveBow(s);
    clearEast(s, at);
    run(s, none, 10);
    expect(opened(s, t)).toBe(false);
    place(s, at(109, 10), 'left');
    shoot(s);
    run(s, none, 30);
    expect(opened(s, t)).toBe(true);
  });

  it('way 3: clear the west row; a fire arrow turns the east vane', () => {
    const { s, at } = room(t);
    giveBow(s);
    clearWest(s, at);
    run(s, none, 10);
    expect(opened(s, t)).toBe(false);
    place(s, at(99, 7), 'right');
    shoot(s);
    run(s, none, 30);
    expect(opened(s, t)).toBe(true);
  });

  it('two fire arrows alone are not enough: the first fire is out before the second is lit', () => {
    const { s, at } = room(t);
    giveBow(s);
    place(s, at(99, 7), 'right');
    shoot(s);
    run(s, none, 200); // (walking across the room)
    place(s, at(109, 10), 'left');
    shoot(s);
    run(s, none, 30);
    expect(opened(s, t)).toBe(false);
  });
});

// The terrace is the first chapter that is gone through, not round (plan_10h.md S1): its end is
// 二つ風の試練 on the high terrace, and opening it sets the flag chapter_terrace. Nothing in the
// main story reads the flag yet (what it opens is decided by the people who decide the story).
describe('風切りの段丘 as a chapter: its end cannot be reached without going through it', () => {
  const W = WORLD.ground[0].length;
  const s0 = terraceState();
  const map = s0.map;
  const passable = (i) => map.ground[i] !== Ground.DARK && map.ground[i] !== Ground.PIT && (!map.solid[i] || ['tree', 'bramble'].includes(s0.env.objectAt.get(i)?.type));
  const climbable = (i) => map.ground[i] !== Ground.RUIN && map.ground[i] !== Ground.WALL;
  /** Tiles reached from where the pass arrives: walking, jumping up a level, climbing earth, dropping, and the given air routes (no doorways). */
  const reach = (routeIds) => {
    const jumps = new Map();
    for (const r of AIR_ROUTES.filter((x) => routeIds.includes(x.id))) {
      const a = T(r.from[0], r.from[1]);
      const b = T(Math.round((r.to.x0 + r.to.x1) / 2), Math.round((r.to.y0 + r.to.y1) / 2));
      jumps.set(a.ty * W + a.tx, [...(jumps.get(a.ty * W + a.tx) ?? []), b.ty * W + b.tx]);
    }
    const pass = WORLD.warps.find((w) => w.id === 'pass-terrace');
    const start = pass.toTy * W + pass.toTx;
    const seen = new Set([start]);
    const q = [start];
    while (q.length) {
      const i = q.pop();
      for (const j of [i - 1, i + 1, i - W, i + W, ...(jumps.get(i) ?? [])]) {
        if (seen.has(j) || !passable(j)) continue;
        const air = jumps.get(i)?.includes(j);
        if (!air && map.elev[j] - map.elev[i] > 16 && !climbable(j)) continue;
        if (!air && Math.abs((j % W) - (i % W)) > 1) continue;
        seen.add(j);
        q.push(j);
      }
    }
    return seen;
  };
  const door = WORLD.warps.find((w) => w.id === 'trial_winds-in'); // the doorway at the pillar
  const end = door.ty * W + door.tx;
  const ALL = ['K1-east', 'K3-east', 'U1-high'];

  it('the region marks its chapter: 二つ風の試練 is the last trial, chapter_terrace the flag (the only chapter so far)', () => {
    expect(WORLD.regions.find((r) => r.id === 'terrace').chapter).toEqual({ id: 'terrace', gate: 'trial_winds', flag: 'chapter_terrace' });
    expect(WORLD.regions.filter((r) => r.chapter).map((r) => r.id)).toEqual(['terrace']);
  });

  it('from the pass, the way up to the gate of 二つ風の試練 is the first glide, the wind lane and the updraft, in that order', () => {
    expect(reach(ALL).has(end)).toBe(true);
    for (const leftOut of ALL) expect(reach(ALL.filter((x) => x !== leftOut)).has(end), `without ${leftOut}`).toBe(false);
    expect(reach([]).has(end)).toBe(false);
  });

  it('the only way into the terrace is its pass (no other doorway or pass lands in it)', () => {
    const r = WORLD.regions.find((x) => x.id === 'terrace');
    const into = WORLD.warps.filter((w) => regionAt(WORLD.regions, w.toTx, w.toTy)?.id === 'terrace' && regionAt(WORLD.regions, w.tx, w.ty)?.id !== 'terrace');
    expect(into.map((w) => w.id)).toEqual(['pass-terrace']);
    expect(r.tx).toBe(256);
  });

  it('opening 二つ風の試練 sets chapter_terrace (once, with an event); the other two trials do not', () => {
    const v = room('trial_vane');
    v.s.progress.gates.push('trial_rise'); // (as if 吹き上げの試練 were done too)
    place(v.s, v.at(101, 7), 'left');
    for (let k = 0; k < 3; k++) swing(v.s);
    place(v.s, v.at(106, 8), 'up');
    swing(v.s);
    run(v.s, none, 30);
    expect(opened(v.s, 'trial_vane')).toBe(true);
    expect(v.s.progress.flags.chapter_terrace).toBeUndefined();

    const { s, at } = room('trial_winds');
    const seen = [];
    const step = (input, n) => {
      for (let k = 0; k < n; k++) {
        stepGame(s, input);
        for (const e of s.events) if (e.type === 'chapterDone' && !seen.includes(e)) seen.push(e);
      }
    };
    place(s, at(103, 7), 'up');
    step({ ...none, attack: true }, 1);
    step(none, 40);
    for (const stand of [107, 106]) {
      place(s, at(stand, 9), 'left');
      for (let k = 0; k < 3; k++) {
        step({ ...none, attack: true }, 1);
        step(none, 40);
      }
    }
    step(none, 60);
    expect(opened(s, 'trial_winds')).toBe(true);
    expect(s.progress.flags.chapter_terrace).toBe(true);
    expect(seen.map((e) => e.id)).toEqual(['terrace']);
  });

  it('a save with 二つ風の試練 open has the flag when loaded; one without it does not', () => {
    const a = terraceState();
    applyProgress(a, { ...emptyProgress(), gates: ['trial_light', 'trial_winds'], flags: { princess_met: true } });
    expect(a.progress.flags).toEqual({ princess_met: true, chapter_terrace: true });
    const b = terraceState();
    applyProgress(b, { ...emptyProgress(), gates: ['trial_light', 'trial_vane'], flags: { princess_met: true } });
    expect(b.progress.flags).toEqual({ princess_met: true });
  });
});
