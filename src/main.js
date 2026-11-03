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
import { FixedStepLoop } from './game/core/fixedStep.js';
import { createGameState, stepGame, MAPS } from './game/state.js';
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
  const mapName = /** @type {keyof typeof MAPS} */ (params.get('map') ?? 'height');
  const state = createGameState(MAPS[mapName] ?? MAPS.height);
  const view = new GameView(app, assets, state);
  const zoomParam = Number.parseFloat(params.get('zoom') ?? '');
  if (Number.isFinite(zoomParam)) view.camera.setZoom(zoomParam); // e.g. ?zoom=2 (zoom is adjustable later)
  const loop = new FixedStepLoop();
  const input = new InputManager(uiRoot);
  const hud = new HeartsHud(uiRoot);
  const rotateHint = new RotateHint(uiRoot);
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
        stats.push(ticker.deltaMS, lastCpu);
        if (recording) {
          recording.intervals.push(ticker.deltaMS);
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
            `体力 ${p.hp}/${p.maxHp}  スタミナ ${p.stamina.toFixed(0)}${p.exhausted ? '（疲労）' : ''}${p.climbing ? ' 登攀中' : ''}`,
            `${p.facing}${p.dashing ? ' ダッシュ' : ''}  エラー ${errorLog.total}`,
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
    if (!paused) {
      const frameInput = input.sample();
      alpha = loop.advance(ticker.deltaMS, () => stepGame(state, frameInput)).alpha;
    }
    view.render(state, alpha, performance.now() / 1000, ticker.deltaMS / 1000);
    hud.update(state.player.hp, state.player.maxHp);
    bench.update(ticker.deltaMS / 1000);
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
    rotateHintVisible: () => rotateHint.visible,
    tick: () => state.tick,
    loop: () => ({ totalSteps: loop.totalSteps, droppedMs: loop.droppedMs, elapsedMs: loop.elapsedMs, pendingMs: loop.accumulator }),
    paused: () => paused,
    resolution: () => ({ ...resolution, target: targetHeight }),
    assets: () => assets.stats(),
  };
  document.body.dataset.ready = 'true';
}

boot().catch((err) => {
  errorLog.add('error', err, performance.now());
  showFatal(`起動に失敗しました: ${String(err instanceof Error ? err.message : err)}`);
});
