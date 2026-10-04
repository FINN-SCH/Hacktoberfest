import { expect, it } from 'vitest';
import { measureTiming } from './timing';
it('rounds wire timings to integers while preserving the sum', () => {
  const result = measureTiming([{ voiced: true, samples: 511 }, { voiced: false, samples: 101 }, { voiced: true, samples: 501 }])!;
  expect(result).toEqual({ speech_span_ms: 70, voiced_ms: 63, pause_ms: 7 });
  expect(result.voiced_ms + result.pause_ms).toBe(result.speech_span_ms);
});
