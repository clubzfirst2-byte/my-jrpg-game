// @ts-check
// P11.5: the real art. A PNG in src/art/ named after a logical sprite name (for example
// src/art/player/player.down.0.png) replaces that placeholder sprite. Sub-folders are only for
// keeping things tidy; the file name is what counts. Missing files keep the placeholder art.

const files = /** @type {Record<string, string>} */ (import.meta.glob('../../art/**/*.png', { eager: true, query: '?url', import: 'default' }));

/** Logical sprite name → URL of its PNG. */
export const ART_OVERRIDES = new Map(Object.entries(files).map(([path, url]) => [/** @type {string} */ (path.split('/').pop()).replace(/\.png$/i, ''), url]));
