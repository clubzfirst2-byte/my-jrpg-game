// @ts-check
// Time of day and weather on screen (P5): the ambient light (a light map multiplied over the world,
// with fires, campfires and crystals glowing at night), rain streaks blown by the wind, and
// lightning (a warning flicker on the target, then a bolt and a flash). Reads state only.
//
// Cost: by day in clear weather the light map is skipped entirely. Otherwise it is one small
// render-to-texture at half the internal resolution (LIGHT_MAP_RESOLUTION; the map is only soft
// gradients and flat tint, upscaled with linear filtering), and it is redrawn only when a light, the
// ambient colour or the screen size changed (lightMs is measured for the debug overlay).
// v1.0 (iPhone perf): night rain in software rendering ran at about half the day's frame rate. Per
// frame the view no longer rebuilds the flash Graphics, re-renders an unchanged light map, allocates
// for the lightning lookup, or sets every raindrop's rotation; see `stats` for the counts.
import { Container, Graphics, RenderTexture, Sprite, Texture } from 'pixi.js';
import { ambientAt, isDark, isRaining } from '../game/env/weather.js';
import { playerWeather } from '../game/env/weatherActions.js';
import { ENEMY_KINDS } from '../game/entities/enemies.js';
import { BOSS_KINDS } from '../game/entities/bosses.js';
import { FINAL_BOSS } from '../game/entities/finalBoss.js';
import { openingView } from '../game/story/story.js';
import { WINDOW_GLOW } from './houseWindows.js';
import { atlasFrame, whiteRGBA } from './pixelAtlas.js';

/**
 * gfx W5 rain: two layers of streaks (far: short, faint, slower; near: long, brighter, faster), small
 * splashes on the ground, and a darker, cooler sky while it rains outdoors. Pooled; the splashes
 * are a fixed set of sprites reused in turn.
 */
export const RAIN = Object.freeze({
  /** every `nearEvery`-th drop is a near one */
  nearEvery: 3,
  near: { h: 8, alpha: 0.6, speed: 1.3, tint: 0xc8dcff },
  far: { h: 4, alpha: 0.45, speed: 0.75, tint: 0x9fb8e0 },
  /** the one layer before W5 (?fx=v1) */
  v1: { h: 5, alpha: 0.55, speed: 1, tint: 0xb8d0ff },
  splashes: 40,
  /** splashes a second per 100×100 screen px at full density */
  splashRate: 3.2,
  splashMs: 220,
  /**
   * a splash, in game px, on the game's pixel grid: a 2-px drop, then a crown — 4 px wide, its two
   * ends 1 px up (rows top to bottom; # a pixel)
   */
  splash: Object.freeze([Object.freeze({ rows: Object.freeze(['##']), alpha: 0.85 }), Object.freeze({ rows: Object.freeze(['#..#', '.##.']), alpha: 0.7 })]),
  /** the sky while it rains (multiplied into the ambient light) */
  sky: { r: 0.86, g: 0.9, b: 1 },
});

/** A splash frame's texture (white, one texel per game px, on the effects' atlas). @param {number} f */
export function splashTexture(f) {
  const rows = RAIN.splash[f].rows;
  const w = rows[0].length;
  const h = rows.length;
  return atlasFrame(`splash:${f}`, w, h, () => {
    const a = new Uint8ClampedArray(w * h);
    rows.forEach((row, y) => {
      for (let x = 0; x < w; x++) if (row[x] === '#') a[y * w + x] = 255;
    });
    return whiteRGBA(a, w * h);
  });
}

/** The look of the i-th rain drop. @param {number} i @param {boolean} fancy false: the one layer before W5 */
export const rainLayer = (i, fancy) => (!fancy ? RAIN.v1 : i % RAIN.nearEvery === 0 ? RAIN.near : RAIN.far);

/** Scales a 0xRRGGBB colour by k (0..1). @param {number} c @param {number} k */
const scaleColor = (c, k) => (Math.round(((c >> 16) & 255) * k) << 16) | (Math.round(((c >> 8) & 255) * k) << 8) | Math.round((c & 255) * k);

