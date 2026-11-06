import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { HERO_ANIMS, HeroAnimator, poseOf, LAND_MS } from '../../src/view/heroAnim.js';
import { COMBAT, SWORD } from '../../src/game/entities/playerCombat.js';

// The hero's animation (release art): which action and frame for the player's state.
const base = () => ({ grounded: true, moving: false, dashing: false, walkTime: 0, action: 'none', actionMs: 0, comboIndex: 0, vz: 0, knockMs: 0, dead: false });
const alive = { deathMs: -1 };

describe('hero animation: actions from the player state', () => {
  it('the frame counts follow the approved spec', () => {
    expect(HERO_ANIMS.idle.frames).toBe(4);
    expect(HERO_ANIMS.walk.frames).toBe(6);
    expect(HERO_ANIMS.run.frames).toBe(6);
    expect(HERO_ANIMS.attack1.frames).toBeGreaterThanOrEqual(4);
    expect(HERO_ANIMS.attack3.frames).toBeLessThanOrEqual(6);
    expect(HERO_ANIMS.down.frames).toBe(4);
  });

  it('idle breathes on the clock; walking and running follow the distance walked', () => {
    expect(poseOf(base(), alive, 0, Infinity)).toEqual({ action: 'idle', frame: 0 });
    expect(poseOf(base(), alive, 0.3, Infinity).frame).toBe(1);
    const walking = { ...base(), moving: true, walkTime: 0.25 };
    expect(poseOf(walking, alive, 0, Infinity)).toEqual({ action: 'walk', frame: 2 });
    const running = { ...walking, dashing: true };
    expect(poseOf(running, alive, 0, Infinity).action).toBe('run');
  });

  it('every walk / run / idle frame comes up in a cycle', () => {
    for (const [action, p] of [
      ['walk', { moving: true }],
      ['run', { moving: true, dashing: true }],
    ]) {
      const seen = new Set();
      for (let t = 0; t < 2; t += 0.01) seen.add(poseOf({ ...base(), ...p, walkTime: t }, alive, 0, Infinity).frame);
      expect(seen.size, action).toBe(HERO_ANIMS[action].frames);
    }
    const idle = new Set();
    for (let t = 0; t < 2; t += 0.05) idle.add(poseOf(base(), alive, t, Infinity).frame);
    expect(idle.size).toBe(4);
  });

  it('actions play once over their own duration', () => {
    const sw = SWORD[2];
    const total = sw.startupMs + sw.activeMs + sw.recoveryMs;
    const frames = [0, 0.2, 0.4, 0.6, 0.8, 0.99].map((k) => poseOf({ ...base(), action: 'attack', comboIndex: 2, actionMs: k * total }, alive, 0, Infinity));
    expect(frames.map((f) => f.action)).toEqual(Array(6).fill('attack3'));
    expect(frames.map((f) => f.frame)).toEqual([0, 1, 2, 3, 4, 5]);
    expect(poseOf({ ...base(), action: 'dodge', actionMs: COMBAT.dodgeMs * 0.99 }, alive, 0, Infinity)).toEqual({ action: 'dodge', frame: 3 });
    expect(poseOf({ ...base(), action: 'aim', actionMs: 0 }, alive, 0, Infinity)).toEqual({ action: 'bow', frame: 0 });
    expect(poseOf({ ...base(), action: 'aim', actionMs: COMBAT.bowDrawMs + 50 }, alive, 0, Infinity)).toEqual({ action: 'bow', frame: 3 });
  });

  it('states take priority: down > swim/climb/glide > hurt > attack > air > land > guard > move', () => {
    expect(poseOf(base(), { deathMs: 500 }, 0, Infinity)).toEqual({ action: 'down', frame: 3 });
    expect(poseOf({ ...base(), swimming: true }, alive, 0, Infinity).action).toBe('swim');
    expect(poseOf({ ...base(), climbing: true, grounded: false }, alive, 0, Infinity).action).toBe('climb');
    expect(poseOf({ ...base(), gliding: true, grounded: false }, alive, 0, Infinity).action).toBe('glide');
    expect(poseOf({ ...base(), knockMs: 150, action: 'attack' }, alive, 0, Infinity).action).toBe('hurt');
    expect(poseOf({ ...base(), grounded: false, vz: 50 }, alive, 0, Infinity)).toEqual({ action: 'jump', frame: 0 });
    expect(poseOf({ ...base(), grounded: false, vz: -50 }, alive, 0, Infinity)).toEqual({ action: 'jump', frame: 1 });
    expect(poseOf(base(), alive, 0, 10).action).toBe('land');
    expect(poseOf({ ...base(), guarding: true, guardMs: 200 }, alive, 0, Infinity)).toEqual({ action: 'guard', frame: 1 });
  });

  it('the animator notices a landing', () => {
    const a = new HeroAnimator();
    a.update({ ...base(), grounded: false, vz: -10 }, alive, 0, 16);
    expect(a.update(base(), alive, 0, 16).action).toBe('land');
    expect(a.update(base(), alive, 0, LAND_MS).action).toBe('idle');
  });

  it('missing release frames fall back to idle / walk release art, then to the placeholder (null)', () => {
    const a = new HeroAnimator();
    const has = (k) => k.startsWith('hero.idle.') || k.startsWith('hero.walk.');
    expect(a.textureKey({ action: 'attack1', frame: 2 }, 'down', false, has)).toBe('hero.idle.down.0');
    expect(a.textureKey({ action: 'run', frame: 2 }, 'left', true, has)).toBe('hero.walk.left.0');
    expect(a.textureKey({ action: 'walk', frame: 4 }, 'up', true, has)).toBe('hero.walk.up.4');
    expect(a.textureKey({ action: 'idle', frame: 0 }, 'up', false, () => false)).toBeNull();
  });
});

describe('release hero art (src/art-release/hero)', () => {
  const DIR = new URL('../../src/art-release/hero/', import.meta.url);
  const files = readdirSync(DIR).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
  const size = (name) => {
    const buf = readFileSync(new URL(`${name}.png`, DIR));
    return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
  };

  it('stage 1: idle 4, walk 6, run 6 in all four directions, 32×56', () => {
    for (const action of ['idle', 'walk', 'run']) {
      for (const d of ['down', 'up', 'right', 'left']) {
        for (let i = 0; i < HERO_ANIMS[action].frames; i++) {
          const name = `hero.${action}.${d}.${i}`;
          expect(files, name).toContain(name);
          expect(size(name), name).toEqual([32, 56]);
        }
      }
    }
  });

  it('every frame of a cycle is a different picture', () => {
    for (const action of ['idle', 'walk', 'run']) {
      for (const d of ['down', 'up', 'right']) {
        const pics = new Set();
        for (let i = 0; i < HERO_ANIMS[action].frames; i++) pics.add(readFileSync(new URL(`hero.${action}.${d}.${i}.png`, DIR)).toString('base64'));
        expect(pics.size, `${action} ${d}`).toBe(HERO_ANIMS[action].frames);
      }
    }
  });

  it('only release names (no other files)', () => {
    for (const f of files) expect(f).toMatch(/^hero\.[a-z0-9]+\.(down|up|right|left)\.\d+$/);
  });
});
