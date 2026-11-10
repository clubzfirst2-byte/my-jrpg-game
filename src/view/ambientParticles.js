// @ts-check
// gfx W5: small life in the air — drifting leaves in the forest and in autumn, dust motes in the
// sunlight, fireflies over water at night, sparkles on snow. Cheap: a fixed pool of tiny sprites
// made once (one shared white dot), at most AMBIENT.max on screen (plus AMBIENT.mist soft patches of
// mist in the rain and at dawn), positions in world px (the layers
// follow the world's camera transform). Fireflies glow: they are drawn above the light map; the rest
// are lit like the world. Which kinds show is pure (unit-tested).
import { Container, Sprite } from 'pixi.js';

export const AMBIENT = Object.freeze({
  /** pool size per layer (the most of each layer on screen) */
  max: 40,
  leaves: 14,
  motes: 12,
  fireflies: 14,
  sparkles: 18,
  /** soft drifting patches of mist (large and faint: few, for the fill they cost) */
  mist: 5,
});

/** The morning mist's hours. */
export const MIST_DAWN = Object.freeze({ from: 5, to: 7.5 });

/** Leaf colours: summer forest, autumn. */
const LEAF = Object.freeze({ summer: [0x3f8a46, 0x5fa64e, 0x2c6a3e], autumn: [0xd9822b, 0xa5481f, 0xf0c04a, 0xc0461c] });

/**
 * Which ambient particles show here and now, and how many.
 * @param {{ region: string | null, season: string, dark: boolean, day: boolean, weather: string, indoor: boolean, nearWater: boolean, snowGround: boolean, hour?: number }} c
 * @returns {{ leaves: number, motes: number, fireflies: number, sparkles: number, mist: number, autumn: boolean }}
 */
export function ambientKinds(c) {
  const none = { leaves: 0, motes: 0, fireflies: 0, sparkles: 0, mist: 0, autumn: false };
  if (c.indoor) return none;
  const wet = c.weather === 'rain' || c.weather === 'storm';
  const autumn = c.season === 'autumn';
  const winter = c.season === 'winter';
  const forest = c.region === 'forest';
  const dawn = c.hour !== undefined && c.hour >= MIST_DAWN.from && c.hour < MIST_DAWN.to;
  return {
    leaves: !wet && !winter && (forest || autumn) ? AMBIENT.leaves : 0,
    motes: c.day && c.weather === 'clear' && !winter && !forest ? AMBIENT.motes : 0,
    fireflies: c.dark && !wet && !winter && c.nearWater ? AMBIENT.fireflies : 0,
    sparkles: c.day && (winter || c.snowGround) && !wet ? AMBIENT.sparkles : 0,
    // mist: in the rain, and at dawn in fair weather (not over the desert)
    mist: wet || (dawn && c.weather !== 'snow' && c.region !== 'desert') ? AMBIENT.mist : 0,
    autumn,
  };
}

/**
 * @typedef {{ s: Sprite, kind: number, x: number, y: number, vx: number, vy: number, phase: number, age: number, life: number }} Mote
 */
/** The mist's strongest opacity (the texture's centre). */
export const MIST_ALPHA = 0.15;
const LEAF_K = 1;
const MOTE_K = 2;
const FLY_K = 3;
const SPARK_K = 4;
const MIST_K = 5;

