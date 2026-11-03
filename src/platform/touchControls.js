// @ts-check
// Virtual stick + dash button (DESIGN.md 5.8).
// The stick appears wherever the left half of the screen is touched. Pointer events are used,
// so touch, pen and mouse all work (mouse drag is handy for desktop testing and E2E).
import { normalizeStick } from '../game/input.js';

/** Stick travel radius in CSS px. */
const STICK_RADIUS = 44;

export class TouchControls {
  /** @param {HTMLElement} root */
  constructor(root) {
    this.layer = document.createElement('div');
    this.layer.id = 'touch-layer';
    this.base = document.createElement('div');
    this.base.id = 'stick-base';
    this.knob = document.createElement('div');
    this.knob.id = 'stick-knob';
    this.base.appendChild(this.knob);
    this.base.hidden = true;
    this.dashButton = document.createElement('button');
    this.dashButton.id = 'dash-button';
    this.dashButton.type = 'button';
    this.dashButton.textContent = 'ダッシュ';
    root.append(this.layer, this.base, this.dashButton);

    /** @type {number | null} */
    this.stickPointer = null;
    this.originX = 0;
    this.originY = 0;
    this.rawX = 0;
    this.rawY = 0;
    /** @type {Set<number>} */
    this.dashPointers = new Set();

    this.layer.addEventListener('pointerdown', (e) => this.onStickDown(e));
    window.addEventListener('pointermove', (e) => this.onStickMove(e));
    window.addEventListener('pointerup', (e) => this.onPointerEnd(e));
    window.addEventListener('pointercancel', (e) => this.onPointerEnd(e));

    this.dashButton.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      this.dashPointers.add(e.pointerId);
      this.dashButton.classList.add('active');
      try {
        this.dashButton.setPointerCapture(e.pointerId);
      } catch {
        // ignore: capture is best-effort
      }
    });
    // Prevent long-press menus / text selection on the controls.
    for (const el of [this.layer, this.base, this.dashButton]) {
      el.addEventListener('contextmenu', (e) => e.preventDefault());
    }
  }

  /** @param {PointerEvent} e */
  onStickDown(e) {
    // Left half only: the right half is reserved for action buttons.
    if (this.stickPointer !== null || e.clientX > window.innerWidth / 2) return;
    e.preventDefault();
    this.stickPointer = e.pointerId;
    this.originX = e.clientX;
    this.originY = e.clientY;
    this.rawX = 0;
    this.rawY = 0;
    this.base.style.left = `${e.clientX}px`;
    this.base.style.top = `${e.clientY}px`;
    this.base.hidden = false;
    this.updateKnob();
  }

  /** @param {PointerEvent} e */
  onStickMove(e) {
    if (e.pointerId !== this.stickPointer) return;
    this.rawX = (e.clientX - this.originX) / STICK_RADIUS;
    this.rawY = (e.clientY - this.originY) / STICK_RADIUS;
    this.updateKnob();
  }

  /** @param {PointerEvent} e */
  onPointerEnd(e) {
    if (e.pointerId === this.stickPointer) {
      this.stickPointer = null;
      this.rawX = 0;
      this.rawY = 0;
      this.base.hidden = true;
    }
    if (this.dashPointers.delete(e.pointerId) && this.dashPointers.size === 0) {
      this.dashButton.classList.remove('active');
    }
  }

  updateKnob() {
    const len = Math.hypot(this.rawX, this.rawY);
    const k = len > 1 ? 1 / len : 1;
    this.knob.style.transform = `translate(${this.rawX * k * STICK_RADIUS}px, ${this.rawY * k * STICK_RADIUS}px)`;
  }

  sample() {
    const v = normalizeStick(this.rawX, this.rawY);
    return { moveX: v.x, moveY: v.y, dash: this.dashPointers.size > 0 };
  }

  /** Releases everything (e.g. when the app goes to the background mid-touch). */
  clear() {
    this.stickPointer = null;
    this.rawX = 0;
    this.rawY = 0;
    this.base.hidden = true;
    this.dashPointers.clear();
    this.dashButton.classList.remove('active');
  }
}
