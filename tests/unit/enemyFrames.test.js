import { describe, it, expect, afterEach } from 'vitest';
import { frameTable, useEnemyFrameTable, actionInfo, actionFamily, V1_TABLE, V1_FPS, V2_FPS } from '../../src/view/enemyFrames.js';
import { enemyFrameKey, ENEMY_ANIM } from '../../src/view/enemyAnim.js';
import { sourceFrameKey } from '../../src/view/sourceView.js';
import { createEnemy, ENEMY_KINDS } from '../../src/game/entities/enemies.js';
import { BOSS_KINDS } from '../../src/game/entities/bosses.js';
import { FINAL_BOSS } from '../../src/game/entities/finalBoss.js';

// gfx W3: the coming v2 art has 4–8 frames an action. Frame counts and speeds come from the art's
// frames.json, so every frame plays — here with a fake 8-frame table.

const N = 8;
const ENEMY_ACTIONS = ['idle', 'move', 'windup', 'attack', 'hurt', 'defeat'];
const BOSS_ACTIONS = ['idle', 'idle2', 'move', 'windup_charge', 'attack_charge', 'windup_slam', 'attack_slam', 'windup_volley', 'attack_volley', 'hurt', 'stagger', 'defeat'];
const SOURCE_ACTIONS = ['idle', 'idle2', 'windup_volley', 'attack_volley', 'windup_ring', 'attack_ring', 'windup_slam', 'attack_slam', 'windup_charge', 'attack_charge', 'hurt', 'transform', 'defeat'];
const fake = {
  fps: { idle: 6, move: 10, attack: 14 },
  kinds: {
    slime: { actions: Object.fromEntries(ENEMY_ACTIONS.map((a) => [a, { frames: N }])) },
    beast: { actions: Object.fromEntries(ENEMY_ACTIONS.map((a) => [a, { frames: N, ...(a === 'move' ? { fps: 12 } : {}) }])) },
    boss_root: { actions: Object.fromEntries(BOSS_ACTIONS.map((a) => [a, { frames: N }])) },
    boss_source: { actions: Object.fromEntries(SOURCE_ACTIONS.map((a) => [a, { frames: N }])) },
  },
};
const TABLE = frameTable(fake, 'v2', V2_FPS);
/** All the frames of the fake table are loaded. */
const keys = new Set();
for (const [kind, k] of Object.entries(fake.kinds)) for (const a of Object.keys(k.actions)) for (let f = 0; f < N; f++) keys.add(`enemy.${kind}.${a}.${f}`);
const has = (k) => keys.has(k);
const enemy = (kind, over = {}) => Object.assign(createEnemy(kind, 0, 0, 0, 1), over);
const boss = (over = {}) => ({ id: 1000, boss: true, kind: 'boss_root', bossKind: 'root', state: 'idle', t: 0, phase: 1, pattern: null, windupMs: 800, stunMs: 0, ...over });
const frameOf = (key) => Number(key.split('.').pop());
/** Every frame number seen over `steps` samples. */
const seen = (fn, steps) => new Set(Array.from({ length: steps }, (_, i) => frameOf(fn(i))));

afterEach(() => useEnemyFrameTable(V1_TABLE));

describe('the frame table (frames.json)', () => {
  it('reads counts and speeds per action; a per-action fps wins over the table-wide one', () => {
    expect(actionInfo('enemy.slime.idle', has, undefined, TABLE)).toEqual({ n: 8, fps: 6 });
    expect(actionInfo('enemy.slime.move', has, undefined, TABLE)).toEqual({ n: 8, fps: 10 });
    expect(actionInfo('enemy.beast.move', has, undefined, TABLE)).toEqual({ n: 8, fps: 12 });
    expect(actionInfo('enemy.boss_root.attack_slam', has, undefined, TABLE)).toEqual({ n: 8, fps: 14 }); // (the attack family)
    expect(actionInfo('enemy.slime.hurt', has, undefined, TABLE).fps).toBe(V2_FPS.hurt); // (a default)
    expect(actionFamily('windup_ring')).toBe('windup');
    expect(actionFamily('idle2')).toBe('idle2');
  });

  it('the v1 table is the release art’s frames.json (2–6 frames an action)', () => {
    expect(V1_TABLE.frames.get('enemy.beast.move')).toBe(4);
    expect(V1_TABLE.frames.get('enemy.boss_source.defeat')).toBe(6);
  });

  it('a table that does not match the loaded art falls back to the frames that are there, at v1 speed', () => {
    const v1Only = (k) => /\.(0|1)$/.test(k) && k.startsWith('enemy.slime.idle');
    expect(actionInfo('enemy.slime.idle', v1Only, undefined, TABLE)).toEqual({ n: 2, fps: V1_FPS.idle });
  });
});

