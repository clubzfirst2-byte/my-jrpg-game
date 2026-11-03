// @ts-check
// Landscape is the intended orientation (DESIGN.md 2.5). On touch devices held upright, ask the
// player to rotate. The game still works in portrait (the camera adapts), so it can be dismissed.

export class RotateHint {
  /** @param {HTMLElement} root */
  constructor(root) {
    this.el = document.createElement('div');
    this.el.id = 'rotate-hint';
    const icon = document.createElement('div');
    icon.className = 'rotate-icon';
    icon.setAttribute('aria-hidden', 'true');
    const text = document.createElement('div');
    text.textContent = '画面を横向きにして遊んでください';
    const dismiss = document.createElement('button');
    dismiss.type = 'button';
    dismiss.id = 'rotate-dismiss';
    dismiss.textContent = 'このまま続ける';
    dismiss.addEventListener('click', () => this.el.classList.add('dismissed'));
    this.el.append(icon, text, dismiss);
    root.append(this.el);
  }

  /** Whether the hint is currently shown (for tests). */
  get visible() {
    return getComputedStyle(this.el).display !== 'none';
  }
}
