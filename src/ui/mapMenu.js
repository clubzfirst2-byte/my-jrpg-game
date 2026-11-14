// @ts-check
// The map (volume phase 1; plan M1 / M2). DOM + a small canvas. Opened from the pause screen (or
// the M key), so the game is waiting while it shows.
//
//   left   a drawing of the world, one square per region in its column. A region is drawn (ground,
//          water, roads, heights) once its survey stone has been touched; before that it is a dim
//          square. On it: where the player is, the record stones touched, and — on drawn regions —
//          the landmarks found and the survey stone.
//   right  the record stones touched, by region. Tap one to choose it (it lights up on the drawing),
//          then 「ここへ移る」 to travel there. Two taps, so a slip of the thumb never moves you.
// Every button is a 44 px tap target (the rule of `#ui button`).
import { Ground } from '../game/world/tilemap.js';
import { mapModel, checkpointName, TRAVEL_BLOCKED_TEXT } from '../game/world/survey.js';

/** Tiles between two columns of regions on the drawing. */
const GAP = 6;
/** World columns are 128 tiles wide (world.js); a region's outdoors is its west 96. */
const COLUMN_W = 128;

/** Ground colours [r, g, b] of the drawing (flat; a little lighter with height). */
const COLORS = /** @type {Record<number, [number, number, number]>} */ ({
  [Ground.GRASS]: [86, 150, 78],
  [Ground.PATH]: [196, 160, 106],
  [Ground.WATER]: [58, 112, 190],
  [Ground.RUIN]: [150, 146, 136],
  [Ground.SAND]: [222, 200, 140],
  [Ground.METAL]: [140, 150, 170],
  [Ground.PIT]: [22, 20, 34],
  [Ground.VINE]: [70, 130, 70],
  [Ground.WOOD]: [150, 110, 70],
  [Ground.WALL]: [110, 100, 90],
  [Ground.DARK]: [12, 14, 20],
});
/** Grass by climate: snow in the cold, dry grass in the desert. */
const GRASS_BY_CLIMATE = /** @type {Record<string, [number, number, number]>} */ ({ cold: [226, 234, 242], dry: [200, 176, 110] });

export class MapMenu {
  /**
   * @param {HTMLElement} root
   * @param {{ getState: () => any, onTravel: (id: string) => boolean, onClose?: () => void }} hooks
   *   onTravel: moves the player (survey.js travelTo) and returns whether it did
   */
  constructor(root, hooks) {
    this.hooks = hooks;
    /** @type {string | null} the record stone chosen */
    this.selected = null;
    /** @type {Map<string, HTMLCanvasElement>} region id -> its drawing (made once) */
    this.tiles = new Map();

    this.el = document.createElement('div');
    this.el.id = 'map-menu';
    this.el.hidden = true;
    this.el.addEventListener('click', (e) => e.stopPropagation()); // (the pause screen under it resumes on a tap)
    const head = document.createElement('div');
    head.className = 'map-head';
    const title = document.createElement('div');
    title.className = 'map-title';
    title.textContent = '地図';
    this.note = document.createElement('div');
    this.note.className = 'map-note';
    const close = document.createElement('button');
    close.type = 'button';
    close.id = 'map-close';
    close.textContent = '閉じる';
    close.addEventListener('click', () => this.close());
    head.append(title, this.note, close);

    const body = document.createElement('div');
    body.className = 'map-body';
    this.canvas = document.createElement('canvas');
    this.canvas.id = 'map-canvas';
    const side = document.createElement('div');
    side.className = 'map-side';
    this.list = document.createElement('div');
    this.list.className = 'map-list';
    this.go = document.createElement('button');
    this.go.type = 'button';
    this.go.id = 'map-travel';
    this.go.textContent = 'ここへ移る';
    this.go.addEventListener('click', () => this.travel());
    side.append(this.list, this.go);
    body.append(this.canvas, side);
    this.el.append(head, body);
    root.append(this.el);
  }

  get isOpen() {
    return !this.el.hidden;
  }

  open() {
    this.selected = null;
    this.el.hidden = false;
    this.render();
  }

  close() {
    if (this.el.hidden) return;
    this.el.hidden = true;
    this.hooks.onClose?.();
  }

  travel() {
    if (!this.selected) return;
    if (this.hooks.onTravel(this.selected)) {
      this.el.hidden = true; // (the caller resumes the game: no onClose)
    } else {
      this.render();
    }
  }