export class AmbientParticles {
  /**
   * @param {import('pixi.js').Texture} dot a small white square ('px', 2×2 game px)
   * @param {import('pixi.js').Texture} [soft] a soft white oval (the cast shadows' texture) for the mist
   */
  constructor(dot, soft) {
    /** lit like the world (under the light map) */
    this.under = new Container();
    this.under.label = 'ambient';
    /** glowing (over the light map) */
    this.glow = new Container();
    this.glow.label = 'ambient-glow';
    /** @type {Mote[]} */
    this.pool = [];
    /** @type {Mote[]} */
    this.glowPool = [];
    for (let i = 0; i < AMBIENT.max; i++) {
      const s = new Sprite(dot);
      s.anchor.set(0.5);
      s.visible = false;
      this.under.addChild(s);
      this.pool.push({ s, kind: 0, x: 0, y: 0, vx: 0, vy: 0, phase: 0, age: 0, life: 0 });
    }
    for (let i = 0; i < AMBIENT.fireflies; i++) {
      const s = new Sprite(dot);
      s.anchor.set(0.5);
      s.visible = false;
      s.blendMode = 'add';
      this.glow.addChild(s);
      this.glowPool.push({ s, kind: 0, x: 0, y: 0, vx: 0, vy: 0, phase: 0, age: 0, life: 0 });
    }
    /** mist: its own few sprites, under the small particles @type {Mote[]} */
    this.mistPool = [];
    for (let i = 0; soft && i < AMBIENT.mist; i++) {
      const s = new Sprite(soft);
      s.anchor.set(0.5);
      s.visible = false;
      s.tint = 0xdfe8f2;
      this.under.addChildAt(s, 0);
      this.mistPool.push({ s, kind: 0, x: 0, y: 0, vx: 0, vy: 0, phase: 0, age: 0, life: 0 });
    }
    this.visible = 0;
  }

  /**
   * @param {ReturnType<typeof ambientKinds>} kinds
   * @param {{ x: number, y: number, w: number, h: number }} view the world rect on screen
   * @param {(x: number, y: number) => boolean} nearWater whether a world point is by water (fireflies)
   * @param {number} timeSec @param {number} dt seconds
   */
  update(kinds, view, nearWater, timeSec, dt) {
    let shown = 0;
    // The under-layer pool is shared: leaves first, then motes, then sparkles.
    let i = 0;
    i = this.run(this.pool, i, kinds.leaves, LEAF_K, kinds, view, nearWater, timeSec, dt);
    i = this.run(this.pool, i, kinds.motes, MOTE_K, kinds, view, nearWater, timeSec, dt);
    i = this.run(this.pool, i, kinds.sparkles, SPARK_K, kinds, view, nearWater, timeSec, dt);
    shown += i;
    for (let j = i; j < this.pool.length; j++) this.pool[j].s.visible = false;
    const f = this.run(this.glowPool, 0, kinds.fireflies, FLY_K, kinds, view, nearWater, timeSec, dt);
    for (let j = f; j < this.glowPool.length; j++) this.glowPool[j].s.visible = false;
    const mi = this.run(this.mistPool, 0, kinds.mist, MIST_K, kinds, view, nearWater, timeSec, dt);
    for (let j = mi; j < this.mistPool.length; j++) this.mistPool[j].s.visible = false;
    this.visible = shown + f + mi;
  }

