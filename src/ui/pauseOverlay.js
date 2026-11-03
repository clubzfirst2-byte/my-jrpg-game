// @ts-check
// Pause screen and pause button. Resuming needs a tap, which also satisfies iOS's
// user-gesture rule for audio when sound is added later (DESIGN.md 2.3).

export class PauseOverlay {
  /**
   * @param {HTMLElement} root
   * @param {{ onPauseRequest: () => void, onResume: () => void }} handlers
   */
  constructor(root, handlers) {
    this.button = document.createElement('button');
    this.button.id = 'pause-button';
    this.button.type = 'button';
    this.button.setAttribute('aria-label', '一時停止');
    this.button.textContent = 'Ⅱ';
    this.button.addEventListener('click', () => handlers.onPauseRequest());

    this.overlay = document.createElement('div');
    this.overlay.id = 'pause-overlay';
    this.overlay.hidden = true;
    const title = document.createElement('div');
    title.className = 'pause-title';
    title.textContent = '一時停止中';
    this.message = document.createElement('div');
    this.message.className = 'pause-message';
    const resume = document.createElement('button');
    resume.type = 'button';
    resume.id = 'resume-button';
    resume.textContent = 'タップで再開';
    this.overlay.append(title, this.message, resume);
    this.overlay.addEventListener('click', () => handlers.onResume());

    root.append(this.button, this.overlay);
  }

  /** @param {string} message */
  show(message = '') {
    this.message.textContent = message;
    this.overlay.hidden = false;
  }

  hide() {
    this.overlay.hidden = true;
  }

  get visible() {
    return !this.overlay.hidden;
  }
}
