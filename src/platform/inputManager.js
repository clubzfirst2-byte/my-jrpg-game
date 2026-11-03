// @ts-check
// Merges all input sources into the logic layer's InputFrame (DESIGN.md 1.1).
import { KeyboardInput } from './keyboard.js';
import { TouchControls } from './touchControls.js';

export class InputManager {
  /** @param {HTMLElement} uiRoot */
  constructor(uiRoot) {
    this.keyboard = new KeyboardInput(window);
    this.touch = new TouchControls(uiRoot);
  }

  /** @returns {import('../game/input.js').InputFrame} */
  sample() {
    const k = this.keyboard.sample();
    const t = this.touch.sample();
    // Whichever source pushes harder wins; dash from either.
    const useTouch = Math.hypot(t.moveX, t.moveY) > Math.hypot(k.moveX, k.moveY);
    return {
      moveX: useTouch ? t.moveX : k.moveX,
      moveY: useTouch ? t.moveY : k.moveY,
      dash: k.dash || t.dash,
      jump: k.jump || t.jump,
    };
  }

  clear() {
    this.keyboard.clear();
    this.touch.clear();
  }
}
