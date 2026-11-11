// @ts-check
// gfx W5: hit effects drawn in code — a burst of sparks and an expanding ring where a blow lands,
// over several frames (the game had only the 1–2-frame slash). Pixel art like the rest: the ring is
// a 1-game-px circle drawn on the game's pixel grid, in 4 frames (small → full size), white turning
// yellow; the sparks are 2×2 then 1×1 game px, white → yellow → orange, fully opaque until they go
// out (a faded spark over grass read as a flower dot). Pooled: a fixed number of sprites made once,
// reused; nothing is allocated per frame; a sprite not in use is hidden, so it is not gathered when
// the scene's draw list is rebuilt (it changes only around a blow, when the fight rebuilds that list
// anyway). Drawn above the light map so the sparks read at night too
// (they sit on the struck body, so drawing them over a tree in front costs nothing).
import { Container, Sprite, Texture } from 'pixi.js';
import { atlasFrame, whiteRGBA } from './pixelAtlas.js';

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

/**
 * The ring's frames: its radius as a share of the full radius, its colour (the white ring of a blow
 * turns a light yellow; a coloured one — parry, defeat — keeps its colour), fully opaque so it reads
 * on grass and on a dirt path alike; the last frame is a dotted ring (every other pixel) as it goes out.
 */
export const RING_FRAMES = Object.freeze([
  Object.freeze({ r: 0.4, warm: 0xffffff, alpha: 1, dotted: false }),
  Object.freeze({ r: 0.65, warm: 0xfffbd8, alpha: 1, dotted: false }),
  Object.freeze({ r: 0.85, warm: 0xfff27a, alpha: 1, dotted: false }),
  Object.freeze({ r: 1, warm: 0xfff27a, alpha: 1, dotted: true }),
]);

/**
 * The ring's pixels in order around it (from the right, clockwise on screen), so a dotted ring can
 * keep every other one. Pure.
 * @param {number} r
 */
export const ringPixelsInOrder = (r) => ringPixels(r).sort((a, b) => Math.atan2(a[1], a[0]) - Math.atan2(b[1], b[0]));
/** A spark's colour as it burns out (by its age, 0..1): white, yellow, orange — never faded. */
export const SPARK_STEPS = Object.freeze([
  Object.freeze({ until: 0.35, color: 0xffffff, size: 1 }),
  Object.freeze({ until: 0.7, color: 0xfff060, size: 1 }),
  Object.freeze({ until: 1, color: 0xffa030, size: 0.5 }),
]);

/** The step of a spark at age k (0..1). @param {number} k */
export const sparkStep = (k) => SPARK_STEPS.find((s) => k < s.until) ?? SPARK_STEPS[SPARK_STEPS.length - 1];

/**
 * A 1-px circle outline of radius r on a pixel grid (the midpoint circle): the pixels set, as
 * [x, y] from its centre. Pure.
 * @param {number} r whole game px
 * @returns {[number, number][]}
 */
export function ringPixels(r) {
  /** @type {[number, number][]} */
  const out = [];
  const seen = new Set();
  const put = (/** @type {number} */ x, /** @type {number} */ y) => {
    const k = `${x},${y}`;
    if (seen.has(k)) return;
    seen.add(k);
    out.push([x, y]);
  };
  let x = r;
  let y = 0;
  let d = 1 - r;
  while (x >= y) {
    for (const [a, b] of [[x, y], [y, x], [-y, x], [-x, y], [-x, -y], [-y, -x], [y, -x], [x, -y]]) put(a, b);
    y++;
    if (d < 0) d += 2 * y + 1;
    else {
      x--;
      d += 2 * (y - x) + 1;
    }
  }
  return out;
}

/** A white 1-game-px ring of radius r (2r+1 game px square, on the effects' atlas); dotted: every other pixel. @param {number} r @param {boolean} [dotted] */
function ringTexture(r, dotted = false) {
  const n = 2 * r + 1;
  return atlasFrame(`ring:${r}${dotted ? ':dot' : ''}`, n, n, () => {
    const a = new Uint8ClampedArray(n * n);
    ringPixelsInOrder(r).forEach(([x, y], i) => {
      if (!dotted || i % 2 === 0) a[(y + r) * n + x + r] = 255;
    });
    return whiteRGBA(a, n * n);
  });
}

