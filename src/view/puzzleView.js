// @ts-check
// Puzzle visuals (P7): pressure plates and light sensors (pressed / lit), vine platforms, the light
// orb (灯火) and the resonance ring (共鳴). Reads state only.
import { Container, Graphics } from 'pixi.js';
import { ABILITY } from '../game/puzzles/abilities.js';

export class PuzzleView {
  /**
   * @param {(key: string) => import('pixi.js').Sprite} makeSprite
   * @param {(key: string) => import('pixi.js').Texture} texture
   * @param {Container} ground  flat layer under the actors
   * @param {Container} actors
   * @param {Container} overlay
   * @param {import('../game/state.js').GameState} state
   */
  constructor(makeSprite, texture, ground, actors, overlay, state) {
    this.texture = texture;
    this.makeSprite = makeSprite;
    const ts = state.map.tileSize;
    /** @type {{ id: string, kind: string, sprite: import('pixi.js').Sprite }[]} */
    this.switches = state.switches
      .filter((s) => s.kind === 'plate' || s.kind === 'sensor')
      .map((s) => {
        const sprite = makeSprite(`sw.${s.kind}.off`);
        const z = state.map.elev[s.ty * state.map.width + s.tx];
        sprite.position.set(s.tx * ts + ts / 2, s.ty * ts + ts - 2 - z);
        // Plates lie flat on the floor (drawn before anyone standing on them).
        sprite.zIndex = s.kind === 'plate' ? s.ty * ts + 0.004 : s.ty * ts + ts - 2;
        actors.addChild(sprite);
        return { id: s.id, kind: s.kind, sprite };
      });
    this.vineLayer = new Container();
    ground.addChild(this.vineLayer);
    /** @type {import('pixi.js').Sprite[]} */
    this.vines = [];
    this.orb = makeSprite('fx.light');
    this.orb.visible = false;
    actors.addChild(this.orb);
    this.ring = new Graphics();
    overlay.addChild(this.ring);
    this.ringDrawn = false;
  }

  /** @param {import('../game/state.js').GameState} state @param {number} timeSec */
  update(state, timeSec) {
    for (const s of this.switches) s.sprite.texture = this.texture(`sw.${s.kind}.${state.switchActive[s.id] ? 'on' : 'off'}`);
    // Vines.
    const ts = state.map.tileSize;
    let n = 0;
    for (const [i, v] of state.env.vines) {
      let sp = this.vines[n];
      if (!sp) {
        sp = this.makeSprite('tile.vine');
        this.vineLayer.addChild(sp);
        this.vines.push(sp);
      }
      n++;
      sp.visible = true;
      sp.position.set((i % state.map.width) * ts, Math.floor(i / state.map.width) * ts - state.map.elev[i]);
      // Withering: blink in the last 5 seconds.
      sp.alpha = v.untilMs - state.env.now < 5000 && Math.floor(timeSec * 6) % 2 ? 0.5 : 1;
    }
    for (let k = n; k < this.vines.length; k++) this.vines[k].visible = false;
    // Light orb.
    const o = state.orb;
    this.orb.visible = !!o;
    if (o) {
      this.orb.position.set(Math.round(o.x), Math.round(o.y - o.z + Math.sin(timeSec * 3) * 1.5));
      this.orb.zIndex = o.y + 0.5;
    }
    // Resonance ring (cleared only when there is one, or once after: an emptied Graphics each frame
    // made PixiJS rebuild the world's whole draw list every frame).
    const pl = state.pulse;
    if (pl || this.ringDrawn) this.ring.clear();
    this.ringDrawn = !!pl;
    if (pl) {
      const k = Math.min(1, (state.env.now - pl.startMs) / ABILITY.pulseMs);
      this.ring.circle(pl.x, pl.y, k * ABILITY.pulseRadiusTiles * ts).stroke({ width: 2, color: 0x7fe8ff, alpha: 1 - k });
    }
  }
}
