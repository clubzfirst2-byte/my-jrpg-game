import { describe, it, expect } from 'vitest';
import { createGameState, stepGame, respawnPlayer } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { tileFeet, applyProgress, areaAt } from '../../src/game/world/features.js';
import { hitEnemy } from '../../src/game/combat/damage.js';
import { STEP_SEC } from '../../src/game/core/fixedStep.js';
import { hourOf } from '../../src/game/env/weather.js';
import { dialogueView, advance, startDialogue } from '../../src/game/npc/talk.js';
import { OPENING, ENDING, startOpening, skipOpening, openingView, finishEnding, endingLine } from '../../src/game/story/story.js';
import { poseOf } from '../../src/view/heroAnim.js';

// v1.0 C9 (the opening, minimal) and C10 (the ending): docs/story/V1_STORY_PROPOSAL.md.

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false, ability: false };
const MS = STEP_SEC * 1000;
const run = (s, input, n) => {
  for (let i = 0; i < n; i++) stepGame(s, input);
};
const world = () => {
  const s = createGameState(WORLD);
  s.enemies = [];
  s.enemySpawns = [];
  return s;
};

describe('C9: the opening (a new game only, once, skippable)', () => {
  it('plays about 2.6 s with the controls stopped and the world waiting, then sets opening_seen and saves', () => {
    const s = world();
    startOpening(s);
    expect(s.opening).toEqual({ ms: 0 });
    const at = { x: s.player.x, y: s.player.y };
    const now = s.env.now;
    run(s, { ...none, moveX: 1 }, Math.floor(OPENING.totalMs / MS) - 2);
    expect(s.opening).not.toBe(null);
    expect([s.player.x, s.player.y]).toEqual([at.x, at.y]); // no moving while it plays
    expect(s.env.now).toBe(now); // (and the world waits)
    run(s, none, 4);
    expect(s.opening).toBe(null);
    expect(s.progress.flags.opening_seen).toBe(true);
    expect(s.saveRequested).toBe(true);
    expect(s.events.filter((e) => e.type === 'openingDone')).toHaveLength(1);
    run(s, { ...none, moveX: 1 }, 30);
    expect(s.player.x).toBeGreaterThan(at.x); // the controls are back
  });

  it('the ring flashes first, he gets up (his collapse backwards), then the pendant glows', () => {
    const s = world();
    startOpening(s);
    const seen = [];
    for (let t = 0; t < OPENING.totalMs; t += 50) {
      s.opening.ms = t;
      seen.push({ t, ...openingView(s), pose: poseOf(s.player, s, 0, Infinity) });
    }
    expect(seen.filter((v) => v.flash).every((v) => v.t < OPENING.flashEndMs)).toBe(true);
    expect(seen.some((v) => v.flash)).toBe(true);
    const frames = seen.map((v) => v.riseFrame);
    expect(frames[0]).toBe(3); // lying
    expect(frames.at(-1)).toBe(0); // standing
    for (let k = 1; k < frames.length; k++) expect(frames[k]).toBeLessThanOrEqual(frames[k - 1]);
    expect(seen.every((v) => v.pose.action === 'down' && v.pose.frame === v.riseFrame)).toBe(true);
    const glow = seen.map((v) => v.glow);
    expect(Math.max(...glow)).toBeGreaterThan(0.9);
    expect(glow[0]).toBe(0);
  });

  it('a tap skips it at once (and it never plays again)', () => {
    const s = world();
    startOpening(s);
    run(s, none, 10);
    skipOpening(s);
    expect(s.opening).toBe(null);
    expect(s.progress.flags.opening_seen).toBe(true);
    startOpening(s);
    expect(s.opening).toBe(null);
  });

  it('continuing a save never plays it — an old save without opening_seen included', () => {
    const s = world();
    applyProgress(s, { ...s.progress, flags: { princess_met: true } });
    respawnPlayer(s);
    run(s, none, 200);
    expect(s.opening).toBe(null);
    expect(s.progress.flags.opening_seen).toBeUndefined();
  });
});

// ---- C10 ----

