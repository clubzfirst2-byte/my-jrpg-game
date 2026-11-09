// Build-time constants injected by vite.config.js (define).
declare const __APP_VERSION__: string;
declare const __COMMIT__: string;

// Release art packing (vite.config.js, releaseArt): where each src/art-release/<group> was packed
// in the build (sheet PNG + frame table JSON URLs); null in the dev server.
declare module 'virtual:release-art' {
  const sheets: Record<string, { sheet: string; table: string }> | null;
  export default sheets;
}
