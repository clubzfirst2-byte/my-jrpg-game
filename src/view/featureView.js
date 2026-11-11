// @ts-check
// Draws the island features (P3.5): chests, checkpoint stones, campfires with smoke, cave openings,
// and edge markers pointing at discovered landmarks that are off-screen. Reads state only.
import { Graphics } from 'pixi.js';
import { objectShadow } from './shadows.js';
/** @typedef {import('pixi.js').Sprite} Sprite @typedef {import('pixi.js').Container} Container */
/** @typedef {(g: import('./shadows.js').ShadowGeom, x: number, y: number) => Sprite} ShadowMaker */

const SMOKE_PUFFS = 7;
const SMOKE_RISE_PX = 40;
const SMOKE_PERIOD_SEC = 3.5;
const MARKER_MARGIN = 10;
const FIRE_FPS = 6;

/**
 * gfx W5: a shadow under a feature (chest, record stone), sorted just under it.
 * @param {ShadowMaker | undefined} make @param {Container} actors @param {string} type @param {Sprite} s @param {number} zIndex
 */
function castShadow(make, actors, type, s, zIndex) {
  const g = make ? objectShadow(type, s.width, s.height) : null;
  if (!make || !g) return;
  const sh = make(g, s.x, s.y);
  sh.zIndex = zIndex;
  actors.addChild(sh);
}

export class FeatureView {
  /**
   * @param {(key: string) => Sprite} makeSprite
   * @param {Container} actors   Y-sorted layer
   * @param {Container} screen   screen-space layer (markers)
   * @param {import('../game/state.js').GameState} state
   * @param {ShadowMaker} [makeShadow] gfx W5: makes a cast shadow (shadows.js; none with ?fx=v1)
   */
  constructor(makeSprite, actors, screen, state, makeShadow) {
    this.makeSprite = makeSprite;
    const map = state.map;
    const ts = map.tileSize;
    /** @param {number} tx @param {number} ty */
    const feet = (tx, ty) => ({ x: tx * ts + ts / 2, y: ty * ts + ts, z: map.elev[ty * map.width + tx] });

    /** @type {{ id: string, sprite: Sprite }[]} */
    this.chests = state.chests.map((c) => {
      const f = feet(c.tx, c.ty);
      const s = makeSprite('obj.chest.closed');
      s.position.set(f.x, f.y - f.z - 1);
      s.zIndex = f.y - 1;
      actors.addChild(s);
      castShadow(makeShadow, actors, 'chest', s, f.y - 1.01);
      return { id: c.id, sprite: s };
    });

    /** @type {{ id: string, sprite: Sprite }[]} */
    this.checkpoints = state.checkpointDefs.map((c) => {
      const f = feet(c.tx, c.ty);
      const s = makeSprite('obj.checkpoint.off');
      s.position.set(f.x, f.y - f.z - 3);
      s.zIndex = f.y - 3;
      actors.addChild(s);
      castShadow(makeShadow, actors, 'checkpoint', s, f.y - 3.01);
      return { id: c.id, sprite: s };
    });

    /** @type {{ sprite: Sprite, puffs: Sprite[], x: number, y: number }[]} */
    this.fires = state.campfires.map((c, i) => {
      const f = feet(c.tx, c.ty);
      const s = makeSprite('obj.campfire.0');
      s.position.set(f.x, f.y - f.z - 1);
      s.zIndex = f.y - 1;
      actors.addChild(s);
      // Smoke rises high so it can be seen from afar (a landmark, DESIGN.md 5.9).
      const puffs = [];
      for (let k = 0; k < SMOKE_PUFFS; k++) {
        const p = makeSprite('fx.smoke');
        p.zIndex = 1e6 + i; // always above the terrain
        actors.addChild(p);
        puffs.push(p);
      }
      return { sprite: s, puffs, x: f.x, y: f.y - f.z - 12 };
    });

    // Cave mouths: on the cliff north of every doorway entered by walking north.
    for (const w of state.warps) {
      if (w.facing !== 'up' || w.ty === 0) continue;
      const here = map.elev[w.ty * map.width + w.tx];
      const north = map.elev[(w.ty - 1) * map.width + w.tx];
      if (north <= here) continue;
      const s = makeSprite('obj.cave');
      s.position.set(w.tx * ts + ts / 2, w.ty * ts - here);
      s.zIndex = w.ty * ts - 0.5; // over the cliff row, under anyone standing in the doorway
      actors.addChild(s);
    }

    // Daylight on the floor where a doorway leads back outside (walking south).
    for (const w of state.warps) {
      if (w.facing !== 'down') continue;
      const s = makeSprite('px');
      s.tint = 0xfff2c0;
      s.alpha = 0.35;
      s.width = ts;
      s.height = ts;
      s.position.set(w.tx * ts, w.ty * ts - map.elev[w.ty * map.width + w.tx]);
      s.zIndex = w.ty * ts - 1;
      actors.addChild(s);
    }

    // Inside an area (cave) everything outside it is dark.
    this.mask = new Graphics();
    screen.addChild(this.mask);
    this.maskDrawn = false;

    /** @type {{ id: string, x: number, y: number, sprite: Sprite }[]} */
    this.markers = state.landmarks.map((l) => {
      const s = makeSprite('ui.marker');
      s.visible = false;
      screen.addChild(s);
      const f = feet(l.tx, l.ty);
      return { id: l.id, x: f.x, y: f.y - f.z, sprite: s };
    });
  }

