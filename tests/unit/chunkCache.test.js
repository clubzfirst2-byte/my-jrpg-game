import { describe, it, expect } from 'vitest';
import { TexturePool } from 'pixi.js';
import { CHUNK, chunkCacheArea } from '../../src/view/gameView.js';

// v1.0 final (QA C-1): a 1 px dark line across the grass north of the beach ring (island chunk 1,1,
// world rows 46 and 58), only at some screen sizes (852×393 at DPR 2: internal height 394).
// The chunk's flat-ground cache was sized to the flat tiles' bounds (512×384 there: its top rows are
// raised). PixiJS's texture pool backs a request that fits under the screen at the SCREEN's size, so
// that cache got a 512×394 texture for a 512×384 frame, and the tiles' pixel snapping in that render
// left two 1-texel rows of it empty. The cache now always covers the whole chunk (512×512).

describe('chunk ground cache', () => {
  it('reproduces the cause: a part-chunk request gets a screen-sized backing taller than its frame', () => {
    TexturePool.setScreenSize(999_001, 852, 394);
    try {
      expect(TexturePool.getOptimalSize(512, 384)).toEqual({ width: 512, height: 394 });
    } finally {
      TexturePool.removeScreen(999_001);
    }
  });

  it('covers the whole chunk, a power of two: frame and backing match at every iPhone size', () => {
    const area = chunkCacheArea(1, 1, 16);
    expect(area).toEqual({ x: 512, y: 512, width: CHUNK * 16, height: CHUNK * 16 });
    // internal sizes of 734×343@3, 852×393@2, 852×393@3, 932×430@3, and a big desktop window
    for (const [w, h] of [[882, 412], [852, 394], [852, 394], [932, 430], [1920, 1080]]) {
      TexturePool.setScreenSize(999_002, w, h);
      try {
        expect(TexturePool.getOptimalSize(area.width, area.height), `${w}×${h}`).toEqual({ width: area.width, height: area.height });
      } finally {
        TexturePool.removeScreen(999_002);
      }
    }
  });

  it('a chunk at the edge of a map that is not a whole number of chunks is still cached whole', () => {
    expect(chunkCacheArea(0, 0, 16)).toEqual({ x: 0, y: 0, width: 512, height: 512 });
  });
});