  /** @param {any} region one region of the map model */
  drawingOf(region) {
    let c = this.tiles.get(region.id);
    if (c) return c;
    const state = this.hooks.getState();
    const map = state.map;
    c = document.createElement('canvas');
    c.width = region.tw;
    c.height = region.th;
    const ctx = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
    const img = ctx.createImageData(region.tw, region.th);
    const climate = state.regions.find((/** @type {any} */ r) => r.id === region.id)?.climate;
    const trees = new Set(map.objects.filter((/** @type {any} */ o) => o.type === 'tree').map((/** @type {any} */ o) => o.ty * map.width + o.tx));
    for (let y = 0; y < region.th; y++) {
      for (let x = 0; x < region.tw; x++) {
        const i = (region.ty + y) * map.width + region.tx + x;
        const g = map.ground[i];
        let [r, gg, b] = (g === Ground.GRASS && GRASS_BY_CLIMATE[climate]) || COLORS[g] || [0, 0, 0];
        if (trees.has(i)) [r, gg, b] = climate === 'cold' ? [150, 176, 170] : [48, 104, 60];
        const k = 1 + Math.min(0.3, map.elev[i] / 320); // higher ground a little lighter
        const o = (y * region.tw + x) * 4;
        img.data[o] = Math.min(255, r * k);
        img.data[o + 1] = Math.min(255, gg * k);
        img.data[o + 2] = Math.min(255, b * k);
        img.data[o + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    this.tiles.set(region.id, c);
    return c;
  }

  render() {
    const state = this.hooks.getState();
    const m = mapModel(state);
    // --- the drawing ---
    const cols = Math.max(...m.regions.map((/** @type {any} */ r) => Math.floor(r.tx / COLUMN_W))) + 1;
    const worldH = Math.max(...m.regions.map((/** @type {any} */ r) => r.ty + r.th));
    const S = 2; // canvas px per tile (markers stay readable when the canvas is shown small)
    const cv = this.canvas;
    cv.width = (cols * 96 + (cols - 1) * GAP) * S;
    cv.height = worldH * S;
    const ctx = /** @type {CanvasRenderingContext2D} */ (cv.getContext('2d'));
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = '#0a0e16';
    ctx.fillRect(0, 0, cv.width, cv.height);
    /** Tile -> canvas px. @param {number} tx @param {number} ty */
    const at = (tx, ty) => {
      const col = Math.floor(tx / COLUMN_W);
      return { x: (col * (96 + GAP) + Math.min(95, tx - col * COLUMN_W) + 0.5) * S, y: (ty + 0.5) * S };
    };
    /** @param {number} x @param {number} y @param {number} r @param {string} fill @param {string} [stroke] */
    const dot = (x, y, r, fill, stroke) => {
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = fill;
      ctx.fill();
      if (stroke) {
        ctx.lineWidth = 2;
        ctx.strokeStyle = stroke;
        ctx.stroke();
      }
    };
    ctx.font = `bold ${6 * S}px sans-serif`;
    ctx.textAlign = 'center';
    for (const r of m.regions) {
      const o = at(r.tx, r.ty);
      const x0 = o.x - 0.5 * S;
      const y0 = o.y - 0.5 * S;
      if (r.surveyed) {
        ctx.drawImage(this.drawingOf(r), x0, y0, r.tw * S, r.th * S);
      } else {
        ctx.fillStyle = '#1b2230';
        ctx.fillRect(x0, y0, r.tw * S, r.th * S);
        ctx.fillStyle = '#5a6a80';
        ctx.fillText(r.checkpoints.length || r.current ? r.name : '？？？', x0 + (r.tw * S) / 2, y0 + (r.th * S) / 2 - 3 * S);
        ctx.fillText('（測量石を探そう）', x0 + (r.tw * S) / 2, y0 + (r.th * S) / 2 + 6 * S);
      }
      ctx.strokeStyle = r.current ? '#ffe27a' : '#3c5571';
      ctx.lineWidth = r.current ? 2 : 1;
      ctx.strokeRect(x0 + 0.5, y0 + 0.5, r.tw * S - 1, r.th * S - 1);
      for (const l of r.landmarks) {
        const p = at(l.tx, l.ty);
        dot(p.x, p.y, 2.5, '#ffd75e', '#3a2a10');
      }
      for (const sv of r.surveys) {
        const p = at(sv.tx, sv.ty);
        dot(p.x, p.y, 2.5, '#7fe8ff', '#103a44');
      }
      for (const c of r.checkpoints) {
        if (!c.outdoors) continue;
        const p = at(c.tx, c.ty);
        dot(p.x, p.y, c.id === this.selected ? 6 : 4, c.id === this.selected ? '#ffffff' : '#c8d6ff', c.id === this.selected ? '#ff8a3c' : '#22304a');
      }
    }
    if (m.player) {
      const p = at(m.player.tx, m.player.ty);
      dot(p.x, p.y, 4, '#ff5d5d', '#ffffff');
    }
    // --- the list of record stones ---
    this.list.textContent = '';
    let any = false;
    for (const r of m.regions) {
      if (r.checkpoints.length === 0) continue;
      const h = document.createElement('div');
      h.className = 'map-region';
      h.textContent = r.name;
      this.list.append(h);
      for (const c of r.checkpoints) {
        any = true;
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'map-stone';
        b.dataset.id = c.id;
        b.textContent = `${checkpointName(c.id)}${c.active ? '（いまの復活地点）' : ''}`;
        b.classList.toggle('active', c.id === this.selected);
        b.addEventListener('click', () => {
          this.selected = c.id;
          this.render();
        });
        this.list.append(b);
      }
    }
    if (!any) {
      const e = document.createElement('div');
      e.className = 'map-empty';
      e.textContent = '記録石にまだ触れていない。触れた記録石へは、ここから移れる。';
      this.list.append(e);
    }
    const surveyed = m.regions.filter((/** @type {any} */ r) => r.surveyed).length;
    this.note.textContent = m.blocked ? TRAVEL_BLOCKED_TEXT[m.blocked] : `測量 ${surveyed}/${m.regions.length} ・ 記録石を選ぶと移れる`;
    this.go.disabled = !this.selected || !!m.blocked;
    this.go.textContent = this.selected ? `「${checkpointName(this.selected)}」へ移る` : 'ここへ移る';
  }
}
