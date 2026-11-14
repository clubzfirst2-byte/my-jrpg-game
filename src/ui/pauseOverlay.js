// @ts-check
// Pause screen and pause button. Resuming needs a tap, which also satisfies iOS's
// user-gesture rule for audio (DESIGN.md 2.3). P11.2: the sound volumes are set here.

export class PauseOverlay {
  /**
   * @param {HTMLElement} root
   * @param {{ onPauseRequest: () => void, onResume: () => void, onVolume?: (kind: 'bgm' | 'sfx') => void, volumes?: () => { bgm: number, sfx: number }, onSettings?: () => void, onTitle?: () => void, onMap?: () => void, version?: string }} handlers
   *   onTitle: v1.0 「タイトルへ」 (saves, then back to the title; only when given); version: shown small
   */
  constructor(root, handlers) {
    this.handlers = handlers;
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
    // P11.2: sound volumes (tapping one steps it; the rest of the screen resumes).
    const sound = document.createElement('div');
    sound.className = 'pause-sound';
    /** @param {'bgm' | 'sfx'} kind */
    const volumeButton = (kind) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.id = `volume-${kind}`;
      b.addEventListener('click', (e) => {
        e.stopPropagation();
        handlers.onVolume?.(kind);
      });
      sound.append(b);
      return b;
    };
    this.bgmButton = volumeButton('bgm');
    this.sfxButton = volumeButton('sfx');
    // P11.3: the settings screen.
    const settings = document.createElement('button');
    settings.type = 'button';
    settings.id = 'open-settings';
    settings.textContent = '設定';
    settings.addEventListener('click', (e) => {
      e.stopPropagation();
      handlers.onSettings?.();
    });
    sound.append(settings);
    // v1.0: back to the title (the game saves first).
    if (handlers.onTitle) {
      const toTitle = document.createElement('button');
      toTitle.type = 'button';
      toTitle.id = 'pause-title-button';
      toTitle.textContent = 'タイトルへ';
      toTitle.addEventListener('click', (e) => {
        e.stopPropagation();
        handlers.onTitle?.();
      });
      sound.append(toTitle);
    }
    this.overlay.append(title);
    // v1.0 final: the version sits in the centred column under the title (it used to be pinned
    // to the top-left corner, where it overlapped the pause button).
    if (handlers.version) {
      const v = document.createElement('div');
      v.className = 'pause-version';
      v.textContent = handlers.version;
      this.overlay.append(v);
    }
    this.overlay.append(this.message);
    // Volume phase 1: the map (in the centred column, above the resume button).
    if (handlers.onMap) {
      const map = document.createElement('button');
      map.type = 'button';
      map.id = 'open-map';
      map.textContent = '地図';
      map.addEventListener('click', (e) => {
        e.stopPropagation();
        handlers.onMap?.();
      });
      this.overlay.append(map);
    }
    this.overlay.append(sound, resume);
    this.refresh();
    this.overlay.addEventListener('click', () => handlers.onResume());

    root.append(this.button, this.overlay);
  }

  /** @param {string} message */
  show(message = '') {
    this.message.textContent = message;
    this.refresh();
    this.overlay.hidden = false;
  }

  /** Shows the current volumes on the buttons. */
  refresh() {
    const v = this.handlers.volumes?.() ?? { bgm: 0.5, sfx: 0.8 };
    const label = (/** @type {number} */ x) => (x <= 0 ? 'オフ' : `${Math.round(x * 100)}%`);
    this.bgmButton.textContent = `BGM ${label(v.bgm)}`;
    this.sfxButton.textContent = `効果音 ${label(v.sfx)}`;
  }

  hide() {
    this.overlay.hidden = true;
  }

  get visible() {
    return !this.overlay.hidden;
  }
}