const OY = WORLD.areas.find((a) => a.id === 'source_arena').ty - 36;
function place(s, tx, ty, facing = 'up') {
  const f = tileFeet(s.map, tx, ty);
  const p = s.player;
  Object.assign(p, { x: f.x, y: f.y, prevX: f.x, prevY: f.y, vx: 0, vy: 0, knockMs: 0, grounded: true, facing });
  p.z = p.prevZ = p.groundZ = s.map.elev[ty * s.map.width + tx];
  const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[facing];
  p.aimX = v[0];
  p.aimY = v[1];
}
const keep = (s) => {
  s.player.hp = s.player.maxHp = 4000;
  s.player.dead = false;
  place(s, 104, OY + 50);
};
/** A game at the end of the story: the gate open, the player in the arena, the source awake. */
function atTheSource() {
  const s = world();
  Object.assign(s.progress.flags, { princess_met: true, source_open: true, opening_seen: true });
  s.progress.quests = { star_ring_call: 'done', source_of_murk: 'active' };
  s.progress.bosses = ['core_forest', 'core_mountains', 'core_desert', 'core_lake'];
  place(s, 104, OY + 55);
  stepGame(s, none);
  const b = s.enemies.find((e) => e.final);
  expect(b).toBeTruthy();
  return { s, b };
}
/** Purifies the source the quick way: its four seats awake, a blow in each stagger. */
function purify(s, b) {
  for (let round = 0; round < 3; round++) {
    for (let i = 0; i < 400 && b.state !== 'stagger'; i++) {
      keep(s);
      for (const id of b.seatIds) b.seats[id] = true;
      stepGame(s, none);
    }
    expect(b.state, `round ${round}`).toBe('stagger');
    expect(hitEnemy(s, b, { owner: 'player', id: `r${round}`, damage: 1, from: { x: b.x, y: b.y + 20 }, kind: 'melee' })).toBe(true);
    for (const id of b.seatIds) b.seats[id] = false;
  }
  keep(s);
  stepGame(s, none);
  expect(s.progress.flags.source_purified).toBe(true);
}
/** Reads the dialogue to its end, answering with the given choices. */
function talkThrough(s, answers) {
  const q = [...answers];
  for (let k = 0; k < 40 && s.dialogue; k++) {
    const v = dialogueView(s);
    if (v.choices) advance(s, q.shift() ?? 0);
    else advance(s);
  }
}

