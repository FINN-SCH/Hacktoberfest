import { describe, expect, it } from 'vitest';
import { highlightParts } from './highlights';
import type { Schema } from '../api/client';
const correction = (extra: Partial<Schema<'CorrectionOut'>> = {}): Schema<'CorrectionOut'> => ({
  id: 1, original: 'habe', corrected: 'bin', corrected_sentence: 'Ich bin gegangen.', kind: 'error',
  topic: 'de_perfekt_auxiliary', topic_label: 'Auxiliary', explanation: 'Use sein', status: 'active',
  highlight_start: 2, highlight_end: 6, ...extra,
});
describe('evidence highlights', () => {
  it('interprets server offsets as code points after an astral character', () => {
    expect(highlightParts('𐐀 habe gesprochen.', [correction()])).toEqual([
      { text: '𐐀 ', highlighted: false }, { text: 'habe', highlighted: true }, { text: ' gesprochen.', highlighted: false },
    ]);
  });
  it('keeps text intact for null, excluded, overlapping or mismatched spans', () => {
    const text = 'Ich habe gesprochen.';
    const parts = highlightParts(text, [correction({ highlight_start: null }), correction({ status: 'excluded' }), correction()]);
    expect(parts).toEqual([{ text, highlighted: false }]);
    const duplicate = correction({ highlight_start: 4, highlight_end: 8 });
    expect(highlightParts(text, [duplicate, duplicate]).filter(x => x.highlighted)).toHaveLength(1);
  });
});
