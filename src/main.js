// @ts-check
// Boot: wires platform (input, lifecycle, settings), logic (fixed-step game state),
// view (PixiJS) and the measurement overlay. main.js only connects layers.
import './styles.css';
import { UPDATE_PRIORITY } from 'pixi.js';
import { ErrorLog, installGlobalHandlers } from './debug/errorLog.js';
import { FrameStats } from './debug/frameStats.js';
import { installDrawCounter } from './debug/drawCounter.js';
import { collectDeviceInfo } from './debug/deviceInfo.js';
import { buildReport } from './debug/report.js';
import { createOverlay } from './debug/overlay.js';
import { createRenderer, resizeRenderer } from './view/renderer.js';
import { RESOLUTION_CANDIDATES, DEFAULT_TARGET_HEIGHT, nextCandidate } from './view/resolution.js';
import { AssetManager } from './view/assets/assetManager.js';
import { buildPlaceholderPack } from './view/assets/placeholderPack.js';
import { GameView } from './view/gameView.js';
import { Bench } from './view/bench.js';
import { InputManager } from './platform/inputManager.js';
import { installLifecycle } from './platform/lifecycle.js';
import { loadSettings, saveSettings } from './platform/settings.js';
import { PauseOverlay } from './ui/pauseOverlay.js';
import { HeartsHud } from './ui/hud.js';
import { RotateHint } from './ui/rotateHint.js';
import { TitleScreen } from './ui/title.js';
import { Toast } from './ui/toast.js';
import { SaveStore } from './save/saveStore.js';
import { Autosave } from './save/autosave.js';
import { failureMessage } from './save/saveFormat.js';
import { FixedStepLoop } from './game/core/fixedStep.js';
import { createGameState, stepGame, spawnEnemies, respawnPlayer, MAPS } from './game/state.js';
import { applyProgress, areaAt } from './game/world/features.js';
import { envSummary, ignite, material, weatherNow, setWorldTime } from './game/env/envSim.js';
import { clockText, CLOCK } from './game/env/weather.js';
import { groundHeightUnder } from './game/physics/collision.js';
import { GAME_TITLE, PHASE } from './game/version.js';

const errorLog = new ErrorLog();
installGlobalHandlers(errorLog, window);

const params = new URLSearchParams(window.location.search);
/** @param {string} key @param {number} fallback */
const intParam = (key, fallback) => {
  const v = Number.parseInt(params.get(key) ?? '', 10);
  return Number.isFinite(v) && v >= 0 ? v : fallback;
};

/** @param {string} message */
function showFatal(message) {
  const box = document.getElementById('fatal');
  if (!box) return;
  box.hidden = false;
  box.textContent = message;
}

/** @param {import('pixi.js').Container} node */
function countDisplayObjects(node) {
  let n = 1;
  for (const child of node.children) n += countDisplayObjects(child);
  return n;
}

