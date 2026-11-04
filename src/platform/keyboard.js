// @ts-check
// Keyboard input (for desktop development and testing).

const KEYS = {
  left: ['ArrowLeft', 'KeyA'],
  right: ['ArrowRight', 'KeyD'],
  up: ['ArrowUp', 'KeyW'],
  down: ['ArrowDown', 'KeyS'],
  dash: ['ShiftLeft', 'ShiftRight'],
  jump: ['Space', 'KeyK'],
  attack: ['KeyJ'],
  dodge: ['KeyL'],
  guard: ['KeyI'],
  bow: ['KeyU'],
  ability: ['KeyQ'],
};

/** Tap-type actions: a press is latched until the next sample so quick taps are never lost. */
const TAP_ACTIONS = /** @type {const} */ (['jump', 'attack', 'dodge', 'ability']);

export class KeyboardInput {
  /** @param {Window} win */
  constructor(win) {
    /** @type {Set<string>} */
    this.down = new Set();
    /** @type {Record<string, boolean>} */
    this.latched = {};
    win.addEventListener('keydown', (e) => {
      if (Object.values(KEYS).some((codes) => codes.includes(e.code))) e.preventDefault();
      if (!e.repeat) {
        for (const a of TAP_ACTIONS) if (KEYS[a].includes(e.code)) this.latched[a] = true;
      }
      this.down.add(e.code);
    });
    win.addEventListener('keyup', (e) => this.down.delete(e.code));
    win.addEventListener('blur', () => this.down.clear());
  }

  /** For tests and older callers. */
  get jumpLatched() {
    return !!this.latched.jump;
  }

  /** @param {keyof typeof KEYS} action */
  pressed(action) {
    return KEYS[action].some((c) => this.down.has(c));
  }

  /** @param {typeof TAP_ACTIONS[number]} action */
  tap(action) {
    const v = this.pressed(action) || !!this.latched[action];
    this.latched[action] = false;
    return v;
  }

  sample() {
    const x = (this.pressed('right') ? 1 : 0) - (this.pressed('left') ? 1 : 0);
    const y = (this.pressed('down') ? 1 : 0) - (this.pressed('up') ? 1 : 0);
    const len = Math.hypot(x, y) || 1;
    return {
      moveX: x / len,
      moveY: y / len,
      dash: this.pressed('dash'),
      jump: this.tap('jump'),
      attack: this.tap('attack'),
      dodge: this.tap('dodge'),
      guard: this.pressed('guard'),
      bow: this.pressed('bow'),
      ability: this.tap('ability'),
    };
  }

  clear() {
    this.down.clear();
    this.latched = {};
  }
}