/** Pool sizes (the most on screen at once). */
export const FX_POOL = Object.freeze({ sparks: 48, rings: 8 });

export class HitFx {
  /** @param {Texture} dot a small white square (the 'px' sprite) */
  constructor(dot) {
    this.layer = new Container();
    this.layer.label = 'hit-fx';
    /** @type {{ s: Sprite, live: boolean, x: number, y: number, vx: number, vy: number, age: number, life: number, warm: boolean }[]} */
    this.sparks = [];
    for (let i = 0; i < FX_POOL.sparks; i++) {
      const s = new Sprite(dot);
      s.anchor.set(0.5);
      s.visible = false;
      this.layer.addChild(s);
      this.sparks.push({ s, live: false, x: 0, y: 0, vx: 0, vy: 0, age: 0, life: 0, warm: false });
    }
    /** @type {{ s: Sprite, live: boolean, r: number, age: number, life: number, color: number, frame: number }[]} */
    this.rings = [];
    for (let i = 0; i < FX_POOL.rings; i++) {
      const s = new Sprite(Texture.WHITE);
      s.anchor.set(0.5);
      s.visible = false;
      this.layer.addChild(s);
      this.rings.push({ s, live: false, r: 0, age: 0, life: 0, color: 0xffffff, frame: -1 });
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
      p.x = Math.round(x);
      p.y = Math.round(y);
      p.vx = Math.cos(a) * v;
      p.vy = Math.sin(a) * v - 20;
      p.age = 0;
      p.life = spec.life * (0.7 + Math.random() * 0.3);
      p.s.tint = spec.color;
      p.warm = spec.color === 0xfff2b0;
      p.s.alpha = 1;
      p.s.scale.set(1);
      p.s.visible = true;
      p.live = true;
    }
    if (spec.ring > 0) {
      const r = this.rings[this.nextRing];
      this.nextRing = (this.nextRing + 1) % this.rings.length;
      r.s.position.set(Math.round(x), Math.round(y));
      r.r = spec.ring;
      r.age = 0;
      r.life = spec.life;
      r.color = spec.ringColor;
      r.frame = -1;
      r.s.visible = true;
      r.live = true;
      this.ringFrame(r, 0);
    }
  }

  /** Moves and fades what is alive. @param {number} dt seconds */
  update(dt) {
    const ms = dt * 1000;
    let active = 0;
    for (let i = 0; i < this.sparks.length; i++) {
      const p = this.sparks[i];
      if (!p.live) continue;
      p.age += ms;
      if (p.age >= p.life) {
        p.live = false;
        p.s.visible = false;
        continue;
      }
      active++;
      const k = p.age / p.life;
      p.vy += 160 * dt; // they fall a little
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.s.position.set(Math.round(p.x), Math.round(p.y));
      // white → yellow → orange, 2×2 → 1×1 game px, opaque until it goes out (no fade to a dull dot)
      const st = sparkStep(k);
      p.s.scale.set(st.size);
      if (p.warm && k >= SPARK_STEPS[0].until) p.s.tint = st.color; // (coloured sparks keep their colour)
    }
    for (let i = 0; i < this.rings.length; i++) {
      const r = this.rings[i];
      if (!r.live) continue;
      r.age += ms;
      if (r.age >= r.life) {
        r.live = false;
        r.s.visible = false;
        continue;
      }
      active++;
      this.ringFrame(r, Math.min(RING_FRAMES.length - 1, Math.floor((r.age / r.life) * RING_FRAMES.length)));
    }
    this.active = active;
  }

  /**
   * Shows a ring's frame f (RING_FRAMES): a ring of whole game px, on the pixel grid.
   * @param {{ s: Sprite, r: number, color: number, frame: number }} r @param {number} f
   */
  ringFrame(r, f) {
    if (r.frame === f) return;
    r.frame = f;
    const F = RING_FRAMES[f];
    const rad = Math.max(2, Math.round(r.r * F.r));
    r.s.texture = ringTexture(rad, F.dotted);
    r.s.scale.set(1);
    if (r.s.texture === Texture.WHITE) r.s.scale.set((2 * rad + 1) / Texture.WHITE.width);
    // a blow's white ring warms to yellow; a coloured one (parry, defeat) keeps its colour
    r.s.tint = r.color === 0xffffff ? F.warm : r.color;
    r.s.alpha = F.alpha;
  }
}
