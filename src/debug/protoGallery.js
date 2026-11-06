// @ts-check
// P12: the prototype gallery (?gallery=1) — every prototype NPC by name, walking in the four
// directions as the game plays it (frames 1, 0, 2, 0 at 8 per second), enlarged. A panel over the
// game for checking the art; it changes nothing in the game and is only built when asked for.

import { prototypeFrames } from '../view/assets/heroPrototype.js';

/** Who each villager look is (P12 plan: docs/characters/P12_NPC_ENEMY_PLAN.md). */
export const NPC_NAMES = /** @type {Record<number, string>} */ ({
  1: '老人（長老）',
  3: '兵士（見張り）',
  4: '商人',
  5: '子ども',
  6: '村人',
  7: '鍛冶屋',
  8: '旅人',
  9: '星環の姫',
});
const DIRS = /** @type {const} */ (['down', 'up', 'right', 'left']);
const DIR_JA = { down: '下', up: '上', right: '右', left: '左' };
const CYCLE = [1, 0, 2, 0];
const SCALE = 3;

/** @param {HTMLElement} root */
export async function openProtoGallery(root) {
  const frames = await prototypeFrames(['npc']);
  /** @type {Map<number, Map<string, HTMLImageElement>>} */
  const looks = new Map();
  await Promise.all(
    [...frames].map(async ([key, url]) => {
      const m = /^npc\.(\d+)\.walk\.(\w+)\.(\d)$/.exec(key);
      if (!m) return;
      const img = new Image();
      img.src = url;
      await img.decode();
      const look = Number(m[1]);
      if (!looks.has(look)) looks.set(look, new Map());
      /** @type {Map<string, HTMLImageElement>} */ (looks.get(look)).set(`${m[2]}.${m[3]}`, img);
    }),
  );
  const panel = document.createElement('div');
  panel.id = 'proto-gallery';
  panel.style.cssText =
    'position:fixed;inset:0;z-index:50;overflow:auto;background:rgba(20,22,30,.94);color:#eee;font:14px sans-serif;padding:12px;touch-action:pan-y';
  const title = document.createElement('div');
  title.textContent = 'P12 仮素材ギャラリー（NPC・歩行アニメーション）— 正式素材ではありません';
  title.style.cssText = 'font-weight:bold;margin-bottom:8px';
  const close = document.createElement('button');
  close.textContent = '閉じる';
  close.style.cssText = 'position:fixed;right:12px;top:8px;font-size:16px;padding:6px 14px';
  close.addEventListener('click', () => panel.remove());
  panel.append(title, close);
  /** @type {{ ctx: CanvasRenderingContext2D, imgs: Map<string, HTMLImageElement>, dir: string }[]} */
  const cells = [];
  for (const look of [...looks.keys()].sort((a, b) => a - b)) {
    const row = document.createElement('div');
    row.className = 'proto-gallery-row';
    row.dataset.look = String(look);
    row.style.cssText = 'display:flex;align-items:flex-end;gap:10px;margin:6px 0';
    const name = document.createElement('div');
    name.textContent = NPC_NAMES[look] ?? `look ${look}`;
    name.style.cssText = 'width:120px';
    row.append(name);
    for (const dir of DIRS) {
      const box = document.createElement('div');
      box.style.cssText = 'text-align:center';
      const cv = document.createElement('canvas');
      cv.width = 32 * SCALE;
      cv.height = 56 * SCALE;
      cv.style.cssText = 'background:#4f8a3e;image-rendering:pixelated';
      const ctx = /** @type {CanvasRenderingContext2D} */ (cv.getContext('2d'));
      ctx.imageSmoothingEnabled = false;
      const label = document.createElement('div');
      label.textContent = DIR_JA[dir];
      box.append(cv, label);
      row.append(box);
      cells.push({ ctx, imgs: /** @type {Map<string, HTMLImageElement>} */ (looks.get(look)), dir });
    }
    panel.append(row);
  }
  root.append(panel);
  let step = 0;
  const draw = () => {
    const f = CYCLE[step % CYCLE.length];
    for (const { ctx, imgs, dir } of cells) {
      ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
      const img = imgs.get(`${dir}.${f}`);
      if (img) ctx.drawImage(img, 0, 0, 32 * SCALE, 56 * SCALE);
    }
    panel.dataset.frame = String(f);
  };
  draw();
  const timer = setInterval(() => {
    if (!panel.isConnected) return clearInterval(timer);
    step++;
    draw();
  }, 125);
  return { looks: [...looks.keys()].sort((a, b) => a - b) };
}
