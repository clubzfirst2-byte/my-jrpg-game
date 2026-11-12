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
/**
 * Graphics v3: the light map's pixels per screen pixel in the v3 view (4 canvas px per game px): 0.25,
 * one map pixel per game pixel as the v3=0 view has with 0.5 (about 2 canvas px per game px), so the
 * lights look as soft as before and the map has the same pixels to fill.
 */
export const LIGHT_MAP_RESOLUTION_V3 = 0.25;

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
export function createLightMap(resolution = LIGHT_MAP_RESOLUTION) {
  const rt = RenderTexture.create({ width: 8, height: 8, dynamic: true, resolution, scaleMode: 'linear' });
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
   * @param {{ lightResolution?: number }} [opts] the light map's pixels per screen pixel (graphics v3: LIGHT_MAP_RESOLUTION_V3)
   */
  constructor(app, makeSprite, actors, { lightResolution = LIGHT_MAP_RESOLUTION } = {}) {
    this.app = app;
    /** The light map's pixels per screen pixel (LIGHT_MAP_RESOLUTION; graphics v3: LIGHT_MAP_RESOLUTION_V3). */
    this.lightResolution = lightResolution;
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
    const map = createLightMap(lightResolution);
    this.rt = map.rt;
    this.overlay = map.overlay;
    // Rain (screen space).
    this.rain = new Container();
    this.rain.label = 'rain';
    /** @type {{ s: Sprite, x: number, y: number }[]} */
    this.drops = [];
    // Snow (P10.2): slow flakes that sway and drift with the wind.
    this.snow = new Container();
    this.snow.label = 'snow';
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
    const amb = area?.dark ? AMB_DARK_ROOM : area?.home ? AMB_HOME : indoor ? this.indoorAmbient : ambientAt(env.now, w.kind);
    const white = amb.r >= 0.999 && amb.g >= 0.999 && amb.b >= 0.999;
    this.lightOn = this.enabled && !white;
    this.overlay.visible = this.lightOn;
    if (this.lightOn) {
      if (this.rtW !== sw || this.rtH !== sh) {
        this.rtW = sw;
        this.rtH = sh;
        this.rt.resize(sw, sh, this.lightResolution);
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
    if (raining) this.updateRain(w, sw, sh, dtSec, w.kind === 'storm' ? 1 : 0.6);
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
    // v1.0: enemies winding up light their own spot, so the red warning reads in the dark.
    for (const l of warningLights(state.enemies ?? [])) add(l.x, l.y, l.r, WARNING_LIGHT.color);
    return n;
  }

  /** @param {import('../game/env/weather.js').Weather} w @param {number} sw @param {number} sh @param {number} dt @param {number} density */
  updateRain(w, sw, sh, dt, density) {
    const want = Math.round(((sw * sh) / 900) * density);
    while (this.drops.length < want) {
      const s = this.makeSprite('px');
      s.width = 1;
      s.height = 5;
      s.tint = 0xb8d0ff;
      s.alpha = 0.55;
      this.rain.addChild(s);
      this.drops.push({ s, x: Math.random() * sw, y: Math.random() * sh });
    }
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
      d.x += vx * dt;
      d.y += vy * dt;
      if (d.y > sh) {
        d.y -= sh + 8;
        d.x = Math.random() * sw;
      }
      if (d.x < 0) d.x += sw;
      if (d.x > sw) d.x -= sw;
      s.position.set(Math.round(d.x), Math.round(d.y));
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
