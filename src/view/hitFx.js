// @ts-check
// gfx W5: hit effects drawn in code — a burst of sparks and an expanding ring where a blow lands,
// over several frames (the game had only the 1–2-frame slash). Pooled: a fixed number of sprites
// made once, reused; nothing is allocated per frame. Drawn above the light map so the sparks read at
// night too (they sit on the struck body, so drawing them over a tree in front costs nothing).
import { Container, Sprite, Texture } from 'pixi.js';

/**
 * What each game event shows. sparks: how many; speed px/s; ring: final radius (0 = none);
 * life ms; y: height above the feet.
 * @type {Readonly<Record<string, { sparks: number, color: number, speed: number, ring: number, ringColor: number, life: number, y: number }>>}
 */
export const HIT_FX = Object.freeze({
  hitEnemy: { sparks: 6, color: 0xfff2b0, speed: 90, ring: 9, ringColor: 0xffffff, life: 240, y: 8 },
  enemyDown: { sparks: 10, color: 0xc070e0, speed: 60, ring: 14, ringColor: 0xe070e0, life: 420, y: 6 },
  parry: { sparks: 8, color: 0xbff4ff, speed: 120, ring: 16, ringColor: 0x7fe8ff, life: 320, y: 10 },
  block: { sparks: 4, color: 0xd8e0ea, speed: 70, ring: 8, ringColor: 0xc8d4e4, life: 200, y: 10 },
  hurt: { sparks: 5, color: 0xff6060, speed: 70, ring: 0, ringColor: 0, life: 220, y: 10 },
  bossStun: { sparks: 10, color: 0xfff2b0, speed: 110, ring: 22, ringColor: 0xffffff, life: 380, y: 18 },
});

/** The effect for an event, or null. @param {{ type: string }} ev */
export const fxFor = (ev) => HIT_FX[ev.type] ?? null;

/** The boss an event names. @param {{ enemies?: any[] }} state @param {string} id */
const bossOf = (state, id) => state.enemies?.find((en) => en.bossId === id) ?? null;

/** Pool sizes (the most on screen at once). */
export const FX_POOL = Object.freeze({ sparks: 48, rings: 8 });

/** A ring outline texture (white, 1 px line at 32 px), made once. @returns {Texture} */
function ringTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 32;
  const g = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
  g.strokeStyle = '#ffffff';
  g.lineWidth = 2;
  g.beginPath();
  g.arc(16, 16, 14, 0, Math.PI * 2);
  g.stroke();
  const t = Texture.from(c);
  t.source.scaleMode = 'linear';
  return t;
}

export class HitFx {
  /** @param {Texture} dot a small white square (the 'px' sprite) */
  constructor(dot) {
    this.layer = new Container();
    this.layer.label = 'hit-fx';
    /** @type {{ s: Sprite, x: number, y: number, vx: number, vy: number, age: number, life: number }[]} */
    this.sparks = [];
    for (let i = 0; i < FX_POOL.sparks; i++) {
      const s = new Sprite(dot);
      s.anchor.set(0.5);
      s.visible = false;
      s.blendMode = 'add';
      this.layer.addChild(s);
      this.sparks.push({ s, x: 0, y: 0, vx: 0, vy: 0, age: 0, life: 0 });
    }
    const ring = typeof document === 'undefined' ? Texture.WHITE : ringTexture();
    /** @type {{ s: Sprite, r: number, age: number, life: number }[]} */
    this.rings = [];
    for (let i = 0; i < FX_POOL.rings; i++) {
      const s = new Sprite(ring);
      s.anchor.set(0.5);
      s.visible = false;
      this.layer.addChild(s);
      this.rings.push({ s, r: 0, age: 0, life: 0 });
    }
    this.nextSpark = 0;
    this.nextRing = 0;
    /** The last game tick whose events were shown. */
    this.lastTick = -1;
    this.active = 0;
  }

  /**
   * Starts the effects of the events that came since the last call.
   * @param {{ tick: number, events: any[], enemies?: any[] }} state
   */
  takeEvents(state) {
    const ev = state.events;
    for (let j = 0; j < ev.length; j++) {
      const e = ev[j];
      if (e.tick <= this.lastTick) continue;
      const spec = fxFor(e);
      if (!spec) continue;
      // where: the event's own place, or (a boss stunned by a parry: `id` only) the boss's
      const at = typeof e.x === 'number' ? e : e.id !== undefined ? bossOf(state, e.id) : null;
      if (at) this.burst(at.x, at.y - (at.z ?? 0) - spec.y, spec);
    }
    this.lastTick = state.tick;
  }

  /** @param {number} x @param {number} y @param {typeof HIT_FX.hitEnemy} spec */
  burst(x, y, spec) {
    for (let k = 0; k < spec.sparks; k++) {
      const p = this.sparks[this.nextSpark];
      this.nextSpark = (this.nextSpark + 1) % this.sparks.length;
      const a = (k / spec.sparks) * Math.PI * 2 + Math.random() * 0.6;
      const v = spec.speed * (0.6 + Math.random() * 0.6);
      p.x = x;
      p.y = y;
      p.vx = Math.cos(a) * v;
      p.vy = Math.sin(a) * v - 20;
      p.age = 0;
      p.life = spec.life * (0.7 + Math.random() * 0.3);
      p.s.tint = spec.color;
      p.s.visible = true;
    }
    if (spec.ring > 0) {
      const r = this.rings[this.nextRing];
      this.nextRing = (this.nextRing + 1) % this.rings.length;
      r.s.position.set(x, y);
      r.r = spec.ring;
      r.age = 0;
      r.life = spec.life;
      r.s.tint = spec.ringColor;
      r.s.visible = true;
    }
  }

  /** Moves and fades what is alive. @param {number} dt seconds */
  update(dt) {
    const ms = dt * 1000;
    let active = 0;
    for (let i = 0; i < this.sparks.length; i++) {
      const p = this.sparks[i];
      if (!p.s.visible) continue;
      p.age += ms;
      if (p.age >= p.life) {
        p.s.visible = false;
        continue;
      }
      active++;
      const k = p.age / p.life;
      p.vy += 160 * dt; // they fall a little
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.s.position.set(Math.round(p.x), Math.round(p.y));
      // 2×2 → 1×1 game px as they burn out (frame by frame, not a smooth scale)
      const size = k < 0.5 ? 1 : 0.5;
      p.s.scale.set(size);
      p.s.alpha = 1 - k * k;
    }
    for (let i = 0; i < this.rings.length; i++) {
      const r = this.rings[i];
      if (!r.s.visible) continue;
      r.age += ms;
      if (r.age >= r.life) {
        r.s.visible = false;
        continue;
      }
      active++;
      const k = r.age / r.life;
      const size = (r.r * 2 * (0.3 + 0.7 * Math.sqrt(k))) / 32;
      r.s.scale.set(size);
      r.s.alpha = 0.9 * (1 - k);
    }
    this.active = active;
  }
}
