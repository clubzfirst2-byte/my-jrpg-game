// @ts-check
// When to save (DESIGN.md 2.6): right after something worth keeping happened (a chest, a
// checkpoint — the logic sets state.saveRequested), every minute of play, and when the app goes to
// the background. Failures are shown to the player; the previous save stays intact.
import { failureMessage } from './saveFormat.js';

export const AUTOSAVE_INTERVAL_MS = 60_000;

export class Autosave {
  /**
   * @param {import('./saveStore.js').SaveStore} store
   * @param {() => any} snapshot   returns the data to save
   * @param {(msg: string) => void} onError
   */
  constructor(store, snapshot, onError) {
    this.store = store;
    this.snapshot = snapshot;
    this.onError = onError;
    this.enabled = false;
    this.sincePlayMs = 0;
    this.saves = 0;
    this.failures = 0;
    /** @type {string | null} */
    this.lastError = null;
    this.lastFailedReason = '';
  }

  /** Call every frame with the real time played (not while paused / on the title). @param {any} state @param {number} dtMs */
  update(state, dtMs) {
    if (!this.enabled) return;
    this.sincePlayMs += dtMs;
    if (state.saveRequested || this.sincePlayMs >= AUTOSAVE_INTERVAL_MS) {
      state.saveRequested = false;
      void this.saveNow();
    }
  }

  /** @returns {Promise<boolean>} */
  async saveNow() {
    if (!this.enabled) return false;
    this.sincePlayMs = 0;
    const r = await this.store.save(this.snapshot());
    if (r.ok === true) {
      this.saves++;
      this.lastFailedReason = '';
      return true;
    }
    if (r.ok !== false) return false;
    this.failures++;
    const msg = failureMessage(r.reason);
    this.lastError = msg;
    // Do not repeat the same message every minute.
    if (this.lastFailedReason !== r.reason) this.onError(msg);
    this.lastFailedReason = r.reason;
    return false;
  }
}
