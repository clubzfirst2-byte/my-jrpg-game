// @ts-check
// Counts WebGL draw calls by wrapping the context's draw functions.
// Works on iPhone without any external inspector.

const DRAW_FNS = ['drawElements', 'drawArrays', 'drawElementsInstanced', 'drawArraysInstanced'];

/**
 * @param {WebGLRenderingContext | WebGL2RenderingContext | undefined | null} gl
 * @returns {{ take(): number, supported: boolean }}
 */
export function installDrawCounter(gl) {
  let count = 0;
  if (!gl) return { take: () => 0, supported: false };
  const target = /** @type {Record<string, any>} */ (/** @type {unknown} */ (gl));
  for (const name of DRAW_FNS) {
    const original = target[name];
    if (typeof original !== 'function') continue;
    target[name] = function (...args) {
      count++;
      return original.apply(this, args);
    };
  }
  return {
    supported: true,
    /** Returns the number of draw calls since the last call and resets the counter. */
    take() {
      const c = count;
      count = 0;
      return c;
    },
  };
}
