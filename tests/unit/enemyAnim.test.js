import { describe, it, expect, vi } from 'vitest';
import { enemyFrameKey, enemyAction, frameCount, warningFlashAlpha, defeatAlpha, WARNING_FLASH, ENEMY_ANIM } from '../../src/view/enemyAnim.js';
import { V1_FPS } from '../../src/view/enemyFrames.js';
import { createEnemy, ENEMY_KINDS, windupProgress, updateEnemy } from '../../src/game/entities/enemies.js';
import { createGameState, ENEMY_CORPSE_MS } from '../../src/game/state.js';
import { BOSS_PARRY_STUN_MS } from '../../src/game/entities/bosses.js';

// v1.0: which frame an enemy shows (release art per action, else the placeholder) and the wind-up
// warning overlay (red #ff3a3a at 50%, docs/art-direction/ART_STYLE_GUIDE.md 5.4 B).

/** The release frames of docs/art-release/enemy/frames.json (art branch) for one kind. */
const ENEMY_ACTIONS = { idle: 2, move: 4, windup: 2, attack: 2, hurt: 1, defeat: 3 };
const BOSS_ACTIONS = { idle: 2, move: 2, windup_charge: 2, attack_charge: 2, windup_slam: 2, attack_slam: 2, windup_volley: 2, attack_volley: 2, hurt: 1, stagger: 2, idle2: 2, defeat: 4 };
const release = (kind, actions) => {
  const keys = new Set([`enemy.${kind}.0`, `enemy.${kind}.1`]);
  for (const [a, n] of Object.entries(actions)) for (let i = 0; i < n; i++) keys.add(`enemy.${kind}.${a}.${i}`);
  return (k) => keys.has(k);
};
const placeholderOnly = (kind) => (k) => k === `enemy.${kind}.0` || k === `enemy.${kind}.1`;
const enemy = (kind, over = {}) => Object.assign(createEnemy(kind, 0, 0, 0, 1), over);
const boss = (over = {}) => ({ id: 1000, boss: true, kind: 'boss_root', bossKind: 'root', state: 'idle', t: 0, phase: 1, pattern: null, windupMs: 800, stunMs: 0, ...over });

describe('frames without release art (placeholder)', () => {
  it('stands on .0 and alternates .0/.1 while moving, as before v1.0', () => {
    for (const kind of ['beast', 'archer', 'slime', 'sentinel']) {
      const has = placeholderOnly(kind);
      expect(enemyFrameKey(enemy(kind), 3.2, false, has)).toBe(`enemy.${kind}.0`);
      const seen = new Set([0, 0.1, 0.2, 0.3].map((t) => enemyFrameKey(enemy(kind), t, true, has)));
      expect(seen).toEqual(new Set([`enemy.${kind}.0`, `enemy.${kind}.1`]));
      // Wind-up, attack, stun and death all keep the placeholder (it has no such frames).
      for (const state of ['windup', 'attack', 'stun', 'dead']) expect(enemyFrameKey(enemy(kind, { state }), 1, false, has)).toMatch(new RegExp(`^enemy\\.${kind}\\.[01]$`));
    }
  });
});

