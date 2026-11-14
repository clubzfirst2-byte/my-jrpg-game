// @ts-check
// Shows the wind of the map (volume phase 1; stand-in drawing until the art is made): streaks
// sliding along each wind lane, and wisps rising in each updraft. Only what is near the view is
// drawn, from a fixed pool of sprites (the white pixel of the atlas, tinted): nothing is created
// or destroyed while playing. Reads state only.
/** @typedef {import('pixi.js').Sprite} Sprite @typedef {import('pixi.js').Container} Container */

const POOL = 48;
/** Streaks per 100 tiles of lane / wisps per 16 tiles of updraft (kept low: it is weather, not a wall). */
const LANE_DENSITY = 0.09;
const UP_DENSITY = 0.5;
const LANE_PERIOD = 1.6;
const UP_PERIOD = 1.4;
const COLOR = 0xeaf6ff;

/** @param {number} n */
const frac = (n) => n - Math.floor(n);
/** A steady pseudo-random number in 0..1 for an index. @param {number} k @param {number} s */
const rnd = (k, s) => frac(Math.sin(k * 127.1 + s * 311.7) * 43758.5453);

export class WindView {
  /**
   * @param {(key: string) => Sprite} makeSprite
   * @param {Container} layer world-space layer above the actors
   * @param {import('../game/state.js').GameState} state
   */
  constructor(makeSprite, layer, state) {
    this.map = state.map;
    this.winds = state.winds ?? [];
    this.updrafts = state.updrafts ?? [];
    /** @type {Sprite[]} */
    this.pool = [];
    if (this.winds.length + this.updrafts.length === 0) return;
    for (let i = 0; i < POOL; i++) {
      const s = makeSprite('px');
      s.tint = COLOR;
      s.visible = false;
      s.zIndex = 2e6;
      layer.addChild(s);
      this.pool.push(s);
    }
  }

  /**
   * @param {{ x: number, y: number }} origin camera top-left (world px)
   * @param {number} viewW @param {number} viewH world px
   * @param {number} timeSec
   */
  update(origin, viewW, viewH, timeSec) {
    if (this.pool.length === 0) return;
    const ts = this.map.tileSize;
    let used = 0;
    const near = (/** @type {{ tx: number, ty: number, tw: number, th: number }} */ r) =>
      r.tx * ts < origin.x + viewW + 32 && (r.tx + r.tw) * ts > origin.x - 32 && r.ty * ts < origin.y + viewH + 32 && (r.ty + r.th) * ts > origin.y - 96;
    const elevAt = (/** @type {number} */ x, /** @type {number} */ y) => {
      const tx = Math.min(this.map.width - 1, Math.max(0, Math.floor(x / ts)));
      const ty = Math.min(this.map.height - 1, Math.max(0, Math.floor(y / ts)));
      return this.map.elev[ty * this.map.width + tx];
    };
    this.winds.forEach((w, wi) => {
      if (!near(w)) return;
      const n = Math.max(2, Math.round(w.tw * w.th * LANE_DENSITY));
      const along = (w.dx ? w.tw : w.th) * ts;
      const across = (w.dx ? w.th : w.tw) * ts;
      for (let k = 0; k < n && used < this.pool.length; k++) {
        const t = frac(timeSec / LANE_PERIOD + rnd(k, wi));
        const a = t * along;
        const c = rnd(k, wi + 7) * across;
        const dir = w.dx + w.dy;
        const x = w.tx * ts + (w.dx ? (dir > 0 ? a : along - a) : c);
        const y = w.ty * ts + (w.dy ? (dir > 0 ? a : along - a) : c);
        const s = this.pool[used++];
        s.visible = true;
        s.width = w.dx ? 10 : 1;
        s.height = w.dx ? 1 : 10;
        s.alpha = 0.55 * Math.sin(t * Math.PI);
        s.position.set(Math.round(x), Math.round(y - elevAt(x, y) - 10));
      }
    });
    this.updrafts.forEach((u, ui) => {
      if (!near(u)) return;
      const n = Math.max(3, Math.round(u.tw * u.th * UP_DENSITY));
      const rise = Math.min(u.lift ?? 112, 64);
      for (let k = 0; k < n && used < this.pool.length; k++) {
        const t = frac(timeSec / UP_PERIOD + rnd(k, ui + 3));
        const x = (u.tx + rnd(k, ui + 11) * u.tw) * ts;
        const y = (u.ty + rnd(k, ui + 17) * u.th) * ts;
        const s = this.pool[used++];
        s.visible = true;
        s.width = 1;
        s.height = 7;
        s.alpha = 0.6 * Math.sin(t * Math.PI);
        s.position.set(Math.round(x + Math.sin(t * 6 + k) * 2), Math.round(y - elevAt(x, y) - t * rise));
      }
    });
    for (let i = used; i < this.pool.length; i++) this.pool[i].visible = false;
  }
}
