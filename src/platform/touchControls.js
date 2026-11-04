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
    root.append(this.layer, this.base);
    // Right-hand cluster (DESIGN.md 5.8): attack is the big main button, the rest arc around it.
    this.attack = new HoldButton(root, 'attack-button', '攻撃');
    this.jump = new HoldButton(root, 'jump-button', 'ジャンプ');
    this.dodge = new HoldButton(root, 'dodge-button', '回避');
    this.bow = new HoldButton(root, 'bow-button', '弓');
    this.guard = new HoldButton(root, 'guard-button', 'ガード');
    this.dash = new HoldButton(root, 'dash-button', 'ダッシュ');
    // P7: the selected 星環 ability (its label shows which one).
    this.ability = new HoldButton(root, 'ability-button', '能力');

    /** @type {number | null} */
    this.stickPointer = null;
    this.originX = 0;
    this.originY = 0;
    this.rawX = 0;
    this.rawY = 0;

    this.layer.addEventListener('pointerdown', (e) => this.onStickDown(e));
    window.addEventListener('pointermove', (e) => this.onStickMove(e));
    window.addEventListener('pointerup', (e) => this.onPointerEnd(e));
    window.addEventListener('pointercancel', (e) => this.onPointerEnd(e));

    // Prevent long-press menus / text selection on the controls.
    for (const el of [this.layer, this.base]) {
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
  }

  updateKnob() {
    const len = Math.hypot(this.rawX, this.rawY);
    const k = len > 1 ? 1 / len : 1;
    this.knob.style.transform = `translate(${this.rawX * k * STICK_RADIUS}px, ${this.rawY * k * STICK_RADIUS}px)`;
  }

  sample() {
    const v = normalizeStick(this.rawX, this.rawY);
    return {
      moveX: v.x,
      moveY: v.y,
      dash: this.dash.held,
      jump: this.jump.consumePress(),
      attack: this.attack.consumePress(),
      dodge: this.dodge.consumePress(),
      guard: this.guard.held,
      bow: this.bow.held,
      ability: this.ability.consumePress(),
    };
  }

  /** Releases everything (e.g. when the app goes to the background mid-touch). */
  clear() {
    this.stickPointer = null;
    this.rawX = 0;
    this.rawY = 0;
    this.base.hidden = true;
    for (const b of [this.dash, this.jump, this.attack, this.dodge, this.bow, this.guard, this.ability]) b.clear();
  }
}

/** A button that reports "held" while any pointer presses it (multi-touch safe). */
class HoldButton {
  /** @param {HTMLElement} root @param {string} id @param {string} label */
  constructor(root, id, label) {
    this.el = document.createElement('button');
    this.el.id = id;
    this.el.type = 'button';
    this.el.className = 'action-button';
    this.el.textContent = label;
    root.append(this.el);
    /** @type {Set<number>} */
    this.pointers = new Set();
    /** Pressed since the last consumePress(): a tap shorter than one frame still counts. */
    this.latched = false;
    this.el.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      this.pointers.add(e.pointerId);
      this.latched = true;
      this.el.classList.add('active');
      try {
        this.el.setPointerCapture(e.pointerId);
      } catch {
        // capture is best-effort
      }
    });
    const end = (/** @type {PointerEvent} */ e) => {
      if (this.pointers.delete(e.pointerId) && this.pointers.size === 0) this.el.classList.remove('active');
    };
    window.addEventListener('pointerup', end);
    window.addEventListener('pointercancel', end);
    this.el.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  get held() {
    return this.pointers.size > 0;
  }

  /** Held now, or tapped since the last call. */
  consumePress() {
    const v = this.held || this.latched;
    this.latched = false;
    return v;
  }

  clear() {
    this.pointers.clear();
    this.latched = false;
    this.el.classList.remove('active');
  }
}