describe('C10: the ending', () => {
  it('2 s after the source is purified the princess before the ring speaks the ending by herself', () => {
    const { s, b } = atTheSource();
    purify(s, b);
    const purifiedAt = s.events.find((e) => e.type === 'sourcePurified').tick;
    expect(s.endingAt).toBe(purifiedAt + ENDING.delayTicks);
    keep(s);
    stepGame(s, none); // (people come and go at the start of a step)
    expect(s.npcs.some((n) => n.id === 'princess_end')).toBe(true);
    expect(s.npcs.filter((n) => n.ghost)).toEqual([]); // the 写し身 are gone
    while (s.tick < s.endingAt - 1) {
      keep(s);
      stepGame(s, none);
    }
    expect(s.dialogue).toBe(null);
    stepGame(s, none);
    expect(s.dialogue).toMatchObject({ id: 'ending', npc: 'princess_end' });
    expect(dialogueView(s).text).toMatch(/もとの向きに戻りました/);
    // It starts once only.
    talkThrough(s, [0, 1]); // 石を合わせる, 手をさしだす
    expect(s.endingAt).toBe(null);
  });

  it('when her dialogue is over: the ending screen (once); after it the village at 6:00, the plains stone, ending_seen, saved', () => {
    const { s, b } = atTheSource();
    purify(s, b);
    while (!s.dialogue) {
      keep(s);
      stepGame(s, none);
    }
    talkThrough(s, [1, 0]); // 胸に戻す, うなずく
    expect(s.progress.flags.regalia_kept).toBe(true);
    expect(s.progress.quests.source_of_murk).toBe('done');
    expect(s.ending).toBe(null);
    stepGame(s, none);
    expect(s.ending).toBe('screen');
    expect(endingLine(s)).toMatch(/二人の胸/);
    const tick = s.tick;
    const at = { x: s.player.x, y: s.player.y };
    run(s, { ...none, moveX: 1 }, 100); // the world waits behind the screen
    expect([s.player.x, s.player.y]).toEqual([at.x, at.y]);
    expect(s.events.filter((e) => e.type === 'endingScreen' && e.tick > tick - 2)).toHaveLength(1);
    s.saveRequested = false;
    finishEnding(s);
    expect(s.ending).toBe(null);
    expect(s.progress.flags.ending_seen).toBe(true);
    expect(s.progress.checkpoint).toBe('plains');
    expect(s.progress.checkpoints).toContain('plains');
    expect(hourOf(s.env.now)).toBe(6);
    expect(s.saveRequested).toBe(true);
    expect(s.player.hp).toBe(s.player.maxHp);
    const door = WORLD.warps.find((w) => w.id === 'inn-in');
    expect([Math.floor(s.player.x / 16), Math.floor(s.player.y / 16)]).toEqual([door.tx, door.ty + 1]);
    expect(areaAt(s, s.player.x, s.player.y)).toBe(null); // outdoors, in front of the inn
    // Then the game goes on: she is in the village, the princess by the ring is gone, nothing again.
    run(s, none, 5);
    expect(s.npcs.some((n) => n.id === 'princess_home')).toBe(true);
    expect(s.npcs.some((n) => n.id === 'princess_end')).toBe(false);
    expect(s.ending).toBe(null);
    finishEnding(s); // (twice is harmless)
    expect(s.events.filter((e) => e.type === 'endingDone')).toHaveLength(1);
    run(s, { ...none, moveY: 1 }, 30);
    expect(s.player.y).toBeGreaterThan(tileFeet(s.map, door.tx, door.ty + 1).y); // free to walk
  });

  it('the choice is made once: talking to her again goes to the last words only', () => {
    const { s, b } = atTheSource();
    purify(s, b);
    while (!s.dialogue) {
      keep(s);
      stepGame(s, none);
    }
    talkThrough(s, [0, 0]);
    startDialogue(s, 'ending', 'princess_end');
    expect(dialogueView(s).text).toMatch(/帰りましょう/);
    talkThrough(s, [1, 1]);
    expect(s.progress.flags.regalia_joined).toBe(true);
    expect(s.progress.flags.regalia_kept).toBeUndefined();
  });

  it('a save taken after the ending continues in the village, with no ending and no opening again', () => {
    const { s, b } = atTheSource();
    purify(s, b);
    while (!s.dialogue) {
      keep(s);
      stepGame(s, none);
    }
    talkThrough(s, [0, 0]);
    stepGame(s, none);
    finishEnding(s);
    const saved = JSON.parse(JSON.stringify({ ...s.progress, worldMs: Math.round(s.env.now) }));
    const t = world();
    applyProgress(t, saved);
    respawnPlayer(t);
    run(t, none, 200);
    expect(t.ending).toBe(null);
    expect(t.opening).toBe(null);
    expect(t.dialogue).toBe(null);
    const stone = WORLD.checkpoints.find((c) => c.id === 'plains');
    expect(Math.hypot(t.player.x / 16 - stone.tx, t.player.y / 16 - stone.ty)).toBeLessThan(3);
    expect(t.npcs.some((n) => n.id === 'princess_home')).toBe(true);
    expect(t.enemies.some((e) => e.final)).toBe(false);
  });

  it('down before her words (a stray shot): she does not speak from afar — she waits by the ring', () => {
    const { s, b } = atTheSource();
    purify(s, b);
    expect(s.endingAt).not.toBe(null);
    s.player.dead = true;
    stepGame(s, none);
    expect(s.endingAt).toBe(null);
    run(s, none, 400); // (back on his feet at the record stone)
    expect(s.player.dead).toBe(false);
    expect(s.dialogue).toBe(null);
    expect(s.npcs.some((n) => n.id === 'princess_end')).toBe(true);
    startDialogue(s, 'ending', 'princess_end');
    talkThrough(s, [0, 0]);
    stepGame(s, none);
    expect(s.ending).toBe('screen');
  });

  it('a map without the village (test maps): the ending still ends, the hero stays where he is', () => {
    const s = world();
    s.warps = s.warps.filter((w) => w.id !== 'inn-in');
    const at = { x: s.player.x, y: s.player.y };
    s.ending = 'screen';
    expect(() => finishEnding(s)).not.toThrow();
    expect(s.progress.flags.ending_seen).toBe(true);
    expect([s.player.x, s.player.y]).toEqual([at.x, at.y]);
  });

  it('closed during the ending screen: the choice is saved, so the screen comes back on continuing', () => {
    const t = world();
    applyProgress(t, { ...t.progress, flags: { princess_met: true, source_open: true, source_purified: true, regalia_joined: true }, quests: { star_ring_call: 'done', source_of_murk: 'done' } });
    respawnPlayer(t);
    stepGame(t, none);
    expect(t.ending).toBe('screen');
  });

  it('a purified source loaded from a save (before her words): she waits by the ring and talking to her ends the game', () => {
    const t = world();
    applyProgress(t, { ...t.progress, flags: { princess_met: true, source_open: true, source_purified: true }, quests: { star_ring_call: 'done', source_of_murk: 'active' } });
    respawnPlayer(t);
    run(t, none, 200);
    expect(t.dialogue).toBe(null); // no auto-start without the purification itself
    const n = t.npcs.find((x) => x.id === 'princess_end');
    expect(n).toBeTruthy();
    startDialogue(t, n.dialogue, n.id);
    talkThrough(t, [0, 0]);
    stepGame(t, none);
    expect(t.ending).toBe('screen');
  });
});
