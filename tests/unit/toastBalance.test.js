import { describe, it, expect } from 'vitest';
import { balancedWidth, phrases } from '../../src/ui/toast.js';

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

// Final QA L-6 (rest): the long boss message broke as 「…目を開け／た。」, inside a word.
describe('phrases (where a toast may break a line)', () => {
  it('breaks between phrases, never inside a word', () => {
    const p = phrases('裏返った星環——淀みの源が目を開けた。まわりの 4 つの座を目覚めさせよう');
    expect(p.join('')).toBe('裏返った星環——淀みの源が目を開けた。まわりの 4 つの座を目覚めさせよう');
    expect(p).toContain('開けた。');
    expect(p).toContain('目を');
    expect(p).not.toContain('た。');
  });

  it('keeps a bracketed name with its particle, and punctuation off the start of a line', () => {
    const p = phrases('星環の力「灯火」を手に入れた！ 右の「能力」ボタンで使える');
    expect(p).toContain('「灯火」を');
    for (const x of p) expect(x).not.toMatch(/^[、。！？」）]/);
    for (const x of p) expect(x).not.toMatch(/[「（]$/);
  });

  it('a short message without hiragana-to-word changes stays whole', () => {
    expect(phrases('穴に落ちた…')).toEqual(['穴に', '落ちた…']);
    expect(phrases('')).toEqual(['']);
  });
});
