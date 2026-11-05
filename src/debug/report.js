// @ts-check
// Builds a Markdown measurement report that can be pasted into docs/device-tests/.
import { summarize } from './frameStats.js';

/**
 * @typedef {object} ReportInput
 * @property {string} version
 * @property {string} commit
 * @property {string} dateIso
 * @property {number} durationSec
 * @property {number[]} intervals   frame intervals (ms)
 * @property {number[]} cpu         JS time per frame (ms)
 * @property {number[]} drawCalls   draw calls per frame
 * @property {number} sprites       benchmark sprite count during the run
 * @property {number} textures
 * @property {number} errors        errors raised during the run
 * @property {Record<string, string|number>} device
 * @property {{ pageMs: number | null, scriptsMs: number | null, readyMs: number, transferKb: number | null, fromCache: boolean | null }} [load]  P11.1
 */

/** @param {number} v */
const f1 = (v) => v.toFixed(1);

/**
 * @param {ReportInput} r
 * @returns {string}
 */
export function buildReport(r) {
  const s = summarize(r.intervals, r.cpu);
  const avgDraw = r.drawCalls.length ? r.drawCalls.reduce((a, b) => a + b, 0) / r.drawCalls.length : 0;
  const verdict = s.fps >= 55 ? '◎ 60fps 目標を達成' : s.fps >= 29.5 ? '○ 30fps 以上（最低ライン達成）' : '× 30fps 未満';
  const deviceRows = Object.entries(r.device)
    .map(([k, v]) => `| ${k} | ${String(v).replace(/\|/g, '/')} |`)
    .join('\n');
  return `### 計測レポート（${r.dateIso}）

| 項目 | 値 |
|---|---|
| ゲームの版 | ${r.version} (${r.commit}) |
| 計測時間 | ${r.durationSec} 秒（${s.frames} フレーム） |
| 負荷テストのスプライト数 | ${r.sprites} |
| 平均 FPS | ${f1(s.fps)} |
| フレーム時間 平均 / 遅い5% / 最大 | ${f1(s.avgMs)} / ${f1(s.p95Ms)} / ${f1(s.maxMs)} ms |
| 30fps を下回ったフレーム | ${f1(s.over33Pct)} % |
| JS 処理時間（平均） | ${f1(s.avgCpuMs)} ms |
| 描画呼び出し数（平均） | ${f1(avgDraw)} |
| テクスチャ数 | ${r.textures} |
| 計測中のエラー | ${r.errors} 件 |${r.load ? `\n| 起動にかかった時間 | ${r.load.readyMs} ms（ページ ${r.load.pageMs ?? '—'} / スクリプト ${r.load.scriptsMs ?? '—'} ms、通信 ${r.load.fromCache ? '0 KB（保存済み）' : `${r.load.transferKb ?? '—'} KB`}） |` : ''}
| 判定 | ${verdict} |

| 端末情報 | 値 |
|---|---|
${deviceRows}
`;
}