describe('frames with release art (enemy.<kind>.<action>.<n>)', () => {
  const has = release('slime', ENEMY_ACTIONS);

  it('idle loops its 2 frames, move its 4', () => {
    const idle = new Set();
    const move = new Set();
    for (let t = 0; t < 3; t += 0.05) {
      idle.add(enemyFrameKey(enemy('slime'), t, false, has));
      move.add(enemyFrameKey(enemy('slime'), t, true, has));
    }
    expect([...idle].sort()).toEqual(['enemy.slime.idle.0', 'enemy.slime.idle.1']);
    expect([...move].sort()).toEqual(['enemy.slime.move.0', 'enemy.slime.move.1', 'enemy.slime.move.2', 'enemy.slime.move.3']);
  });

  it('the wind-up is split over its frames by progress (wind-up by pose)', () => {
    const w = ENEMY_KINDS.slime.windupMs;
    expect(enemyFrameKey(enemy('slime', { state: 'windup', t: 0 }), 0, false, has)).toBe('enemy.slime.windup.0');
    expect(enemyFrameKey(enemy('slime', { state: 'windup', t: w * 0.6 }), 0, false, has)).toBe('enemy.slime.windup.1');
    expect(enemyFrameKey(enemy('slime', { state: 'windup', t: w * 5 }), 0, false, has)).toBe('enemy.slime.windup.1');
  });

  it('attack plays release then follow-through, and recovery holds the follow-through', () => {
    expect(enemyFrameKey(enemy('slime', { state: 'attack', t: 0 }), 0, true, has)).toBe('enemy.slime.attack.0');
    expect(enemyFrameKey(enemy('slime', { state: 'attack', t: 1000 / V1_FPS.attack + 1 }), 0, true, has)).toBe('enemy.slime.attack.1');
    expect(enemyFrameKey(enemy('slime', { state: 'recover', t: 10 }), 0, false, has)).toBe('enemy.slime.attack.1');
  });

  it('stun shows the flinch frame; death plays the defeat frames and stops on the last', () => {
    expect(enemyFrameKey(enemy('slime', { state: 'stun', t: 50 }), 0, false, has)).toBe('enemy.slime.hurt.0');
    expect(enemyFrameKey(enemy('slime', { state: 'dead', t: 0 }), 0, false, has)).toBe('enemy.slime.defeat.0');
    expect(enemyFrameKey(enemy('slime', { state: 'dead', t: ENEMY_ANIM.defeatPlayMs / 3 + 1 }), 0, false, has)).toBe('enemy.slime.defeat.1');
    expect(enemyFrameKey(enemy('slime', { state: 'dead', t: 5000 }), 0, false, has)).toBe('enemy.slime.defeat.2');
  });

  it('every defeat frame is shown, solid, before the body is removed; then it fades out', () => {
    for (const [kind, actions] of [['slime', ENEMY_ACTIONS], ['boss_root', BOSS_ACTIONS]]) {
      const h = release(kind, actions);
      const shown = new Map(); // frame -> its opacity when it first shows
      for (let t = 0; t < ENEMY_CORPSE_MS; t += 1000 / 60) {
        const e = kind === 'slime' ? enemy('slime', { state: 'dead', t }) : boss({ state: 'dead', t });
        const key = enemyFrameKey(e, 0, false, h);
        if (!shown.has(key)) shown.set(key, defeatAlpha(t));
      }
      expect(shown.size, kind).toBe(actions.defeat);
      for (const [key, a] of shown) expect(a, key).toBe(1);
    }
    expect(defeatAlpha(0)).toBe(1);
    expect(defeatAlpha(ENEMY_CORPSE_MS * 0.8)).toBeGreaterThan(0);
    expect(defeatAlpha(ENEMY_CORPSE_MS * 0.8)).toBeLessThan(1);
    expect(defeatAlpha(ENEMY_CORPSE_MS)).toBe(0);
  });

  it('the archer holds its shot pose just after the orb leaves, and lets go of it even when it loses sight', () => {
    const h = release('archer', ENEMY_ACTIONS);
    expect(enemyFrameKey(enemy('archer'), 0, false, h)).toMatch(/^enemy\.archer\.idle\.\d$/); // never shot
    expect(enemyFrameKey(enemy('archer', { sinceShotMs: 10 }), 0, false, h)).toBe('enemy.archer.attack.0');
    expect(enemyFrameKey(enemy('archer', { sinceShotMs: ENEMY_ANIM.shotPoseMs + 1 }), 0, false, h)).toMatch(/^enemy\.archer\.idle\.\d$/);
    // Shoots, then the player is gone (dead: out of sight): the pose still ends.
    const s = createGameState({ ground: ['##########', '#P.......#', '##########'], enemies: [{ kind: 'archer', tx: 6, ty: 1 }] });
    const e = s.enemies[0];
    Object.assign(e, { state: 'windup', t: ENEMY_KINDS.archer.windupMs });
    updateEnemy(e, s, 1 / 60);
    expect(enemyFrameKey(e, 0, false, h)).toBe('enemy.archer.attack.0');
    s.player.dead = true;
    for (let i = 0; i < 30; i++) updateEnemy(e, s, 1 / 60);
    expect(enemyFrameKey(e, 0, false, h)).toMatch(/^enemy\.archer\.idle\.\d$/);
  });

  it('an action whose frames are missing falls back to idle (art can arrive a little at a time)', () => {
    const partial = release('beast', { idle: 2 });
    expect(enemyFrameKey(enemy('beast', { state: 'windup' }), 0, false, partial)).toBe('enemy.beast.idle.0');
    expect(enemyFrameKey(enemy('beast'), 0, true, partial)).toBe('enemy.beast.idle.0');
  });

  it('frameCount counts consecutive frames', () => {
    expect(frameCount('enemy.slime.move', has)).toBe(4);
    expect(frameCount('enemy.slime.nothing', has)).toBe(0);
  });

  it('with a counts map, each action is counted once (not every frame) until the map is cleared', () => {
    let lookups = 0;
    const counting = (k) => {
      lookups++;
      return has(k);
    };
    const counts = new Map();
    enemyFrameKey(enemy('slime'), 0, true, counting, counts);
    const first = lookups;
    for (let i = 0; i < 100; i++) enemyFrameKey(enemy('slime'), i / 10, true, counting, counts);
    expect(lookups).toBe(first);
    expect(counts.get('enemy.slime.move').n).toBe(4);
    counts.clear();
    enemyFrameKey(enemy('slime'), 0, true, counting, counts);
    expect(lookups).toBe(first * 2);
  });
});

