// @ts-check
// On-screen measurement / error UI (DOM). Lets the iPhone itself show performance and errors.

/**
 * @param {string} tag
 * @param {Record<string, string>} [attrs]
 * @param {string} [text]
 */
function el(tag, attrs = {}, text = '') {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text) node.textContent = text;
  return node;
}

/**
 * @typedef {object} OverlayHandlers
 * @property {(factor: number) => void} onScaleSprites  multiply bench sprite count (0 = clear)
 * @property {() => void} onStartReport
 */

/**
 * @param {HTMLElement} root
 * @param {import('./errorLog.js').ErrorLog} errorLog
 * @param {OverlayHandlers} handlers
 * @param {{ open: boolean, reportSec: number }} options
 */
export function createOverlay(root, errorLog, handlers, options) {
  const toggle = el('button', { id: 'debug-toggle', type: 'button', 'aria-expanded': String(options.open) }, '計測');
  const badge = el('button', { id: 'error-badge', type: 'button', hidden: '' }, '');
  const panel = el('div', { id: 'debug-panel', role: 'status' });
  if (!options.open) panel.hidden = true;

  const statsText = el('pre', { id: 'debug-stats' }, '計測中…');
  const controls = el('div', { class: 'debug-controls' });
  const btnLess = el('button', { type: 'button', 'data-action': 'less' }, '負荷 ÷2');
  const btnMore = el('button', { type: 'button', 'data-action': 'more' }, '負荷 ×2');
  const btnClear = el('button', { type: 'button', 'data-action': 'clear' }, '負荷 0');
  const btnReport = el('button', { type: 'button', id: 'debug-report-start' }, `計測 ${options.reportSec}秒`);
  controls.append(btnLess, btnMore, btnClear, btnReport);
  panel.append(statsText, controls);

  const modal = el('div', { id: 'debug-modal', hidden: '' });
  const modalTitle = el('h2', {}, '');
  const modalBody = /** @type {HTMLTextAreaElement} */ (el('textarea', { id: 'debug-modal-body', readonly: '' }));
  const modalActions = el('div', { class: 'debug-controls' });
  const btnCopy = el('button', { type: 'button', id: 'debug-copy' }, 'コピー');
  const btnClose = el('button', { type: 'button' }, '閉じる');
  const copyState = el('span', { class: 'copy-state' }, '');
  modalActions.append(btnCopy, btnClose, copyState);
  modal.append(modalTitle, modalBody, modalActions);

  root.append(toggle, badge, panel, modal);

  toggle.addEventListener('click', () => {
    panel.hidden = !panel.hidden;
    toggle.setAttribute('aria-expanded', String(!panel.hidden));
  });
  btnLess.addEventListener('click', () => handlers.onScaleSprites(0.5));
  btnMore.addEventListener('click', () => handlers.onScaleSprites(2));
  btnClear.addEventListener('click', () => handlers.onScaleSprites(0));
  btnReport.addEventListener('click', () => handlers.onStartReport());
  btnClose.addEventListener('click', () => {
    modal.hidden = true;
  });
  btnCopy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(modalBody.value);
      copyState.textContent = 'コピーしました';
    } catch {
      // Clipboard API may be unavailable (http on LAN etc.): fall back to manual selection.
      modalBody.focus();
      modalBody.select();
      copyState.textContent = '選択しました。長押しでコピーしてください';
    }
  });

  /** @param {string} title @param {string} body */
  function showModal(title, body) {
    modalTitle.textContent = title;
    modalBody.value = body;
    copyState.textContent = '';
    modal.hidden = false;
  }

  function refreshBadge() {
    badge.hidden = errorLog.total === 0;
    badge.textContent = `エラー ${errorLog.total}`;
  }
  errorLog.onAdd(refreshBadge);
  refreshBadge();
  badge.addEventListener('click', () => {
    const text = errorLog.entries
      .map((e) => `[${(e.time / 1000).toFixed(1)}s ${e.kind}] ${e.message}`)
      .join('\n\n');
    showModal(`エラー一覧（全 ${errorLog.total} 件、最新 ${errorLog.entries.length} 件を表示）`, text || 'なし');
  });

  return {
    /** @param {string} text */
    setStats(text) {
      if (!panel.hidden) statsText.textContent = text;
    },
    /** @param {number | null} secondsLeft null = idle */
    setRecording(secondsLeft) {
      btnReport.toggleAttribute('disabled', secondsLeft !== null);
      btnReport.textContent = secondsLeft === null ? `計測 ${options.reportSec}秒` : `計測中… 残り${secondsLeft}秒`;
    },
    /** @param {string} markdown */
    showReport(markdown) {
      showModal('計測レポート（docs/device-tests/ に貼り付けてください）', markdown);
    },
  };
}