  /**
   * Runs `count` particles of one kind from slot `from`; returns the next free slot.
   * @param {Mote[]} pool @param {number} from @param {number} count @param {number} kind
   * @param {ReturnType<typeof ambientKinds>} kinds @param {{ x: number, y: number, w: number, h: number }} v
   * @param {(x: number, y: number) => boolean} nearWater @param {number} t @param {number} dt
   */
  run(pool, from, count, kind, kinds, v, nearWater, t, dt) {
    const end = Math.min(pool.length, from + count);
    for (let i = from; i < end; i++) {
      const m = pool[i];
      const pad = kind === MIST_K ? 80 : 24;
      const out = m.x < v.x - pad || m.x > v.x + v.w + pad || m.y < v.y - pad || m.y > v.y + v.h + pad;
      if (m.kind !== kind || m.age >= m.life || out) this.spawn(m, kind, kinds, v, nearWater);
      m.age += dt * 1000;
      const k = m.age / m.life;
      const s = m.s;
      s.visible = true;
      if (kind === LEAF_K) {
        // drifting down and sideways, swaying, the leaf flipping (its height pulses)
        m.x += (m.vx + Math.sin(t * 2.1 + m.phase) * 14) * dt;
        m.y += m.vy * dt;
        s.scale.set(1, Math.abs(Math.sin(t * 5 + m.phase)) * 0.5 + 0.25);
        s.alpha = Math.min(1, (1 - k) * 4, k * 6);
      } else if (kind === MOTE_K) {
        m.x += (m.vx + Math.sin(t * 0.7 + m.phase) * 3) * dt;
        m.y += (m.vy + Math.cos(t * 0.9 + m.phase) * 2) * dt;
        s.scale.set(0.5);
        s.alpha = 0.55 * Math.max(0, Math.sin(Math.PI * k));
      } else if (kind === FLY_K) {
        m.x += Math.sin(t * 1.3 + m.phase) * 9 * dt;
        m.y += Math.cos(t * 1.1 + m.phase * 1.7) * 6 * dt;
        s.scale.set(1); // (a 2-px glow: they are lights)
        s.alpha = Math.max(0, Math.sin(t * 2.4 + m.phase)) * Math.max(0, Math.sin(Math.PI * k));
      } else if (kind === MIST_K) {
        // a wide, faint patch drifting sideways, fading in and out
        m.x += m.vx * dt;
        s.alpha = MIST_ALPHA * Math.max(0, Math.sin(Math.PI * k));
      } else {
        // a glint on the snow: on, then off
        s.scale.set(0.5);
        s.alpha = Math.max(0, Math.sin(Math.PI * k * 2)) * 0.9;
      }
      s.position.set(Math.round(m.x), Math.round(m.y));
    }
    return end;
  }

  /**
   * @param {Mote} m @param {number} kind @param {ReturnType<typeof ambientKinds>} kinds
   * @param {{ x: number, y: number, w: number, h: number }} v @param {(x: number, y: number) => boolean} nearWater
   */
  spawn(m, kind, kinds, v, nearWater) {
    const r = Math.random;
    m.kind = kind;
    m.age = 0;
    m.phase = r() * 6.28;
    m.x = v.x + r() * v.w;
    m.y = v.y + r() * v.h;
    if (kind === LEAF_K) {
      const pal = kinds.autumn ? LEAF.autumn : LEAF.summer;
      m.s.tint = pal[Math.floor(r() * pal.length)];
      m.y = v.y - 8 + r() * v.h * 0.6; // they fall into view
      m.vx = 6 + r() * 10;
      m.vy = 10 + r() * 8;
      m.life = 4000 + r() * 4000;
    } else if (kind === MOTE_K) {
      m.s.tint = 0xfff6d8;
      m.vx = (r() - 0.5) * 4;
      m.vy = -2 - r() * 3;
      m.life = 3000 + r() * 3000;
    } else if (kind === FLY_K) {
      m.s.tint = 0xd8ff70;
      m.vx = 0;
      m.vy = 0;
      m.life = 4000 + r() * 4000;
      // near water: try a few places; else wait (invisible) for the next spawn
      let ok = false;
      for (let k = 0; k < 6 && !ok; k++) {
        m.x = v.x + r() * v.w;
        m.y = v.y + r() * v.h;
        ok = nearWater(m.x, m.y);
      }
      if (!ok) m.life = 300;
      if (!ok) m.x = v.x - 1000; // off-screen until it finds water
    } else if (kind === MIST_K) {
      m.vx = (r() < 0.5 ? -1 : 1) * (3 + r() * 4);
      m.vy = 0;
      m.life = 7000 + r() * 6000;
      m.age = r() * 2000; // (not all in step)
      m.s.width = 96 + Math.round(r() * 48);
      m.s.height = 26 + Math.round(r() * 12);
    } else {
      m.s.tint = 0xffffff;
      m.vx = 0;
      m.vy = 0;
      m.life = 600 + r() * 900;
    }
  }
}