describe('a core of the murk (front-facing, per-pattern actions)', () => {
  const has = release('boss_root', BOSS_ACTIONS);

  it('winds up and attacks with the frames of its pattern', () => {
    expect(enemyFrameKey(boss({ state: 'windup', pattern: 'slam', t: 0 }), 0, false, has)).toBe('enemy.boss_root.windup_slam.0');
    expect(enemyFrameKey(boss({ state: 'windup', pattern: 'charge', t: 700 }), 0, false, has)).toBe('enemy.boss_root.windup_charge.1');
    expect(enemyFrameKey(boss({ state: 'attack', pattern: 'volley', t: 0 }), 0, false, has)).toBe('enemy.boss_root.attack_volley.0');
    expect(enemyFrameKey(boss({ state: 'recover', pattern: 'charge', t: 0 }), 0, false, has)).toBe('enemy.boss_root.attack_charge.1');
  });

  it('stands in idle2 in its second phase; staggers after a parry; flinches otherwise', () => {
    expect(enemyFrameKey(boss({ phase: 2 }), 0, false, has)).toMatch(/^enemy\.boss_root\.idle2\.\d$/);
    expect(enemyFrameKey(boss({ state: 'stun', stunMs: BOSS_PARRY_STUN_MS, t: 0 }), 0, false, has)).toBe('enemy.boss_root.stagger.0');
    expect(enemyFrameKey(boss({ state: 'stun', stunMs: 200, t: 0 }), 0, false, has)).toBe('enemy.boss_root.hurt.0');
    expect(enemyFrameKey(boss({ state: 'dead', t: 99999 }), 0, false, has)).toBe('enemy.boss_root.defeat.3');
  });

  it('a pattern without its own frames falls back to idle; the placeholder core keeps .0/.1', () => {
    expect(enemyFrameKey(boss({ state: 'windup', pattern: 'ring' }), 0, false, has)).toBe('enemy.boss_root.idle.0');
    expect(enemyFrameKey(boss({ state: 'windup', pattern: 'slam' }), 0, false, placeholderOnly('boss_root'))).toBe('enemy.boss_root.0');
  });

  it('enemyAction names the action the art uses', () => {
    expect(enemyAction(boss({ state: 'windup', pattern: 'ring', t: 400 }), false)).toEqual({ action: 'windup_ring', progress: 0.5 });
    expect(enemyAction(enemy('sentinel', { state: 'windup', t: 450 }), false)).toEqual({ action: 'windup', progress: 0.5 });
  });
});

describe('the wind-up warning overlay', () => {
  it('is red #ff3a3a at 50%', () => {
    expect(WARNING_FLASH).toEqual({ color: 0xff3a3a, alpha: 0.5 });
  });

  it('is off outside a wind-up', () => {
    for (const state of ['idle', 'attack', 'recover', 'stun', 'dead']) {
      for (let t = 0; t < 2; t += 0.01) expect(warningFlashAlpha(enemy('sentinel', { state }), t, 0)).toBe(0);
    }
  });

  it('pulses during the wind-up with the same timing as the old tint, faster as the attack nears', () => {
    const e = enemy('sentinel', { state: 'windup' });
    // On exactly when sin(time * (12 + 24 * progress)) > 0.
    for (let t = 0; t < 2; t += 0.013) {
      for (const k of [0, 0.5, 1]) {
        expect(warningFlashAlpha(e, t, k)).toBe(Math.sin(t * (12 + 24 * k)) > 0 ? 0.5 : 0);
      }
    }
    const flips = (k) => {
      let n = 0;
      let last = warningFlashAlpha(e, 0, k);
      for (let t = 0; t < 1; t += 0.001) {
        const a = warningFlashAlpha(e, t, k);
        if (a !== last) n++;
        last = a;
      }
      return n;
    };
    expect(flips(1)).toBeGreaterThan(flips(0) * 2);
  });

  it('follows the enemy wind-up progress (windupProgress) for every kind and for cores', () => {
    for (const kind of ['beast', 'archer', 'slime', 'sentinel']) {
      const e = enemy(kind, { state: 'windup', t: ENEMY_KINDS[kind].windupMs / 2 });
      expect(windupProgress(e)).toBeCloseTo(0.5);
    }
    expect(windupProgress(boss({ state: 'windup', t: 400 }))).toBeCloseTo(0.5);
  });
});