  /**
   * @param {import('../game/state.js').GameState} state
   * @param {(key: string) => import('pixi.js').Texture} texture
   * @param {{ x: number, y: number }} origin camera top-left (world px)
   * @param {number} zoom
   * @param {number} screenW @param {number} screenH
   * @param {number} timeSec
   * @param {{ x: number, y: number, width: number, height: number } | null} area world rect, inside an area
   */
  update(state, texture, origin, zoom, screenW, screenH, timeSec, area) {
    // (cleared only inside an area, or once on leaving it: an emptied Graphics each frame made
    // PixiJS rebuild the whole scene's draw list every frame)
    if (area || this.maskDrawn) this.mask.clear();
    this.maskDrawn = !!area;
    if (area) {
      const x0 = Math.round((area.x - origin.x) * zoom);
      const y0 = Math.round((area.y - origin.y) * zoom);
      const x1 = Math.round((area.x + area.width - origin.x) * zoom);
      const y1 = Math.round((area.y + area.height - origin.y) * zoom);
      if (y0 > 0) this.mask.rect(0, 0, screenW, y0);
      if (y1 < screenH) this.mask.rect(0, y1, screenW, screenH - y1);
      if (x0 > 0) this.mask.rect(0, Math.max(0, y0), x0, Math.min(screenH, y1) - Math.max(0, y0));
      if (x1 < screenW) this.mask.rect(x1, Math.max(0, y0), screenW - x1, Math.min(screenH, y1) - Math.max(0, y0));
      this.mask.fill({ color: 0x07060a });
    }
    const pr = state.progress;
    for (const c of this.chests) c.sprite.texture = texture(pr.openedChests.includes(c.id) ? 'obj.chest.open' : 'obj.chest.closed');
    for (const c of this.checkpoints) {
      c.sprite.texture = texture(pr.checkpoints.includes(c.id) ? 'obj.checkpoint.on' : 'obj.checkpoint.off');
      // The active stone pulses gently.
      c.sprite.alpha = pr.checkpoint === c.id ? 0.85 + 0.15 * Math.sin(timeSec * 3) : 1;
    }
    for (const f of this.fires) {
      f.sprite.texture = texture(`obj.campfire.${Math.floor(timeSec * FIRE_FPS) % 2}`);
      f.puffs.forEach((p, k) => {
        const t = ((timeSec / SMOKE_PERIOD_SEC + k / f.puffs.length) % 1 + 1) % 1;
        p.position.set(Math.round(f.x + Math.sin(t * 5 + k) * 3 + t * 6), Math.round(f.y - t * SMOKE_RISE_PX * 2.5));
        p.scale.set(1 + t * 1.5);
        p.alpha = 0.7 * (1 - t);
      });
    }

    // Edge markers for discovered landmarks outside the view.
    const viewW = screenW / zoom;
    const viewH = screenH / zoom;
    const cx = origin.x + viewW / 2;
    const cy = origin.y + viewH / 2;
    for (const m of this.markers) {
      const known = pr.landmarks.includes(m.id);
      const inside = m.x >= origin.x && m.x <= origin.x + viewW && m.y >= origin.y - 24 && m.y <= origin.y + viewH;
      m.sprite.visible = known && !inside && !area; // no outdoor landmarks from inside a cave
      if (!m.sprite.visible) continue;
      const dx = m.x - cx;
      const dy = m.y - cy;
      // Clamp the direction to the screen rectangle (minus a margin).
      const hw = screenW / 2 - MARKER_MARGIN;
      const hh = screenH / 2 - MARKER_MARGIN;
      const k = Math.min(hw / Math.max(1e-6, Math.abs(dx * zoom)), hh / Math.max(1e-6, Math.abs(dy * zoom)));
      m.sprite.position.set(Math.round(screenW / 2 + dx * zoom * k), Math.round(screenH / 2 + dy * zoom * k));
      m.sprite.rotation = Math.atan2(dy, dx);
      m.sprite.scale.set(2);
    }
  }

  /** Discovered landmarks whose marker is currently shown (for tests). */
  visibleMarkers() {
    return this.markers.filter((m) => m.sprite.visible).map((m) => m.id);
  }
}