/**
 * A winding-up enemy's warning light (world px): the colour added to the light map.
 * `ringCover`: a ground light reaches the ring (plus `ringMargin`) at this fraction of its radius,
 * where its falloff still adds about 40% (at the very edge of a light it adds nothing).
 * `slamCover`: a slam's ring (the sentinel's, a core's) lies at this fraction of its light's radius,
 * where lightFalloff still adds 26%. (v1.0 inspection of the minor fixes: the slam light used to be
 * `slamRadius + ringMargin` around the body, which put the ring's far edge near the light's rim:
 * about 0.20 with the old cone and 0.13 with the smooth falloff.)
 */
export const WARNING_LIGHT = Object.freeze({ color: 0xffd0c0, enemyRadius: 26, bossRadius: 44, ringMargin: 10, ringCover: 0.62, slamCover: 0.7 });

/**
 * 淀みの源's ground reach for its slam / inversion wave (the ring sourceView.js draws), or 0.
 * @param {any} e
 */
export function sourceReach(e) {
  if (!e.final) return 0;
  return e.pattern === 'slam' ? FINAL_BOSS.slamRadius : e.pattern === 'wave' ? FINAL_BOSS.waveRadius : 0;
}

/**
 * v1.0 (final QA B-1): the wind-up warning is drawn in the world, sorted with its enemy, so a tree
 * in front hides it like it hides the enemy. To keep it readable at night and in dark rooms, every
 * enemy winding up lights its own spot in the light map (big enough for a slam's ring): the red
 * overlay and the ring then show at about daylight strength, and the glow itself says "about to
 * strike". (Drawing the warning above the light map instead kept it bright but floated it over
 * trees.)
 *
 * v1.0 final: 淀みの源 (`final`, no `bossKind`) used to get only its 44 px body light, so most of its
 * slam ring (44) and inversion wave (64) lay in the dark. Its slam and wave now add a light on the
 * ground centred on the ring, wide enough to light all of it, and kept on while the shockwave goes
 * out (`attack`), so the hit itself reads too.
 * @param {any[]} enemies @returns {{ x: number, y: number, r: number }[]}
 */
export function warningLights(enemies) {
  const out = [];
  for (const e of enemies) {
    const reach = sourceReach(e);
    if (reach > 0 && (e.state === 'windup' || e.state === 'attack')) {
      out.push({ x: e.x, y: e.y - e.z, r: Math.ceil((reach + WARNING_LIGHT.ringMargin) / WARNING_LIGHT.ringCover) });
    }
    if (e.state !== 'windup') continue;
    const slam = e.boss && e.bossKind ? (e.pattern === 'slam' ? BOSS_KINDS[e.bossKind]?.slamRadius : 0) : e.kind === 'sentinel' ? ENEMY_KINDS.sentinel.slamRadius : 0;
    const body = e.boss || e.final ? WARNING_LIGHT.bossRadius : WARNING_LIGHT.enemyRadius;
    // A slam: one light centred on its ring (drawn around the feet), the ring at slamCover of it.
    if (slam) out.push({ x: e.x, y: e.y - e.z, r: Math.max(body, Math.ceil(slam / WARNING_LIGHT.slamCover)) });
    else out.push({ x: e.x, y: e.y - e.z - (e.boss || e.final ? 16 : 6), r: body });
  }
  return out;
}

/** The light map's pixels per screen pixel (0.5: a quarter of the pixels to fill). */
export const LIGHT_MAP_RESOLUTION = 0.5;

const RAIN_SPEED = 320; // px/s on screen
const RAIN_WIND = 120;
const FLASH_MS = 260;

/**
 * A light's strength at `t` (0 at its centre, 1 at its edge): (1 - t²)², a smooth bell.
 *
 * v1.0 (final QA L-1, "the lights in rooms look like blotchy patches"): the disc used to be a
 * straight cone (stops 1, 0.55 at 45%, 0: that is 1 - t), with a sharp peak in the middle and a
 * hard crease where it stops at the edge. Over flat stone the eye reads such creases as edges (Mach
 * bands), and two or three overlapping lights in a room made a patchwork of them. This curve is
 * flat at the centre and meets 0 with a flat slope, and gives the same total light as the cone
 * (both 1/3 of a full disc), so nights and the dark trials keep their light.
 * @param {number} t
 */
