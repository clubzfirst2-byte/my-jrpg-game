// @ts-check
// Long-play measurement (P8, DESIGN.md roadmap: "60 分の長時間プレイ測定"). The 自動巡回 mode moves
// the player around the world on its own (a stop every few seconds through every region, so
// chunks and region art keep loading and unloading) and records numbers every 30 seconds. The
// report says whether memory kept growing — the P8 completion check — with the samples to paste.

/**
 * @typedef {{ tSec: number, fps: number, p95Ms: number, textures: number, displayObjects: number, chunks: number, bundles: number, heapMb: number | null }} TourSample
 */

export const TOUR = Object.freeze({
  /** Seconds at each stop. */
  stopSec: 4,
  sampleSec: 30,
});

/** Stops: the island, the plains, the desert, then (P10.3) the lake, the forest, the mountains and back (tile coordinates). */
export const TOUR_STOPS = [
  [48, 60], [30, 40], [16, 34], [60, 30], [80, 44], [47, 70],
  [50, 90], [30, 105], [70, 100], [48, 140], [48, 172],
  [30, 200], [70, 190], [36, 236], [60, 250],
  [128 + 12, 239], [128 + 34, 232], [128 + 66, 248], [128 + 47, 200],
  [128 + 30, 148], [128 + 74, 140], [128 + 47, 104],
  [128 + 47, 70], [128 + 50, 34], [128 + 30, 50],
  [93, 125], [48, 120], [47, 70],
];

/**
 * Judges a run: memory "keeps growing" when the last quarter of the samples is clearly above the
 * first quarter (textures by more than 4, display objects by more than 25%, heap by more than 30%).
 * @param {TourSample[]} samples
 */
export function judgeTour(samples) {
  if (samples.length < 4) return { growing: false, reason: 'サンプルが少ない（4 回以上必要）' };
  const q = Math.max(1, Math.floor(samples.length / 4));
  const first = samples.slice(0, q);
  const last = samples.slice(-q);
  const max = (/** @type {TourSample[]} */ s, /** @type {(x: TourSample) => number | null} */ f) => Math.max(...s.map((x) => f(x) ?? 0));
  const reasons = [];
  if (max(last, (s) => s.textures) > max(first, (s) => s.textures) + 4) reasons.push('テクスチャ数が増え続けている');
  if (max(last, (s) => s.displayObjects) > max(first, (s) => s.displayObjects) * 1.25) reasons.push('表示物の数が増え続けている');
  const heapFirst = max(first, (s) => s.heapMb);
  if (heapFirst > 0 && max(last, (s) => s.heapMb) > heapFirst * 1.3) reasons.push('JS のメモリが増え続けている');
  return { growing: reasons.length > 0, reason: reasons.join('、') || '増え続けていない' };
}

/**
 * The report (Markdown) to paste into docs/device-tests.
 * @param {TourSample[]} samples @param {{ minutes: number, version: string, device: Record<string, string | number> }} info
 */
export function tourReport(samples, info) {
  const j = judgeTour(samples);
  const lines = [
    `## 自動巡回 ${info.minutes} 分（${info.version}）`,
    '',
    `**判定**：${j.growing ? '⚠ ' : '✓ '}${j.reason}`,
    '',
    ...Object.entries(info.device).map(([k, v]) => `- ${k}: ${v}`),
    '',
    '| 経過 | FPS | 遅い5% ms | テクスチャ | 表示物 | チャンク | 素材の束 | JS メモリ MB |',
    '|---|---|---|---|---|---|---|---|',
    ...samples.map((s) => `| ${Math.round(s.tSec / 60)}分${Math.round(s.tSec % 60)}秒 | ${s.fps.toFixed(1)} | ${s.p95Ms.toFixed(1)} | ${s.textures} | ${s.displayObjects} | ${s.chunks} | ${s.bundles} | ${s.heapMb === null ? '—' : s.heapMb.toFixed(1)} |`),
  ];
  return lines.join('\n');
}
