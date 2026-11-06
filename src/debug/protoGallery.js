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
/** The prototype enemies: name and art size (P12 rounds 1 and 3). */
export const ENEMY_INFO = /** @type {Record<string, { name: string, size: string }>} */ ({
  beast: { name: '獣型（獣）', size: '44×32' },
  archer: { name: 'ゴブリン型（弓兵の役）', size: '32×44' },
  slime: { name: 'スライム', size: '32×24' },
  flyer: { name: '飛行型（灯尾蛾）', size: '36×28' },
  plant: { name: '植物型（牙つぼみ）', size: '32×40' },
  golem: { name: '大型（苔岩の巨人）', size: '64×72' },
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
  title.textContent = 'P12 仮素材ギャラリー（NPC の歩行・敵の 2 コマ）— 正式素材ではありません';
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
  // Enemies: both frames side by side (right and left as the game mirrors them), and the
  // two frames alternating as they do while moving.
  const enemyFrames = await prototypeFrames(['enemy']);
  /** @type {Map<string, HTMLImageElement[]>} */
  const enemies = new Map();
  await Promise.all(
    [...enemyFrames].map(async ([key, url]) => {
      const m = /^enemy\.([a-z_]+)\.(\d)$/.exec(key);
      if (!m) return;
      const img = new Image();
      img.src = url;
      await img.decode();
      if (!enemies.has(m[1])) enemies.set(m[1], []);
      /** @type {HTMLImageElement[]} */ (enemies.get(m[1]))[Number(m[2])] = img;
    }),
  );
  /** @type {{ ctx: CanvasRenderingContext2D, imgs: HTMLImageElement[], flip: boolean }[]} */
  const enemyCells = [];
  if (enemies.size) {
    const head = document.createElement('div');
    head.textContent = '敵（2 コマ：待機・移動。右向き／左向き／交互の再生）';
    head.style.cssText = 'font-weight:bold;margin:14px 0 6px';
    panel.append(head);
  }
  const order = Object.keys(ENEMY_INFO).filter((k) => enemies.has(k));
  for (const kind of order) {
    const imgs = /** @type {HTMLImageElement[]} */ (enemies.get(kind));
    const row = document.createElement('div');
    row.className = 'proto-gallery-enemy';
    row.dataset.kind = kind;
    row.style.cssText = 'display:flex;align-items:flex-end;gap:10px;margin:6px 0';
    const name = document.createElement('div');
    name.textContent = `${ENEMY_INFO[kind].name}（${ENEMY_INFO[kind].size}）`;
    name.style.cssText = 'width:120px';
    row.append(name);
    const w = imgs[0].naturalWidth;
    const h = imgs[0].naturalHeight;
    for (const [label, which, flip] of /** @type {const} */ ([['コマ0', 0, false], ['コマ1', 1, false], ['左向き', -1, true], ['交互', -1, false]])) {
      const box = document.createElement('div');
      box.style.cssText = 'text-align:center';
      const cv = document.createElement('canvas');
      cv.width = w * SCALE;
      cv.height = h * SCALE;
      cv.style.cssText = 'background:#4f8a3e;image-rendering:pixelated';
      const ctx = /** @type {CanvasRenderingContext2D} */ (cv.getContext('2d'));
      ctx.imageSmoothingEnabled = false;
      if (which >= 0) ctx.drawImage(imgs[which], 0, 0, w * SCALE, h * SCALE);
      else enemyCells.push({ ctx, imgs, flip });
      const l = document.createElement('div');
      l.textContent = label;
      box.append(cv, l);
      row.append(box);
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
    // enemies alternate their two frames (about 3 per second here, to see each one)
    const ef = Math.floor(step / 3) % 2;
    for (const { ctx, imgs, flip } of enemyCells) {
      const { width: cw, height: ch } = ctx.canvas;
      ctx.clearRect(0, 0, cw, ch);
      ctx.save();
      if (flip) ctx.setTransform(-1, 0, 0, 1, cw, 0);
      ctx.drawImage(imgs[flip ? 0 : ef], 0, 0, cw, ch);
      ctx.restore();
    }
    panel.dataset.enemyFrame = String(ef);
  };
  draw();
  const timer = setInterval(() => {
    if (!panel.isConnected) return clearInterval(timer);
    step++;
    draw();
  }, 125);
  return { looks: [...looks.keys()].sort((a, b) => a - b), enemies: order };
}
