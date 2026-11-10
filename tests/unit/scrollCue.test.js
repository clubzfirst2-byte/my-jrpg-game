import { describe, it, expect } from 'vitest';
import { hasMoreBelow } from '../../src/ui/scrollCue.js';

// v1.0 (iPhone): the shop / bag list shows a "more below" cue until it is scrolled to its end.
describe('hasMoreBelow', () => {
  it('is true while content is hidden below, false at the end or when nothing scrolls', () => {
    expect(hasMoreBelow({ scrollTop: 0, clientHeight: 200, scrollHeight: 320 })).toBe(true);
    expect(hasMoreBelow({ scrollTop: 119, clientHeight: 200, scrollHeight: 320 })).toBe(false); // within 1 px
    expect(hasMoreBelow({ scrollTop: 120, clientHeight: 200, scrollHeight: 320 })).toBe(false);
    expect(hasMoreBelow({ scrollTop: 0, clientHeight: 200, scrollHeight: 200 })).toBe(false);
  });
});
