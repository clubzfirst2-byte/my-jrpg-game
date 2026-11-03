// @ts-check

/**
 * Collects device information for reports.
 * @param {WebGLRenderingContext | WebGL2RenderingContext | undefined | null} gl
 * @param {string} rendererName
 * @returns {Record<string, string|number>}
 */
export function collectDeviceInfo(gl, rendererName) {
  let gpu = 'unknown';
  let glVersion = 'unknown';
  if (gl) {
    glVersion = String(gl.getParameter(gl.VERSION));
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    gpu = String(ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER));
  }
  const standalone =
    window.matchMedia?.('(display-mode: standalone)').matches ||
    /** @type {any} */ (navigator).standalone === true;
  return {
    UserAgent: navigator.userAgent,
    画面サイズ: `${window.screen.width}×${window.screen.height}`,
    表示領域: `${window.innerWidth}×${window.innerHeight}`,
    devicePixelRatio: window.devicePixelRatio,
    描画方式: rendererName,
    WebGL: glVersion,
    GPU: gpu,
    ホーム画面から起動: standalone ? 'はい' : 'いいえ',
  };
}
