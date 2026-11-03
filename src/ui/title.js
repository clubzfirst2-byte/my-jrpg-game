// @ts-check
// Title screen (P3.5): "はじめから" / "つづきから". Starting a new game while a save exists asks for
// confirmation and explains that the next save overwrites the old one (DESIGN.md 2.6).

export class TitleScreen {
  /**
   * @param {HTMLElement} root
   * @param {{ title: string, hasSave: boolean, saveNote: string, onNew: () => void, onContinue: () => void }} opts
   */
  constructor(root, opts) {
    this.el = document.createElement('div');
    this.el.id = 'title-screen';
    const h = document.createElement('h1');
    h.textContent = opts.title;
    const buttons = document.createElement('div');
    buttons.className = 'title-buttons';

    const cont = document.createElement('button');
    cont.type = 'button';
    cont.id = 'title-continue';
    cont.textContent = 'つづきから';
    cont.disabled = !opts.hasSave;

    const fresh = document.createElement('button');
    fresh.type = 'button';
    fresh.id = 'title-new';
    fresh.textContent = 'はじめから';

    const note = document.createElement('p');
    note.className = 'title-note';
    note.textContent = opts.saveNote;

    const confirmBox = document.createElement('div');
    confirmBox.className = 'title-confirm';
    confirmBox.hidden = true;
    const msg = document.createElement('p');
    msg.textContent = 'はじめから遊びますか？ いまの保存データは、次に保存したときに上書きされます。';
    const yes = document.createElement('button');
    yes.type = 'button';
    yes.id = 'title-confirm-yes';
    yes.textContent = 'はじめから遊ぶ';
    const no = document.createElement('button');
    no.type = 'button';
    no.id = 'title-confirm-no';
    no.textContent = 'もどる';
    confirmBox.append(msg, yes, no);

    cont.addEventListener('click', () => {
      this.hide();
      opts.onContinue();
    });
    fresh.addEventListener('click', () => {
      if (!opts.hasSave) {
        this.hide();
        opts.onNew();
        return;
      }
      buttons.hidden = true;
      confirmBox.hidden = false;
    });
    yes.addEventListener('click', () => {
      this.hide();
      opts.onNew();
    });
    no.addEventListener('click', () => {
      confirmBox.hidden = true;
      buttons.hidden = false;
    });

    if (opts.hasSave) buttons.append(cont, fresh);
    else buttons.append(fresh, cont);
    this.el.append(h, buttons, confirmBox, note);
    root.append(this.el);
  }

  get visible() {
    return !this.el.hidden;
  }

  hide() {
    this.el.hidden = true;
  }
}
