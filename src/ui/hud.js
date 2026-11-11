// @ts-check
// Hearts HUD. Health is counted in quarter hearts (4 per heart).

const SVG_NS = 'http://www.w3.org/2000/svg';
const HEART_PATH = 'M11 19 L2.5 10.5 A5 5 0 0 1 11 4 A5 5 0 0 1 19.5 10.5 Z';

export class HeartsHud {
  /** @param {HTMLElement} root */
  constructor(root) {
    this.el = document.createElement('div');
    this.el.id = 'hud-hearts';
    this.el.setAttribute('role', 'img');
    root.append(this.el);
    this.hp = -1;
    this.maxHp = -1;
  }

  /** @param {number} hp @param {number} maxHp */
  update(hp, maxHp) {
    if (hp === this.hp && maxHp === this.maxHp) return;
    this.hp = hp;
    this.maxHp = maxHp;
    this.el.replaceChildren();
    this.el.setAttribute('aria-label', `体力 ${hp / 4} / ${maxHp / 4}`);
    this.el.dataset.hp = String(hp);
    for (let i = 0; i < maxHp / 4; i++) {
      const fill = Math.max(0, Math.min(4, hp - i * 4)) / 4; // 0, .25, .5, .75, 1
      this.el.append(heart(fill, i));
    }
  }
}

/** @param {number} fill 0..1 @param {number} i */
function heart(fill, i) {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 22 20');
  svg.dataset.q = String(Math.round(fill * 4)); // W4: the v2 UI draws heart.<q> (quarters) instead
  const clipId = `heart-clip-${i}`;
  const defs = document.createElementNS(SVG_NS, 'defs');
  const clip = document.createElementNS(SVG_NS, 'clipPath');
  clip.id = clipId;
  const rect = document.createElementNS(SVG_NS, 'rect');
  rect.setAttribute('x', '0');
  rect.setAttribute('y', '0');
  rect.setAttribute('width', String(22 * fill));
  rect.setAttribute('height', '20');
  clip.append(rect);
  defs.append(clip);
  const empty = document.createElementNS(SVG_NS, 'path');
  empty.setAttribute('d', HEART_PATH);
  empty.setAttribute('fill', '#3a2230');
  empty.setAttribute('stroke', '#1a1c2c');
  empty.setAttribute('stroke-width', '1.5');
  const full = document.createElementNS(SVG_NS, 'path');
  full.setAttribute('d', HEART_PATH);
  full.setAttribute('fill', '#e8505b');
  full.setAttribute('clip-path', `url(#${clipId})`);
  svg.append(defs, empty, full);
  return svg;
}
