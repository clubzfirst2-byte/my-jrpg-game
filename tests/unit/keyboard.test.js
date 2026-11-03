import { describe, it, expect } from 'vitest';
import { KeyboardInput } from '../../src/platform/keyboard.js';

/** Minimal window stand-in: just an event target. */
function fakeWindow() {
  const target = new EventTarget();
  return target;
}

function key(win, type, code, repeat = false) {
  const e = new Event(type);
  Object.assign(e, { code, repeat });
  win.dispatchEvent(e);
}

describe('KeyboardInput', () => {
  it('a jump tapped and released between two frames is still seen once', () => {
    const win = fakeWindow();
    const kb = new KeyboardInput(/** @type {any} */ (win));
    key(win, 'keydown', 'Space');
    key(win, 'keyup', 'Space');
    expect(kb.sample().jump).toBe(true); // the tap is not lost
    expect(kb.sample().jump).toBe(false); // and counts only once
  });

  it('a held jump stays held; key repeat does not create extra presses', () => {
    const win = fakeWindow();
    const kb = new KeyboardInput(/** @type {any} */ (win));
    key(win, 'keydown', 'Space');
    expect(kb.sample().jump).toBe(true);
    key(win, 'keydown', 'Space', true);
    expect(kb.sample().jump).toBe(true);
    key(win, 'keyup', 'Space');
    expect(kb.sample().jump).toBe(false);
  });

  it('maps arrows to a normalized move vector', () => {
    const win = fakeWindow();
    const kb = new KeyboardInput(/** @type {any} */ (win));
    key(win, 'keydown', 'ArrowRight');
    key(win, 'keydown', 'ArrowUp');
    const s = kb.sample();
    expect(Math.hypot(s.moveX, s.moveY)).toBeCloseTo(1, 6);
    expect(s.moveX).toBeGreaterThan(0);
    expect(s.moveY).toBeLessThan(0);
  });
});
