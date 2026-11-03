// @ts-check
// Keyboard input (for desktop development and testing).

const KEYS = {
  left: ['ArrowLeft', 'KeyA'],
  right: ['ArrowRight', 'KeyD'],
  up: ['ArrowUp', 'KeyW'],
  down: ['ArrowDown', 'KeyS'],
  dash: ['ShiftLeft', 'ShiftRight', 'KeyJ'],
  jump: ['Space', 'KeyK'],
};

export class KeyboardInput {
  /** @param {Window} win */
  constructor(win) {
    /** @type {Set<string>} */
    this.down = new Set();
    win.addEventListener('keydown', (e) => {
      if (Object.values(KEYS).some((codes) => codes.includes(e.code))) e.preventDefault();
      this.down.add(e.code);
    });
    win.addEventListener('keyup', (e) => this.down.delete(e.code));
    win.addEventListener('blur', () => this.down.clear());
  }

  /** @param {keyof typeof KEYS} action */
  pressed(action) {
    return KEYS[action].some((c) => this.down.has(c));
  }

  sample() {
    const x = (this.pressed('right') ? 1 : 0) - (this.pressed('left') ? 1 : 0);
    const y = (this.pressed('down') ? 1 : 0) - (this.pressed('up') ? 1 : 0);
    const len = Math.hypot(x, y) || 1;
    return { moveX: x / len, moveY: y / len, dash: this.pressed('dash'), jump: this.pressed('jump') };
  }

  clear() {
    this.down.clear();
  }
}
