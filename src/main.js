// @ts-check
// Boot: wires the error log, the renderer, the P0 benchmark scene and the measurement overlay.
// No gameplay yet (P0 = environment + measurement foundation, DESIGN.md section 8).
import './styles.css';
import { UPDATE_PRIORITY } from 'pixi.js';
import { ErrorLog, installGlobalHandlers } from './debug/errorLog.js';
import { FrameStats } from './debug/frameStats.js';
import { installDrawCounter } from './debug/drawCounter.js';
import { collectDeviceInfo } from './debug/deviceInfo.js';
import { buildReport } from './debug/report.js';
import { createOverlay } from './debug/overlay.js';
import { createRenderer, addTestFloor } from './view/renderer.js';
import { Bench } from './view/bench.js';
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
  document.title = GAME_TITLE;
  const label = document.getElementById('phase-label');
  if (label) label.textContent = `${GAME_TITLE} ${PHASE} 計測シーン v${__APP_VERSION__} (${__COMMIT__})`;

  /** @type {import('pixi.js').Application} */
  let app;
  try {
    app = await createRenderer(host);
  } catch (err) {
    errorLog.add('error', err, performance.now());
    showFatal(
      'WebGL を初期化できませんでした。Safari を最新版に更新するか、ほかのアプリを閉じて再読み込みしてください。\n\n' +
        String(err instanceof Error ? err.message : err),
    );
    return;
  }

  addTestFloor(app);
  const bench = new Bench(app);
  bench.setCount(intParam('bench', 0));

  const renderer = /** @type {any} */ (app.renderer);
  const gl = renderer.gl ?? null;
  const drawCounter = installDrawCounter(gl);
  const stats = new FrameStats(240);
  const reportSec = intParam('reportSec', 30) || 30;

  // Measure JS time per frame: from the start of the ticker frame to the end of render submission.
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
  let skipNextFrame = true; // first frame and the first frame after returning from background are not representative

  const overlay = createOverlay(
    /** @type {HTMLElement} */ (document.getElementById('ui')),
    errorLog,
    {
      onScaleSprites(factor) {
        const next = factor === 0 ? 0 : bench.count === 0 ? 100 : bench.count * factor;
        bench.setCount(next);
      },
      onStartReport() {
        if (recording) return;
        stats.reset();
        recording = {
          endAt: performance.now() + reportSec * 1000,
          intervals: [],
          cpu: [],
          draws: [],
          errorsAtStart: errorLog.total,
        };
      },
    },
    { open: params.get('debug') === '1', reportSec },
  );

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      stats.reset();
      skipNextFrame = true;
    }
  });

  function finishRecording() {
    if (!recording) return;
    const r = recording;
    recording = null;
    overlay.setRecording(null);
    const markdown = buildReport({
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
      device: collectDeviceInfo(gl, app.renderer.name),
    });
    overlay.showReport(markdown);
    lastReport = markdown;
  }

  let objectCount = 0;
  let lastObjectCount = 0;
  let lastOverlay = 0;

  // HIGH priority: runs first each frame and records the previous frame's numbers.
  app.ticker.add(
    (ticker) => {
      const now = performance.now();
      lastDraws = drawCounter.take();
      if (skipNextFrame) {
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
        overlay.setStats(
          [
            `FPS ${s.fps.toFixed(1)}   30fps未満 ${s.over33Pct.toFixed(1)}%`,
            `フレーム 平均${s.avgMs.toFixed(1)} / 遅い5% ${s.p95Ms.toFixed(1)} / 最大${s.maxMs.toFixed(1)} ms`,
            `JS ${s.avgCpuMs.toFixed(2)}ms   描画 ${lastDraws}回${drawCounter.supported ? '' : '(未対応)'}`,
            `表示物 ${objectCount}   テクスチャ ${textureCount()}   負荷 ${bench.count}`,
            `画面 ${app.screen.width}×${app.screen.height}  DPR ${window.devicePixelRatio}  ${app.renderer.name}`,
            `エラー ${errorLog.total}`,
          ].join('\n'),
        );
      }
    },
    undefined,
    UPDATE_PRIORITY.HIGH,
  );

  // NORMAL priority: scene update (benchmark only in P0).
  app.ticker.add((ticker) => bench.update(ticker.deltaMS / 1000));

  // Small hook for automated E2E tests (read-only view of measurement state).
  /** @type {any} */ (window).__debugApi = {
    summary: () => stats.summary(),
    sprites: () => bench.count,
    setSprites: (/** @type {number} */ n) => bench.setCount(n),
    drawCalls: () => lastDraws,
    errors: () => errorLog.total,
    rendererName: () => app.renderer.name,
    lastReport: () => lastReport,
  };
  document.body.dataset.ready = 'true';
}

boot().catch((err) => {
  errorLog.add('error', err, performance.now());
  showFatal(`起動に失敗しました: ${String(err instanceof Error ? err.message : err)}`);
});
