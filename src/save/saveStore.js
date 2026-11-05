// @ts-check
// IndexedDB save store (DESIGN.md 2.6). Two generations (A / B) are written alternately; the data
// and the "which one is latest" record are committed in ONE transaction, so an interrupted write
// leaves the previous generation intact. Writes never overlap: requests are queued and coalesced.
import { chooseSave, classifyError, makeEnvelope, needsLegacyObjects, useLegacyObjects } from './saveFormat.js';

const DB_NAME = 'seimyaku';
const STORE = 'saves';
const SLOT = 'slot1';

/** @returns {Promise<IDBDatabase>} */
function openDb() {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(Object.assign(new Error('IndexedDB is not available'), { name: 'InvalidStateError' }));
      return;
    }
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

/** @param {IDBRequest} r @returns {Promise<any>} */
const result = (r) =>
  new Promise((resolve, reject) => {
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });

export class SaveStore {
  /** @param {string} gameVersion */
  constructor(gameVersion) {
    this.gameVersion = gameVersion;
    /** @type {Promise<IDBDatabase> | null} */
    this.db = null;
    /** @type {Promise<void>} */
    this.queue = Promise.resolve();
    /** @type {Promise<any> | null} */
    this.waiting = null;
    /** @type {any} */
    this.pendingData = null;
    this.seq = 0;
  }

  /** @returns {Promise<IDBDatabase>} */
  database() {
    if (!this.db) this.db = openDb();
    return this.db;
  }

  /** Asks the browser not to evict our data under storage pressure (iOS). */
  async requestPersistence() {
    try {
      return (await navigator.storage?.persist?.()) ?? false;
    } catch {
      return false;
    }
  }

  /**
   * @returns {Promise<ReturnType<typeof chooseSave> | { status: 'error', reason: ReturnType<typeof classifyError> }>}
   */
  async load() {
    try {
      const db = await this.database();
      const tx = db.transaction(STORE, 'readonly');
      const store = tx.objectStore(STORE);
      const [a, b] = await Promise.all([result(store.get(`${SLOT}A`)), result(store.get(`${SLOT}B`))]);
      // P11.4: an old save (P8-P10.2) needs the old object lists, fetched only then.
      if (needsLegacyObjects(a) || needsLegacyObjects(b)) useLegacyObjects((await import('./legacyObjects.js')).LEGACY_OBJECTS);
      const choice = chooseSave(a ?? null, b ?? null);
      this.seq = Math.max(a?.seq ?? 0, b?.seq ?? 0);
      return choice;
    } catch (err) {
      return { status: 'error', reason: classifyError(err) };
    }
  }

  /**
   * Saves (queued; a burst of requests becomes one write of the latest data).
   * @param {any} data
   * @returns {Promise<{ ok: true } | { ok: false, reason: ReturnType<typeof classifyError> }>}
   */
  save(data) {
    this.pendingData = data;
    // A write that has not started yet will pick up this newer data: share its result.
    if (this.waiting) return this.waiting;
    /** @type {Promise<{ ok: true } | { ok: false, reason: ReturnType<typeof classifyError> }>} */
    const run = this.queue.then(async () => {
      this.waiting = null;
      const snapshot = this.pendingData;
      try {
        await this.write(snapshot);
        return { ok: /** @type {const} */ (true) };
      } catch (err) {
        return { ok: /** @type {const} */ (false), reason: classifyError(err) };
      }
    });
    this.waiting = run;
    this.queue = run.then(() => undefined);
    return run;
  }

  /** @param {any} data */
  async write(data) {
    const db = await this.database();
    const tx = db.transaction(STORE, 'readwrite');
    const store = tx.objectStore(STORE);
    const meta = await result(store.get(`${SLOT}meta`));
    const next = meta?.latest === 'A' ? 'B' : 'A';
    this.seq += 1;
    const env = makeEnvelope(data, this.gameVersion, this.seq, Date.now());
    store.put(env, `${SLOT}${next}`);
    store.put({ latest: next, seq: env.seq }, `${SLOT}meta`);
    await new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve(undefined);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  }

  /** Removes the save (used by "start a new game" after confirmation, and by tests). */
  async clear() {
    const db = await this.database();
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).clear();
    await new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve(undefined);
      tx.onerror = () => reject(tx.error);
    });
    this.seq = 0;
  }
}