export const lightFalloff = (t) => (t >= 1 ? 0 : (1 - t * t) ** 2);

/** A soft white disc (radial falloff, lightFalloff) for lights. */
function lightTexture() {
  const size = 128;
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const g = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
  const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  const steps = 24; // the canvas interpolates linearly between stops: 24 follow the curve within 1%
  for (let k = 0; k <= steps; k++) grad.addColorStop(k / steps, `rgba(255,255,255,${lightFalloff(k / steps).toFixed(4)})`);
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  return Texture.from(c);
}

const AMB_DARK_ROOM = Object.freeze({ r: 0.1, g: 0.1, b: 0.16 });
const AMB_HOME = Object.freeze({ r: 0.94, g: 0.86, b: 0.72 });
const AMB_INDOOR = Object.freeze({ r: 0.55, g: 0.55, b: 0.65 });

/** @typedef {{ radius: number, color: number }} FireLight */
/** A fire's light (campfire, brazier, lit sconce): radius (world px) and colour. @type {Readonly<FireLight>} */
export const FIRE_LIGHT = Object.freeze({ radius: 64, color: 0xffb070 });
/**
 * v1.0 (inspection of the minor fixes): a fire in a lit room (a cave, a mine, a trial that is not
 * dark) reaches a little further. Its warm pool reads against the brighter room light
 * (terrainArt.indoorLight) as it did before; near the fire the light map is at full strength
 * either way, so only the reach can add to it.
 */
/** @type {Readonly<FireLight>} */
export const FIRE_LIGHT_ROOM = Object.freeze({ radius: 72, color: 0xffb070 });

