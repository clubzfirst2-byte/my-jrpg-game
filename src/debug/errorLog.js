// @ts-check
// Collects runtime errors so they can be shown on screen (no Mac / Web Inspector needed).

/**
 * @typedef {object} ErrorEntry
 * @property {number} time  ms since page load
 * @property {'error'|'rejection'|'console'} kind
 * @property {string} message
 */

export class ErrorLog {
  /** @param {number} limit max entries kept */
  constructor(limit = 50) {
    this.limit = limit;
    /** @type {ErrorEntry[]} */
    this.entries = [];
    this.total = 0;
    /** @type {Set<(e: ErrorEntry) => void>} */
    this.listeners = new Set();
  }

  /**
   * @param {ErrorEntry['kind']} kind
   * @param {unknown} detail
   * @param {number} time
   */
  add(kind, detail, time) {
    const entry = { time, kind, message: describe(detail) };
    this.entries.push(entry);
    if (this.entries.length > this.limit) this.entries.shift();
    this.total++;
    for (const fn of this.listeners) fn(entry);
    return entry;
  }

  /** @param {(e: ErrorEntry) => void} fn */
  onAdd(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }
}

/** @param {unknown} detail */
export function describe(detail) {
  if (detail instanceof Error) {
    const stack = detail.stack ? detail.stack.split('\n').slice(0, 4).join('\n') : '';
    return stack.includes(detail.message) ? stack : `${detail.name}: ${detail.message}\n${stack}`.trim();
  }
  if (typeof detail === 'string') return detail;
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail);
  }
}

/**
 * Hook global error sources of a browser window into the log.
 * @param {ErrorLog} log
 * @param {Window} win
 */
export function installGlobalHandlers(log, win) {
  const now = () => win.performance.now();
  win.addEventListener('error', (ev) => {
    log.add('error', ev.error ?? `${ev.message} (${ev.filename}:${ev.lineno})`, now());
  });
  win.addEventListener('unhandledrejection', (ev) => {
    log.add('rejection', ev.reason, now());
  });
  const con = /** @type {Console} */ (/** @type {any} */ (win).console);
  const original = con.error.bind(con);
  con.error = (...args) => {
    log.add('console', args.map(describe).join(' '), now());
    original(...args);
  };
}
