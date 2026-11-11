// @ts-check
// Graphics v3 (artV3.js): a left-facing frame may be its right frame mirrored (SpriteMeta.flipX), so a
// sprite that shows directional frames takes its texture, anchor and mirroring together from here.

/**
 * Shows frame `key` on a sprite: its texture and anchor, mirrored when the frame is (flipX). Without v3
 * (no frame is mirrored) this only sets the texture and anchor the sprite already had.
 * @param {import('pixi.js').Sprite} sprite @param {import('./assets/assetManager.js').AssetManager} assets @param {string} key
 */
export function setFrame(sprite, assets, key) {
  sprite.texture = assets.texture(key);
  const m = assets.meta(key);
  if (m.flipX) {
    sprite.anchor.set(m.anchor[0], m.anchor[1]);
    if (sprite.scale.x > 0) sprite.scale.x = -sprite.scale.x;
  } else if (sprite.scale.x < 0) {
    sprite.anchor.set(m.anchor[0], m.anchor[1]);
    sprite.scale.x = -sprite.scale.x;
  }
}