describe('8-frame actions play fully', () => {
  it('idle loops all 8 frames at its fps (6), move at 10', () => {
    useEnemyFrameTable(TABLE);
    const idle = seen((i) => enemyFrameKey(enemy('slime'), i / 60, false, has), 120);
    expect(idle.size).toBe(8);
    // one loop of idle takes 8 / 6 s
    expect(frameOf(enemyFrameKey(enemy('slime', { id: 7 }), 0, false, has))).toBe(0);
    expect(frameOf(enemyFrameKey(enemy('slime', { id: 7 }), 1 / 6 + 0.001, false, has))).toBe(1);
    const move = seen((i) => enemyFrameKey(enemy('slime'), i / 60, true, has), 60);
    expect(move.size).toBe(8);
    expect(frameOf(enemyFrameKey(enemy('slime', { id: 7 }), 0.1 + 0.001, true, has))).toBe(1);
  });

  it('the wind-up goes through all 8 frames over its length, in order', () => {
    useEnemyFrameTable(TABLE);
    const w = ENEMY_KINDS.slime.windupMs;
    const frames = Array.from({ length: 80 }, (_, i) => frameOf(enemyFrameKey(enemy('slime', { state: 'windup', t: (i / 80) * w }), 0, false, has)));
    expect(new Set(frames).size).toBe(8);
    expect(frames).toEqual([...frames].sort((a, b) => a - b));
  });

  it('the attack plays all 8 frames, through the recovery, then holds the last', () => {
    useEnemyFrameTable(TABLE);
    const k = ENEMY_KINDS.slime;
    const at = (state, t) => frameOf(enemyFrameKey(enemy('slime', { state, t }), 0, false, has));
    const frames = new Set();
    for (let t = 0; t < k.activeMs; t += 5) frames.add(at('attack', t));
    for (let t = 0; t < k.recoveryMs; t += 5) frames.add(at('recover', t));
    expect(frames.size).toBe(8);
    expect(at('recover', k.recoveryMs)).toBe(7);
    expect(at('attack', 0)).toBe(0);
  });

  it('hurt plays through once; defeat spreads its 8 frames over the time before the body goes', () => {
    useEnemyFrameTable(TABLE);
    expect(seen((i) => enemyFrameKey(enemy('slime', { state: 'stun', t: i * 20 }), 0, false, has), 60).size).toBe(8);
    const defeat = seen((i) => enemyFrameKey(enemy('slime', { state: 'dead', t: (i / 100) * ENEMY_ANIM.defeatPlayMs }), 0, false, has), 100);
    expect(defeat.size).toBe(8);
  });

  it('a core: each pattern’s wind-up and attack, idle2 in phase 2, the stagger loop — all 8 frames', () => {
    useEnemyFrameTable(TABLE);
    for (const pattern of ['charge', 'slam', 'volley']) {
      expect(seen((i) => enemyFrameKey(boss({ state: 'windup', pattern, t: (i / 80) * 800 }), 0, false, has), 80).size, pattern).toBe(8);
    }
    const charge = BOSS_KINDS.root.chargeMs;
    const att = new Set();
    for (let t = 0; t < charge; t += 10) att.add(frameOf(enemyFrameKey(boss({ state: 'attack', pattern: 'charge', t }), 0, false, has)));
    for (let t = 0; t < 1000; t += 10) att.add(frameOf(enemyFrameKey(boss({ state: 'recover', pattern: 'charge', t }), 0, false, has)));
    expect(att.size).toBe(8);
    expect(enemyFrameKey(boss({ phase: 2 }), 0, false, has)).toMatch(/\.idle2\./);
    expect(seen((i) => enemyFrameKey(boss({ phase: 2 }), i / 30, false, has), 60).size).toBe(8);
    expect(seen((i) => enemyFrameKey(boss({ state: 'stun', stunMs: 99999, t: i * 20 }), 0, false, has), 100).size).toBe(8);
  });

  it('the source: transform, defeat, wind-ups and its open eye use all 8 frames', () => {
    useEnemyFrameTable(TABLE);
    const e = { final: true, state: 'idle', phase: 1, pattern: null, t: 0, clock: 0, transformUntil: 0, transformFrom: 0, windupMs: FINAL_BOSS.windupMs };
    expect(seen((i) => sourceFrameKey({ ...e, clock: i * 10, transformFrom: 0, transformUntil: 1000 }, 0, has), 100).size).toBe(8);
    expect(seen((i) => sourceFrameKey({ ...e, state: 'dead', t: (i / 100) * FINAL_BOSS.defeatMs }, 0, has), 100).size).toBe(8);
    expect(seen((i) => sourceFrameKey({ ...e, state: 'windup', pattern: 'ring', t: (i / 100) * FINAL_BOSS.windupMs }, 0, has), 100).size).toBe(8);
    expect(seen((i) => sourceFrameKey({ ...e, state: 'stagger' }, i / 30, has), 60).size).toBe(8);
    expect(seen((i) => sourceFrameKey({ ...e, state: 'attack', pattern: 'slam', t: i * 10 }, 0, has), 100).size).toBe(8);
  });
});
