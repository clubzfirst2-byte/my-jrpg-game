// @ts-check
// gfx W5: which set of light / shadow / effects the view draws. Pure (unit-tested).
//
//   v2 (default)  cast shadows, lit windows at night, the two-layer rain with splashes and mist,
//                 ambient particles, hit sparks and the slash's after-images
//   v1            the look before W5 (none of the above): ?fx=v1, or ?v2=0 (every graphics-v2 group
//                 back to v1 at once); ?fx=v2 keeps the effects on even with ?v2=0
//
// Drawing only: nothing here is saved, and the game's logic never reads it.

/**
 * @param {{ get(name: string): string | null }} params the page's URL parameters
 * @returns {'v1' | 'v2'}
 */
export function fxVersion(params) {
  const fx = params.get('fx');
  if (fx === 'v1' || fx === 'v2') return fx;
  return params.get('v2') === '0' ? 'v1' : 'v2';
}