/** @param {number[]} a @param {number[]} b */
function sameNumbers(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

/** @param {{ r: number, g: number, b: number }} c */
const toHex = (c) => (Math.round(Math.min(1, c.r) * 255) << 16) | (Math.round(Math.min(1, c.g) * 255) << 8) | Math.round(Math.min(1, c.b) * 255);

/**
 * The light map: a render texture the size of the screen, drawn over the world with 'multiply'.
 *
 * v1.0 fix (final QA A-1, "nights are never dark when the game starts from the title"): the texture
 * starts tiny and is resized to the screen on the first update. A Sprite only follows its texture's
 * size changes when the texture is `dynamic`; otherwise it keeps the size it had when it was first
 * drawn. With the title, the app draws frames while boot waits for the save (store.load), before
 * the first update: the light map was drawn at 8×8 then and stayed an 8×8 dot in the corner for
 * good, so the world was never darkened. (Without the title, the first draw came after the resize,
 * so it happened to work.) Hence `dynamic: true`, and the map stays hidden until it is first filled.
 * v1.0 (iPhone perf): drawn at LIGHT_MAP_RESOLUTION and stretched back with linear filtering. With
 * an odd screen size the texture is up to one map pixel larger than the screen (it still starts at
 * the top left, so screen and map coordinates match).
 */
export function createLightMap() {
  const rt = RenderTexture.create({ width: 8, height: 8, dynamic: true, resolution: LIGHT_MAP_RESOLUTION, scaleMode: 'linear' });
  const overlay = new Sprite(rt);
  overlay.blendMode = 'multiply';
  overlay.label = 'light-map';
  overlay.visible = false;
  return { rt, overlay };
}

/**
 * v1.0 (C5, C9): whether the beach ring is open (lit): a gate to the source until the ending is seen,
 * and its one flash in the opening. Drawn as obj.star_ring.on (gameView) and lit at night (below).
 * @param {any} state
 */
export const starRingOpen = (state) => (!!state.progress?.flags.source_open && !state.progress.flags.ending_seen) || !!openingView(state)?.flash;

/**
 * The shock crystal's night light: the placeholder's cyan, or with the release art (a pale-yellow
 * crystal) the shock ramp's 3rd step #eeea88, the colour of its lit faces (v1.0).
 * @param {import('pixi.js').Texture} tex the crystal's texture in use
 */
export const crystalLightColor = (tex) => (tex.source.resolution >= 2 ? 0xeeea88 : 0x60d8ff);

/** The lit ring's light: the hero's gem blue, about the size of the ring's glow (v1.0). */
export const STAR_RING_LIGHT = Object.freeze({ radius: 40, color: 0x7fe8ff });

export class WeatherView {
  /**
   * @param {import('pixi.js').Application} app
   * @param {(key: string) => Sprite} makeSprite
   * @param {Container} actors world layer for the strike warning
   */
  constructor(app, makeSprite, actors) {
    this.app = app;
    this.renderer = app.renderer;
    this.makeSprite = makeSprite;
    /** The ambient light indoors (caves, mines, trial rooms); v1.0: set by the view (terrainArt.indoorLight). @type {{ r: number, g: number, b: number }} */
    this.indoorAmbient = AMB_INDOOR;
    /** The shock crystals' light colour (crystalLightColor; set by the game view from the art in use). */
    this.crystalLight = 0x60d8ff;
    /** Fires' light (campfire, brazier, lit sconce): FIRE_LIGHT, or FIRE_LIGHT_ROOM in a lit room. */
    /** @type {FireLight} */
    this.fire = { ...FIRE_LIGHT };
    /** @type {FireLight} */
    this.fireRoom = { ...FIRE_LIGHT_ROOM };
    // Light map.
    /** The soft disc for lights, made on first use. @type {Texture | null} */
    this.lightTex = null;
    this.lightScene = new Container();
    this.ambientFill = new Sprite(Texture.WHITE);
    this.lightScene.addChild(this.ambientFill);
    /** @type {Sprite[]} */
    this.lights = [];
    const map = createLightMap();
    this.rt = map.rt;
    this.overlay = map.overlay;
    // Rain (screen space).
    this.rain = new Container();
    this.rain.label = 'rain';
    this.rain.isRenderGroup = true; // (gfx W5: its drops and splashes come and go without rebuilding the world's list)
    /** @type {{ s: Sprite, x: number, y: number, k: number }[]} */
    this.drops = [];
    /** gfx W5: splashes on the ground (made on first rain). @type {{ s: Sprite, age: number }[]} */
    this.splashes = [];
    this.nextSplash = 0;
    this.splashAcc = 0;
    /** The ambient colour in use (reused: no allocation per frame). */
    this.ambRain = { r: 1, g: 1, b: 1 };
    /** gfx W5: lit windows (world px of each pane's centre) and how lit they are (0..1); set by the game view. */
    /** @type {{ x: number, y: number }[]} */
    this.windowLights = [];
    this.windowGlow = 0;
    /** gfx W5: the rain's splashes and darker sky (off only for measuring) */
    this.fancyRain = true;
    /** the style the drops have now (null: restyle) @type {boolean | null} */
    this.rainStyle = null;
    /** The ambient light in use last update. @type {{ r: number, g: number, b: number }} */
    this.ambient = { r: 1, g: 1, b: 1 };
    /** @type {string} */
    this.kind = 'clear';
    this.flashing = false;
    // Snow (P10.2): slow flakes that sway and drift with the wind.
    this.snow = new Container();
    this.snow.label = 'snow';
    this.snow.isRenderGroup = true; // (gfx W5: its drops and splashes come and go without rebuilding the world's list)
    /** @type {{ s: Sprite, x: number, y: number, phase: number, speed: number }[]} */
    this.flakes = [];
    // Lightning.
    this.bolt = new Graphics();
    this.flash = new Graphics();
    this.warn = makeSprite('px');
    this.warn.visible = false;
    this.warn.width = 16;
    this.warn.height = 16;
    actors.addChild(this.warn);
    this.flashUntil = 0;
    this.lastBoltTick = -1;
    /** Milliseconds spent on the light map last frame (debug overlay). */
    this.lightMs = 0;
    this.lightOn = false;
    this.enabled = true;
    /** The light map's requested size (the texture may round up by one map pixel). */
    this.rtW = 0;
    this.rtH = 0;
    /** What the light map was last drawn from (screen size, ambient, every light); reused buffers. */
    this.lightSig = /** @type {number[]} */ ([]);
    this.lastLightSig = /** @type {number[]} */ ([]);
    this.flashW = 0;
    this.flashH = 0;
    this.rainAngle = NaN;
    this.rainDrops = 0;
    /** Work counters (unit tests and profiling): light map renders and skips, flash rebuilds. */
    this.stats = { lightRenders: 0, lightSkips: 0, flashRebuilds: 0 };
    // The light map is redrawn only when its inputs change, but its pixels live on the GPU: when
    // iOS drops the WebGL context (the app in the background) and Pixi restores it, the texture
    // comes back empty while the hero may still be standing still. Redraw after a context restore,
    // when the page becomes visible again and after the renderer is resized.
    const r = /** @type {any} */ (this.renderer);
    r.runners?.contextChange?.add({ contextChange: () => this.invalidateLightMap() });
    r.on?.('resize', () => this.invalidateLightMap());
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') this.invalidateLightMap();
      });
    }
  }

  /** Forgets what the light map was drawn from, so the next update draws it again. */
  invalidateLightMap() {
    this.lastLightSig.length = 0;
  }

  /** Adds the screen-space layers in order: light map, rain, snow, bolt, flash. @param {Container} stage @param {number} index */
  attach(stage, index) {
    stage.addChildAt(this.overlay, index);
    stage.addChildAt(this.rain, index + 1);
    stage.addChildAt(this.snow, index + 2);
    stage.addChildAt(this.bolt, index + 3);
    stage.addChildAt(this.flash, index + 4);
  }

  /**
   * @param {import('../game/state.js').GameState} state
   * @param {{ x: number, y: number }} origin @param {number} zoom
   * @param {{ dark?: boolean, home?: boolean } | null} area the cave / trial / house the player is in (null outdoors)
   * @param {number} timeSec @param {number} dtSec
   */
  update(state, origin, zoom, area, timeSec, dtSec) {
    const indoor = !!area;
    const env = state.env;
    const w = playerWeather(state);
    /** The weather here (the game view's ambient particles read it). */
    this.kind = w.kind;
    const sw = this.app.screen.width;
    const sh = this.app.screen.height;
    const nowMs = timeSec * 1000;

    // --- lightning ---
    let bolt = null;
    for (let j = state.events.length - 1; j >= 0; j--) {
      if (state.events[j].type === 'lightning') {
        bolt = state.events[j];
        break;
      }
    }
    if (bolt && bolt.tick !== this.lastBoltTick) {
      this.lastBoltTick = bolt.tick;
      this.flashUntil = nowMs + FLASH_MS;
      this.drawBolt(/** @type {number} */ (bolt.x), /** @type {number} */ (bolt.y), origin, zoom);
    }
    const flashing = nowMs < this.flashUntil;
    /** gfx W5: a lightning flash is lighting the scene (the sun's shadows go out). */
    this.flashing = flashing && !indoor;
    const k = flashing ? (this.flashUntil - nowMs) / FLASH_MS : 0;
    this.bolt.alpha = k;
    // The flash is one white rect built once per screen size; only its alpha changes per frame.
    this.flash.visible = flashing && !indoor;
    if (this.flash.visible) {
      if (this.flashW !== sw || this.flashH !== sh) {
        this.flashW = sw;
        this.flashH = sh;
        this.flash.clear().rect(0, 0, sw, sh).fill({ color: 0xffffff, alpha: 1 });
        this.stats.flashRebuilds++;
      }
      this.flash.alpha = 0.45 * k;
    }
    const st = env.strike;
    this.warn.visible = !!st;
    if (st) {
      const ts = state.map.tileSize;
      const tx = st.i % state.map.width;
      const ty = (st.i / state.map.width) | 0;
      this.warn.position.set(tx * ts, ty * ts - state.map.elev[st.i]);
      this.warn.zIndex = ty * ts + 0.003;
      this.warn.tint = 0xfff6a0;
      this.warn.alpha = Math.floor(timeSec * 16) % 2 ? 0.6 : 0.15;
    }

    // --- light map ---
    const t0 = performance.now();
    // Indoors is dim; a dark trial room is nearly black until something gives light (P7).
    // P10.1: a lived-in room is warm and lamp-lit at any hour.
    let amb = area?.dark ? AMB_DARK_ROOM : area?.home ? AMB_HOME : indoor ? this.indoorAmbient : ambientAt(env.now, w.kind);
    if (!indoor && isRaining(w) && this.fancyRain) {
      // gfx W5: a darker, cooler sky in the rain
      const t = this.ambRain;
      t.r = amb.r * RAIN.sky.r;
      t.g = amb.g * RAIN.sky.g;
      t.b = amb.b * RAIN.sky.b;
      amb = t;
    }
    /** The ambient light in use (the game view lights the windows from it). */
    this.ambient = amb;
    const white = amb.r >= 0.999 && amb.g >= 0.999 && amb.b >= 0.999;
    this.lightOn = this.enabled && !white;
    this.overlay.visible = this.lightOn;
    if (this.lightOn) {
      if (this.rtW !== sw || this.rtH !== sh) {
        this.rtW = sw;
        this.rtH = sh;
        this.rt.resize(sw, sh, LIGHT_MAP_RESOLUTION);
      }
      const ambHex = toHex(amb);
      this.ambientFill.width = this.rt.width;
      this.ambientFill.height = this.rt.height;
      this.ambientFill.tint = ambHex;
      const sig = this.lightSig;
      sig.length = 0;
      sig.push(sw, sh, ambHex);
      let n = 0;
      // A lit room (caves, mines, trials that are not dark): its fires get FIRE_LIGHT_ROOM.
      const fire = amb === this.indoorAmbient ? this.fireRoom : this.fire;
      if (isDark(amb) || indoor) n = this.placeLights(state, origin, zoom, timeSec, sw, sh, sig, fire);
      for (let j = n; j < this.lights.length; j++) this.lights[j].visible = false;
      if (sameNumbers(sig, this.lastLightSig)) {
        this.stats.lightSkips++; // nothing moved, flickered or changed colour: the map is still right
      } else {
        this.renderer.render({ container: this.lightScene, target: this.rt, clear: true });
        this.stats.lightRenders++;
        this.lightSig = this.lastLightSig;
        this.lastLightSig = sig;
      }
    } else {
      this.lastLightSig.length = 0; // redraw when the map is next needed
    }
    this.lightMs = performance.now() - t0;

    // --- rain ---
    const raining = isRaining(w) && !indoor;
    this.rain.visible = raining;
    if (raining) this.updateRain(w, sw, sh, dtSec, w.kind === 'storm' ? 1 : 0.6, zoom);
    const snowing = w.kind === 'snow' && !indoor;
    this.snow.visible = snowing;
    if (snowing) this.updateSnow(w, sw, sh, dtSec, timeSec);
  }

  /** @param {import('../game/env/weather.js').Weather} w @param {number} sw @param {number} sh @param {number} dt @param {number} timeSec */
  updateSnow(w, sw, sh, dt, timeSec) {
    const want = Math.round((sw * sh) / 1400);
    while (this.flakes.length < want) {
      const s = this.makeSprite('px');
      const big = Math.random() < 0.3;
      s.width = s.height = big ? 2 : 1;
      s.tint = 0xffffff;
      s.alpha = big ? 0.9 : 0.7;
      this.snow.addChild(s);
      this.flakes.push({ s, x: Math.random() * sw, y: Math.random() * sh, phase: Math.random() * 6.28, speed: big ? 34 : 22 });
    }
    const flakes = this.flakes;
    for (let j = 0; j < flakes.length; j++) {
      const f = flakes[j];
      f.s.visible = j < want;
      if (j >= want) continue;
      f.x += (w.windX * 30 + Math.sin(timeSec * 1.7 + f.phase) * 10) * dt;
      f.y += f.speed * dt;
      if (f.y > sh) {
        f.y -= sh + 4;
        f.x = Math.random() * sw;
      }
      if (f.x < 0) f.x += sw;
      if (f.x > sw) f.x -= sw;
      f.s.position.set(Math.round(f.x), Math.round(f.y));
    }
  }

  /** @returns {number} lights used */
  placeLights(/** @type {any} */ state, /** @type {{ x: number, y: number }} */ o, /** @type {number} */ zoom, /** @type {number} */ timeSec, /** @type {number} */ sw, /** @type {number} */ sh, /** @type {number[]} */ sig = [], fire = this.fire) {
    const env = state.env;
    const map = state.map;
    const ts = map.tileSize;
    let n = 0;
    const add = (/** @type {number} */ wx, /** @type {number} */ wy, /** @type {number} */ radius, /** @type {number} */ color) => {
      const x = (wx - o.x) * zoom;
      const y = (wy - o.y) * zoom;
      const r = radius * zoom;
      if (x < -r || y < -r || x > sw + r || y > sh + r) return;
      let s = this.lights[n];
      if (!s) {
        s = new Sprite((this.lightTex ??= lightTexture()));
        s.anchor.set(0.5);
        s.blendMode = 'add';
        this.lightScene.addChild(s);
        this.lights.push(s);
      }
      n++;
      s.visible = true;
      s.position.set(x, y);
      s.width = s.height = r * 2;
      s.tint = color;
      sig.push(x, y, r, color);
    };
    const flicker = (/** @type {number} */ i) => 1 + 0.08 * Math.sin(timeSec * 9 + i);
    // The player's own small glow, so night is dark but playable.
    const p = state.player;
    add(p.x, p.y - p.z - 8, 44, 0x8a7a60);
    for (const i of env.burning) {
      add((i % map.width) * ts + ts / 2, ((i / map.width) | 0) * ts + ts / 2 - map.elev[i], 34 * flicker(i), 0xffb060);
    }
    for (const [i, ob] of env.objectAt) {
      if (ob.gone) continue;
      const x = (i % map.width) * ts + ts / 2;
      const y = ((i / map.width) | 0) * ts + ts / 2 - map.elev[i];
      if (ob.type === 'campfire' || ob.type === 'brazier' || (ob.type === 'sconce' && ob.lit)) add(x, y - 6, fire.radius * flicker(i), fire.color);
      else if (ob.type === 'stove') add(x, y - 4, 40 * flicker(i), 0xffa860);
      else if (ob.type === 'stone' && ob.glow) add(x, y - 8, 30, 0x7fe8ff);
      else if (ob.type === 'pillar' || ob.type === 'altar') add(x, y - 10, 30, 0x7fe8ff);
      else if (ob.type === 'crystal') add(x, y - 8, 26, this.crystalLight);
      else if (ob.type === 'receiver' && ob.on) add(x, y - 8, 22, 0x60d8ff);
      else if (ob.type === 'star_ring' && starRingOpen(state)) add(x, y - 12, STAR_RING_LIGHT.radius, STAR_RING_LIGHT.color);
    }
    if (state.orb) add(state.orb.x, state.orb.y - state.orb.z, 80, 0xfff0c8); // 灯火
    if (env.sparks) for (const i of env.sparks.cells) add((i % map.width) * ts + ts / 2, ((i / map.width) | 0) * ts + ts / 2, 20, 0xfff27a);
    // gfx W5: lit windows cast a small warm pool on the ground in front of them (not on the wall).
    if (this.windowGlow > 0.01) {
      const c = scaleColor(WINDOW_GLOW.light, this.windowGlow);
      for (const l of this.windowLights) add(l.x, l.y, WINDOW_GLOW.radius, c);
    }
    // v1.0: enemies winding up light their own spot, so the red warning reads in the dark.
    for (const l of warningLights(state.enemies ?? [])) add(l.x, l.y, l.r, WARNING_LIGHT.color);
    return n;
  }

  /** @param {import('../game/env/weather.js').Weather} w @param {number} sw @param {number} sh @param {number} dt @param {number} density @param {number} [zoom] screen px per game px */
  updateRain(w, sw, sh, dt, density, zoom = 1) {
    const want = Math.round(((sw * sh) / 900) * density);
    while (this.drops.length < want) {
      const s = this.makeSprite('px');
      s.width = 1;
      this.rain.addChild(s);
      this.drops.push({ s, x: Math.random() * sw, y: Math.random() * sh, k: 1 });
      this.rainStyle = null; // (style the new drops)
    }
    if (this.rainStyle !== this.fancyRain) {
      // gfx W5: two layers — far (short, faint, slow) and near (long, bright, fast); one layer before it
      this.rainStyle = this.fancyRain;
      for (let j = 0; j < this.drops.length; j++) {
        const d = this.drops[j];
        const L = rainLayer(j, this.fancyRain);
        d.s.height = L.h;
        d.s.tint = L.tint;
        d.s.alpha = L.alpha;
        d.k = L.speed;
      }
    }
    if (this.fancyRain) this.updateSplashes(sw, sh, dt, density, zoom);
    else for (const p of this.splashes) p.s.visible = false;
    const vx = w.windX * RAIN_WIND;
    const vy = RAIN_SPEED;
    const angle = Math.atan2(vx, vy);
    // All drops share the wind's angle: set it only when the wind changes (or new drops appear).
    const turn = angle !== this.rainAngle || this.drops.length !== this.rainDrops;
    this.rainAngle = angle;
    this.rainDrops = this.drops.length;
    const drops = this.drops;
    for (let j = 0; j < drops.length; j++) {
      const d = drops[j];
      const s = d.s;
      if (turn) s.rotation = -angle;
      if (j >= want) {
        s.visible = false;
        continue;
      }
      s.visible = true;
      d.x += vx * d.k * dt;
      d.y += vy * d.k * dt;
      if (d.y > sh) {
        d.y -= sh + 8;
        d.x = Math.random() * sw;
      }
      if (d.x < 0) d.x += sw;
      if (d.x > sw) d.x -= sw;
      s.position.set(Math.round(d.x), Math.round(d.y));
    }
  }

  /**
   * gfx W5: small splashes where the rain hits the ground (screen space, pooled, reused in turn).
   * @param {number} sw @param {number} sh @param {number} dt @param {number} density @param {number} zoom screen px per game px
   */
  updateSplashes(sw, sh, dt, density, zoom) {
    if (this.splashes.length === 0) {
      for (let i = 0; i < RAIN.splashes; i++) {
        const s = new Sprite(splashTexture(0));
        s.anchor.set(0.5, 1); // (bottom centre: the crown rises from where the drop hit)
        s.tint = 0xd8e8ff;
        s.visible = false;
        this.rain.addChild(s);
        this.splashes.push({ s, age: RAIN.splashMs });
      }
    }
    this.splashAcc += ((sw * sh) / 10000) * RAIN.splashRate * density * dt;
    while (this.splashAcc >= 1) {
      this.splashAcc -= 1;
      const p = this.splashes[this.nextSplash];
      this.nextSplash = (this.nextSplash + 1) % this.splashes.length;
      p.age = 0;
      // on the game's pixel grid (the splash is drawn in whole game px)
      p.s.position.set(Math.round((Math.random() * sw) / zoom) * zoom, Math.round((sh * (0.15 + Math.random() * 0.85)) / zoom) * zoom);
    }
    const ms = dt * 1000;
    for (let i = 0; i < this.splashes.length; i++) {
      const p = this.splashes[i];
      p.age += ms;
      const k = p.age / RAIN.splashMs;
      p.s.visible = k < 1;
      if (k >= 1) continue;
      // two frames: a drop hitting (2 game px), then a crown opening (4 game px, its ends up)
      const fi = k < 0.45 ? 0 : 1;
      const tex = splashTexture(fi);
      if (p.s.texture !== tex) p.s.texture = tex;
      p.s.scale.set(zoom);
      p.s.alpha = RAIN.splash[fi].alpha;
    }
  }

  /** A zigzag bolt from the top of the screen to the strike. */
  drawBolt(/** @type {number} */ wx, /** @type {number} */ wy, /** @type {{ x: number, y: number }} */ o, /** @type {number} */ zoom) {
    const x = (wx - o.x) * zoom;
    const y = (wy - o.y) * zoom;
    const g = this.bolt;
    g.clear();
    let px = x + (Math.random() - 0.5) * 30;
    let py = 0;
    g.moveTo(px, py);
    const segs = 7;
    for (let k = 1; k <= segs; k++) {
      py = (y * k) / segs;
      px = k === segs ? x : x + (Math.random() - 0.5) * 18;
      g.lineTo(px, py);
    }
    g.stroke({ width: 2, color: 0xfffbe0 });
  }
}