describe('the overlay sprite (flashOverlay.js)', async () => {
  // Pixi stand-ins: enough of Sprite / Texture for placing the overlay without a GPU.
  vi.doMock('pixi.js', () => {
    class Point {
      constructor() {
        this.x = 0;
        this.y = 0;
      }
      copyFrom(p) {
        this.x = p.x;
        this.y = p.y;
      }
      set(x, y) {
        this.x = x;
        this.y = y ?? x;
      }
    }
    class Texture {
      static WHITE = new Texture();
      constructor() {
        this.destroyed = false;
        // (no image behind it: the silhouette falls back to a plain white texture)
        this.source = { resolution: 1, resource: null };
        this.frame = { x: 0, y: 0, width: 8, height: 8 };
      }
      destroy() {
        this.destroyed = true;
      }
    }
    class Sprite {
      constructor(texture) {
        this.texture = texture;
        this.anchor = new Point();
        this.position = new Point();
        this.scale = new Point();
        this.scale.set(1, 1);
        this.alpha = 1;
        this.tint = 0xffffff;
        this.visible = true;
        this.zIndex = 0;
        this.destroyed = false;
      }
      destroy() {
        this.destroyed = true;
      }
    }
    return { Sprite, Texture, Rectangle: class {} };
  });
  const { placeFlash, SilhouetteCache } = await import('../../src/view/flashOverlay.js');
  const { Sprite, Texture } = await import('pixi.js');
  const parent = () => ({ children: [], addChild(c) { this.children.push(c); } });

  it('is not made until the first wind-up flash, then sits exactly over the sprite in red at 50%', () => {
    const cache = new SilhouetteCache();
    const box = parent();
    const spr = new Sprite(new Texture());
    spr.anchor.set(0.5, 1);
    spr.position.set(40, 30);
    spr.scale.set(-1, 1);
    spr.zIndex = 30;
    expect(placeFlash(spr, null, 0, cache, box)).toBe(null);
    expect(box.children).toHaveLength(0);
    const o = placeFlash(spr, null, 0.5, cache, box);
    expect(box.children).toEqual([o]);
    expect(o.tint).toBe(0xff3a3a);
    expect(o.alpha).toBe(0.5);
    expect([o.anchor.x, o.anchor.y, o.position.x, o.position.y, o.scale.x]).toEqual([0.5, 1, 40, 30, -1]);
    expect(o.zIndex).toBeGreaterThan(spr.zIndex);
    expect(o.visible).toBe(true);
    // The sprite's own colour is not touched (no tint multiplied in).
    expect(spr.tint).toBe(0xffffff);
    // Off: hidden, and reused next time (no new sprite).
    expect(placeFlash(spr, o, 0, cache, box)).toBe(o);
    expect(o.visible).toBe(false);
    expect(placeFlash(spr, o, 0.5, cache, box)).toBe(o);
    expect(box.children).toHaveLength(1);
  });

  it('fades with a dying sprite', () => {
    const spr = new Sprite(new Texture());
    spr.alpha = 0.4;
    const o = placeFlash(spr, null, 0.5, new SilhouetteCache(), parent());
    expect(o.alpha).toBeCloseTo(0.2);
  });

  it('makes one silhouette per frame texture and drops it when that texture is gone', () => {
    const cache = new SilhouetteCache();
    const a = new Texture();
    const b = new Texture();
    expect(cache.get(a)).toBe(cache.get(a));
    cache.get(b);
    expect(cache.size).toBe(2);
    a.destroy();
    cache.prune();
    expect(cache.size).toBe(1);
  });
});
