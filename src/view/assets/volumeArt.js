// @ts-check
// Stand-in art (仮の絵) for the things volume phase 1 adds, in the placeholder style (rows of palette
// letters, placeholderArt.js PALETTE). The real art is listed for the art director (v3); until it
// lands these keys are placeholder fallbacks (objectsArt.js PLACEHOLDER_FALLBACK_KEYS).

/** 12x22 wind vane (風車): a post with four blades; two frames (the blades straight / turned). @param {0 | 1} frame */
export function vaneSprite(frame) {
  const head =
    frame === 0
      ? ['.....aa.....', '.....aa.....', '.....aa.....', 'aaaaakkaaaaa', 'aaaaakkaaaaa', '.....aa.....', '.....aa.....', '.....aa.....']
      : ['.a........a.', '.aa......aa.', '..aa....aa..', '....akka....', '....akka....', '..aa....aa..', '.aa......aa.', '.a........a.'];
  return [
    ...head,
    '.....kk.....',
    '.....Nk.....',
    '.....Nk.....',
    '.....Nk.....',
    '.....Nk.....',
    '.....Nk.....',
    '.....Nk.....',
    '.....Nk.....',
    '....kNNk....',
    '...kBBBBk...',
    '..kBBvvBBk..',
    '..kBQQQQBk..',
    '..kkkkkkkk..',
    '............',
  ];
}

/** 12x20 survey stone (測量石): a squat stone with a disc on top; the disc glows once it is read. @param {boolean} on */
export function surveySprite(on) {
  const c = on ? 'I' : 'Q';
  const y = on ? 'J' : 'y';
  return [
    '............',
    '............',
    '....kkkk....',
    `...k${y}${y}${y}${y}k...`,
    `..k${y}${c}${c}${c}${c}${y}k..`,
    `..k${y}${c}kk${c}${y}k..`,
    `..k${y}${c}${c}${c}${c}${y}k..`,
    `...k${y}${y}${y}${y}k...`,
    '....kkkk....',
    '....kRrk....',
    '...kRRrmk...',
    '..kRRrrrmk..',
    '..kRrrrrmk..',
    `..kRr${c}${c}rmk..`,
    '..kRrrrrmk..',
    '..krrrrmmk..',
    '.kmrrrrmmmk.',
    'kkmmmmmmmmkk',
    'kmmmmmmmmmmk',
    'kkkkkkkkkkkk',
  ];
}

/** Keys and rows of the volume phase 1 stand-ins (anchored at the feet). */
export function volumeEntries() {
  return [
    { key: 'obj.vane.0', rows: vaneSprite(0) },
    { key: 'obj.vane.1', rows: vaneSprite(1) },
    { key: 'obj.survey.off', rows: surveySprite(false) },
    { key: 'obj.survey.on', rows: surveySprite(true) },
  ];
}
