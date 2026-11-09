import { describe, it, expect } from 'vitest';
import { balancedWidth } from '../../src/ui/toast.js';

// v1.0 QA2 (C-6 / L-6): a toast that wraps must not leave its last character alone on a line.
describe('balancedWidth (the fallback for text-wrap: balance)', () => {
  it('leaves a message that fits on one line alone', () => {
    expect(balancedWidth(300, 520, 28)).toBe(0);
    expect(balancedWidth(520, 520, 28)).toBe(0);
  });

  it('splits a message one character too long into two even lines', () => {
    // 520 px box, 28 px padding: 492 px of text per line; 506 px of text = 36 characters of 14 px
    const w = balancedWidth(506 + 28, 520, 28);
    expect(w).toBeLessThan(520);
    expect(w - 28).toBeGreaterThanOrEqual(506 / 2); // two lines are enough
    expect(w - 28).toBeLessThan(506 / 2 + 20); // and about even
  });

  it('three lines when needed, never wider than the box', () => {
    const w = balancedWidth(1100 + 28, 520, 28);
    expect(Math.ceil(1100 / (w - 28))).toBe(3);
    expect(w).toBeLessThanOrEqual(520);
  });
});