async function boot() {
  const host = /** @type {HTMLElement} */ (document.getElementById('app'));
  const uiRoot = /** @type {HTMLElement} */ (document.getElementById('ui'));
  document.title = GAME_TITLE;
  const label = document.getElementById('phase-label');
  if (label) label.textContent = `${GAME_TITLE} ${PHASE} v${__APP_VERSION__} (${__COMMIT__})`;

  const settings = loadSettings();
  const resParam = intParam('res', 0);
  let targetHeight = /** @type {readonly number[]} */ (RESOLUTION_CANDIDATES).includes(resParam)
    ? resParam
    : /** @type {readonly number[]} */ (RESOLUTION_CANDIDATES).includes(settings.resolution)
      ? settings.resolution
      : DEFAULT_TARGET_HEIGHT;

  /** @type {import('pixi.js').Application} */
  let app;
  try {
    app = await createRenderer(host, targetHeight);
  } catch (err) {
    errorLog.add('error', err, performance.now());
    showFatal(
      'WebGL を初期化できませんでした。Safari を最新版に更新するか、ほかのアプリを閉じて再読み込みしてください。\n\n' +
        String(err instanceof Error ? err.message : err),
    );
    return;
  }
  const fpsCap = intParam('fps', 0);
  if (fpsCap > 0) app.ticker.maxFPS = fpsCap; // e.g. ?fps=30 to verify 30fps behaviour

  // --- assets / logic / view ---
  const assets = new AssetManager();
  assets.register('placeholder', buildPlaceholderPack);
  await assets.load('placeholder');
  // Without ?map= the game starts at the title on the first island and saves its progress.
  // ?map=... (tests, height/field test maps) skips the title and never touches the save.
  const mapParam = params.get('map');
  const withTitle = mapParam === null;
  const mapName = /** @type {keyof typeof MAPS} */ (mapParam ?? 'island');
  const state = createGameState(MAPS[mapName] ?? MAPS.island);
  const view = new GameView(app, assets, state);
  // Test / check helpers: ?time=20 (hour) and ?weather=rain|storm|cloudy|clear.
  const timeParam = Number.parseFloat(params.get('time') ?? '');
  if (Number.isFinite(timeParam)) setWorldTime(state.env, timeParam * CLOCK.hourMs);
  const weatherParam = params.get('weather');
  if (weatherParam && ['clear', 'cloudy', 'rain', 'storm'].includes(weatherParam)) state.env.weatherOverride = /** @type {any} */ (weatherParam);
  if (params.get('light') === '0') view.weather.enabled = false;
  const zoomParam = Number.parseFloat(params.get('zoom') ?? '');
  if (Number.isFinite(zoomParam)) view.camera.setZoom(zoomParam); // e.g. ?zoom=2 (zoom is adjustable later)
  const loop = new FixedStepLoop();
  const input = new InputManager(uiRoot);
  const hud = new HeartsHud(uiRoot);
  const rotateHint = new RotateHint(uiRoot);
  const deathOverlay = document.createElement('div');
  deathOverlay.id = 'death-overlay';
  deathOverlay.textContent = '力尽きた…';
  deathOverlay.hidden = true;
  uiRoot.append(deathOverlay);
  const toast = new Toast(uiRoot);
  const treasureHud = document.createElement('div');
  treasureHud.id = 'hud-treasure';
  treasureHud.hidden = true;
  uiRoot.append(treasureHud);
  let shownTreasures = -1;
  const clockHud = document.createElement('div');
  clockHud.id = 'hud-clock';
  uiRoot.append(clockHud);
  let shownClock = '';
  const WEATHER_NAMES = { clear: '晴れ', cloudy: 'くもり', rain: '雨', storm: '雷雨' };

  // --- save (DESIGN.md 2.6) ---
  const store = new SaveStore(__APP_VERSION__);
  const autosave = new Autosave(
    store,
    () => ({ ...state.progress, worldMs: Math.round(state.env.now) }),
    (msg) => toast.show(msg, { kind: 'error', ms: 6000 }),
  );
  /** @type {any} */
  let loaded = { status: 'empty' };
  let inTitle = withTitle;
  /** @type {TitleScreen | null} */
  let title = null;
  if (withTitle) {
    loaded = await store.load();
    const notes = {
      empty: '',
      ok: loaded.recovered ? '最新の保存データが壊れていたため、ひとつ前の保存から再開します。' : '',
      corrupt: '保存データが壊れていて読み込めませんでした。はじめから遊べます。',
      newer: 'この保存データは新しいバージョンで作られています。ページを再読み込みしてください（データは消しません）。',
      error: loaded.status === 'error' ? failureMessage(loaded.reason) : '',
    };
    title = new TitleScreen(uiRoot, {
      title: GAME_TITLE,
      hasSave: loaded.status === 'ok',
      saveNote: notes[/** @type {keyof typeof notes} */ (loaded.status)] ?? '',
      onNew: () => startGame(false),
      onContinue: () => startGame(true),
    });
  }
  /** @param {boolean} fromSave */
  function startGame(fromSave) {
    if (fromSave && loaded.status === 'ok') {
      applyProgress(state, loaded.data);
      respawnPlayer(state);
      if (loaded.recovered) toast.show('ひとつ前の保存から再開しました。', { ms: 4000 });
    }
    // Never overwrite a save written by a newer version of the game.
    autosave.enabled = loaded.status !== 'newer';
    void store.requestPersistence();
    inTitle = false;
    input.clear();
    loop.reset();
    view.snapCamera(state);
  }
  // Save when the app goes to the background (iOS may close it without further notice).
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') void autosave.saveNow();
  });
  window.addEventListener('pagehide', () => void autosave.saveNow());

  // Messages for things that happened in the game.
  let lastEventTick = state.tick;
  function announceEvents() {
    for (const e of state.events) {
      if (e.tick <= lastEventTick) continue;
      const ev = /** @type {any} */ (e);
      if (ev.type === 'chest') {
        toast.show(ev.reward === 'heart' ? 'ハートの器を手に入れた！ 体力が増えた' : `宝物を手に入れた！（${state.progress.treasures}）`);
      } else if (ev.type === 'checkpoint') {
        toast.show('記録石に触れた — 倒れてもここから再開できる');
      } else if (ev.type === 'gateOpen') {
        toast.show('どこかで扉が開いた音がする…');
      } else if (ev.type === 'landmark') {
        const l = state.landmarks.find((x) => x.id === ev.id);
        if (l && !l.always) toast.show(`発見：${l.name}`);
      }
    }
    lastEventTick = state.tick;
  }

  const bench = new Bench(app);
  bench.setCount(intParam('bench', 0));

  // --- pause / resume ---
  let paused = false;
  const pauseOverlay = new PauseOverlay(uiRoot, {
    onPauseRequest: () => pause(''),
    onResume: () => resume(),
  });
  /** @param {string} message */
  function pause(message) {
    paused = true;
    input.clear();
    pauseOverlay.show(message);
  }
  function resume() {
    paused = false;
    loop.reset(); // never "catch up" on time spent paused
    stats.reset();
    skipNextFrame = true;
    pauseOverlay.hide();
  }

  let resolution = resizeRenderer(app, targetHeight);
  installLifecycle(app.canvas, {
    onPause: () => {
      if (!paused) pause('');
      void autosave.saveNow();
    },
    onContextLost: () => pause('描画が一時的に中断されました。戻らない場合は再読み込みしてください。'),
    onContextRestored: () => pauseOverlay.show('描画が復帰しました。'),
    onViewportChange: () => {
      resolution = resizeRenderer(app, targetHeight);
    },
  });

  // --- measurement ---
  const renderer = /** @type {any} */ (app.renderer);
  const gl = renderer.gl ?? null;
  const drawCounter = installDrawCounter(gl);
  const stats = new FrameStats(240);
  const reportSec = intParam('reportSec', 30) || 30;
  let frameStart = performance.now();
  let lastCpu = 0;
  let lastDraws = 0;
  const originalRender = renderer.render.bind(renderer);
  renderer.render = (/** @type {any[]} */ ...args) => {
    const result = originalRender(...args);
    lastCpu = performance.now() - frameStart;
    return result;
  };

  /** @type {null | { endAt: number, intervals: number[], cpu: number[], draws: number[], errorsAtStart: number }} */
  let recording = null;
  let lastReport = '';
  const textureCount = () => renderer.texture?.managedTextures?.length ?? 0;
  let skipNextFrame = true;

  const overlay = createOverlay(
    uiRoot,
    errorLog,
    {
      onScaleSprites(factor) {
        const next = factor === 0 ? 0 : bench.count === 0 ? 100 : bench.count * factor;
        bench.setCount(next);
      },
      onStartReport() {
        if (recording) return;
        stats.reset();
        recording = { endAt: performance.now() + reportSec * 1000, intervals: [], cpu: [], draws: [], errorsAtStart: errorLog.total };
      },
      onCycleResolution() {
        targetHeight = nextCandidate(targetHeight);
        settings.resolution = targetHeight;
        saveSettings(settings);
        resolution = resizeRenderer(app, targetHeight);
        stats.reset();
        return targetHeight;
      },
    },
    { open: params.get('debug') === '1', reportSec, resolution: targetHeight },
  );

  function finishRecording() {
    if (!recording) return;
    const r = recording;
    recording = null;
    overlay.setRecording(null);
    lastReport = buildReport({
      version: __APP_VERSION__,
      commit: __COMMIT__,
      dateIso: new Date().toISOString(),
      durationSec: reportSec,
      intervals: r.intervals,
      cpu: r.cpu,
      drawCalls: r.draws,
      sprites: bench.count,
      textures: textureCount(),
      errors: errorLog.total - r.errorsAtStart,
      device: {
        内部解像度: `${resolution.width}×${resolution.height}（目標 ${targetHeight}、×${resolution.scale}）`,
        ...collectDeviceInfo(gl, app.renderer.name),
      },
    });
    overlay.showReport(lastReport);
  }

  let objectCount = 0;
  let lastObjectCount = 0;
  let lastOverlay = 0;

  // HIGH priority: runs first each frame and records the previous frame's numbers.
  app.ticker.add(
    (ticker) => {
      const now = performance.now();
      lastDraws = drawCounter.take();
      if (skipNextFrame || paused) {
        skipNextFrame = false;
      } else {
        stats.push(ticker.elapsedMS, lastCpu);
        if (recording) {
          recording.intervals.push(ticker.elapsedMS);
          recording.cpu.push(lastCpu);
          recording.draws.push(lastDraws);
          if (now >= recording.endAt) finishRecording();
          else overlay.setRecording(Math.ceil((recording.endAt - now) / 1000));
        }
      }
      frameStart = now;

      if (now - lastObjectCount > 500) {
        objectCount = countDisplayObjects(app.stage);
        lastObjectCount = now;
      }
      if (now - lastOverlay > 250) {
        lastOverlay = now;
        const s = stats.summary();
        const p = state.player;
        overlay.setStats(
          [
            `FPS ${s.fps.toFixed(1)}   30fps未満 ${s.over33Pct.toFixed(1)}%`,
            `フレーム 平均${s.avgMs.toFixed(1)} / 遅い5% ${s.p95Ms.toFixed(1)} / 最大${s.maxMs.toFixed(1)} ms`,
            `JS ${s.avgCpuMs.toFixed(2)}ms   描画 ${lastDraws}回${drawCounter.supported ? '' : '(未対応)'}`,
            `表示物 ${objectCount}   テクスチャ ${textureCount()}   負荷 ${bench.count}`,
            `内部 ${resolution.width}×${resolution.height} ×${resolution.scale}  DPR ${window.devicePixelRatio}`,
            `位置 ${p.x.toFixed(0)},${p.y.toFixed(0)} 高さ ${p.z.toFixed(0)}（地面 ${p.groundZ.toFixed(0)}）${p.grounded ? '' : ' 空中'}`,
            `体力 ${p.hp}/${p.maxHp}  スタミナ ${p.stamina.toFixed(0)}${p.exhausted ? '（疲労）' : ''}${p.climbing ? ' 登攀中' : ''}${p.gliding ? ' 滑空中' : ''}${p.swimming ? ' 水泳中' : ''}`,
            `${p.facing}${p.dashing ? ' ダッシュ' : ''}  エラー ${errorLog.total}`,
            (() => {
              const e = envSummary(state.env);
              return `環境 燃焼${e.burning} 計算${e.lastTickCells}/最大${e.maxTickCells} 灰${e.ash} 凍結${state.env.rw * state.env.rh - e.awakeRegions}${e.jobs ? ` 早送り中${e.jobs}` : ''}\nライト ${view.weather.lightOn ? `${view.weather.lightMs.toFixed(2)}ms` : 'なし'}  ${shownClock}`;
            })(),
          ].join('\n'),
        );
      }
    },
    undefined,
    UPDATE_PRIORITY.HIGH,
  );

  // NORMAL priority: fixed-step logic, then draw the interpolated state.
  let alpha = 0;
  app.ticker.add((ticker) => {
    if (!paused && !inTitle) {
      const frameInput = input.sample();
      // Real elapsed time (PixiJS caps ticker.deltaMS at 100ms); the loop applies its own clamp
      // and accounts for any time it drops (DESIGN.md 1.3).
      alpha = loop.advance(ticker.elapsedMS, () => stepGame(state, frameInput)).alpha;
    }
    if (!paused && !inTitle) {
      announceEvents();
      autosave.update(state, ticker.elapsedMS);
    }
    view.render(state, alpha, performance.now() / 1000, ticker.elapsedMS / 1000);
    hud.update(state.player.hp, state.player.maxHp);
    const clock = `${clockText(state.env.now)} ${WEATHER_NAMES[weatherNow(state.env).kind]}`;
    if (clock !== shownClock) {
      shownClock = clock;
      clockHud.textContent = clock;
    }
    if (state.progress.treasures !== shownTreasures) {
      shownTreasures = state.progress.treasures;
      treasureHud.hidden = shownTreasures === 0;
      treasureHud.textContent = `宝物 ${shownTreasures}`;
    }
    deathOverlay.hidden = state.deathMs < 0;
    bench.update(ticker.elapsedMS / 1000);
  });

  // Read-only hook for automated E2E tests.
  /** @type {any} */ (window).__debugApi = {
    summary: () => stats.summary(),
    sprites: () => bench.count,
    setSprites: (/** @type {number} */ n) => bench.setCount(n),
    drawCalls: () => lastDraws,
    errors: () => errorLog.total,
    rendererName: () => app.renderer.name,
    lastReport: () => lastReport,
    player: () => {
      const p = state.player;
      return {
        x: p.x,
        y: p.y,
        z: p.z,
        groundZ: p.groundZ,
        grounded: p.grounded,
        hp: p.hp,
        facing: p.facing,
        dashing: p.dashing,
        climbing: p.climbing,
        gliding: p.gliding,
        swimming: p.swimming,
        dead: !!p.dead,
        action: p.action,
        guarding: !!p.guarding,
        invulnMs: p.invulnMs,
        stamina: p.stamina,
        exhausted: p.exhausted,
      };
    },
    occluded: () => view.playerOccluded,
    /** Test helper: place the player on tile (tx, ty), standing on the terrain. */
    teleport: (/** @type {number} */ tx, /** @type {number} */ ty) => {
      const p = state.player;
      const ts = state.map.tileSize;
      p.x = p.prevX = tx * ts + ts / 2;
      p.y = p.prevY = ty * ts + ts - 2;
      p.z = p.prevZ = p.groundZ = groundHeightUnder(p, state.map);
      p.vx = p.vy = p.vz = 0;
      p.grounded = true;
      p.climbing = false;
      view.snapCamera(state);
    },
    camera: () => {
      const c = view.camera;
      return { x: c.x, y: c.y, zoom: c.zoom, origin: c.origin(), viewWidth: c.viewWidth, viewHeight: c.viewHeight, bounds: c.bounds };
    },
    setZoom: (/** @type {number} */ z) => view.camera.setZoom(z),
    /** Test helper: remove all enemies (for tests that are not about combat). */
    clearEnemies: () => {
      state.enemySpawns = [];
      state.enemies = [];
      state.projectiles = [];
    },
    enemies: () => state.enemies.map((e) => ({ id: e.id, kind: e.kind, x: e.x, y: e.y, z: e.z, hp: e.hp, state: e.state })),
    projectiles: () => state.projectiles.map((pr) => ({ kind: pr.kind, owner: pr.owner, x: pr.x, y: pr.y })),
    flurry: () => state.flurryMs,
    /** Test helper: place an enemy next to the player. */
    spawnEnemy: (/** @type {'beast' | 'archer'} */ kind, /** @type {number} */ tx, /** @type {number} */ ty) => {
      state.enemySpawns.push({ kind, tx, ty });
      spawnEnemies(state);
    },
    /** Test helper: set health (quarter hearts). */
    setHp: (/** @type {number} */ v) => {
      state.player.hp = v;
    },
    deathMs: () => state.deathMs,
    /** Recent game events (last 64): lets tests observe short actions without racing them. */
    events: () => state.events.map((e) => e.type),
    /** Test helper: set stamina (e.g. to check drowning without waiting). */
    setStamina: (/** @type {number} */ v) => {
      state.player.stamina = v;
    },
    rotateHintVisible: () => rotateHint.visible,
    titleVisible: () => !!title && title.visible,
    progress: () => JSON.parse(JSON.stringify(state.progress)),
    area: () => areaAt(state, state.player.x, state.player.y)?.id ?? null,
    /** Test helper: save immediately; resolves to whether it worked. */
    saveNow: () => autosave.saveNow(),
    saveInfo: () => ({ enabled: autosave.enabled, saves: autosave.saves, failures: autosave.failures, loaded: loaded.status }),
    toasts: () => [...toast.history],
    markers: () => view.features.visibleMarkers(),
    /** P4 environment: summary, and test helpers to set a tile alight / read a tile. */
    env: () => envSummary(state.env),
    envIgnite: (/** @type {number} */ tx, /** @type {number} */ ty) => ignite(state.env, state.map, ty * state.map.width + tx),
    envTile: (/** @type {number} */ tx, /** @type {number} */ ty) => {
      const i = ty * state.map.width + tx;
      return { material: material(state.env, state.map, i), burning: state.env.burning.has(i), solid: state.map.solid[i] === 1 };
    },
    /** P5: time of day and weather. */
    weather: () => ({ ...weatherNow(state.env), clock: clockText(state.env.now), lightOn: view.weather.lightOn, lightMs: view.weather.lightMs, rainVisible: view.weather.rain.visible }),
    setHour: (/** @type {number} */ h) => setWorldTime(state.env, Math.floor(state.env.now / CLOCK.dayMs) * CLOCK.dayMs + h * CLOCK.hourMs),
    setWeather: (/** @type {any} */ kind) => {
      state.env.weatherOverride = kind;
    },
    /** Test helper: a lightning strike on tile (tx, ty) after the usual warning. */
    forceStrike: (/** @type {number} */ tx, /** @type {number} */ ty) => {
      state.env.strike = { i: ty * state.map.width + tx, atMs: state.env.now + 900 };
    },
    strikePending: () => !!state.env.strike,
    envEvents: () => state.events.filter((e) => ['ignite', 'fireArrow', 'discharge', 'douse', 'gateOpen', 'burn', 'cut'].includes(e.type)).map((e) => e.type),
    /** Test helper: point the player in a direction without moving (for opening chests). */
    face: (/** @type {'up' | 'down' | 'left' | 'right'} */ dir) => {
      const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[dir];
      state.player.facing = dir;
      state.player.aimX = v[0];
      state.player.aimY = v[1];
    },
    tick: () => state.tick,
    loop: () => ({ totalSteps: loop.totalSteps, droppedMs: loop.droppedMs, elapsedMs: loop.elapsedMs, pendingMs: loop.accumulator }),
    paused: () => paused,
    /** Test helpers: freeze / unfreeze the game deterministically (same as the pause button). */
    pause: () => pause(''),
    resume: () => resume(),
    /** Test helper: while paused, advance exactly `n` logic steps with the current input. */
    step: (/** @type {number} */ n = 1) => {
      for (let i = 0; i < n; i++) stepGame(state, input.sample());
    },
    resolution: () => ({ ...resolution, target: targetHeight }),
    assets: () => assets.stats(),
  };
  document.body.dataset.ready = 'true';
}

boot().catch((err) => {
  errorLog.add('error', err, performance.now());
  showFatal(`起動に失敗しました: ${String(err instanceof Error ? err.message : err)}`);
});
