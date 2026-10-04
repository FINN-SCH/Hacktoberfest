export const SAMPLE_RATE = 16000;
export const TIMING_VERSION = 'silero-v5-positive-0.5-v1';
export interface ClassifiedFrame { voiced: boolean; samples: number }
export interface SpeechTiming { speech_span_ms: number; voiced_ms: number; pause_ms: number }

/** Trim only outer non-speech frames. Keep every internal pause. No wall-clock timing. */
export function measureTiming(frames: readonly ClassifiedFrame[]): SpeechTiming | null {
  for (const frame of frames) {
    if (!Number.isSafeInteger(frame.samples) || frame.samples <= 0) throw new Error('Invalid frame size');
  }
  const first = frames.findIndex(frame => frame.voiced);
  if (first < 0) return null;
  let last = frames.length - 1;
  while (!frames[last].voiced) last--;
  let span = 0, voiced = 0;
  for (let i = first; i <= last; i++) {
    span += frames[i].samples;
    if (frames[i].voiced) voiced += frames[i].samples;
  }
  const speech_span_ms = Math.round(span * 1000 / SAMPLE_RATE);
  const voiced_ms = Math.round(voiced * 1000 / SAMPLE_RATE);
  return { speech_span_ms, voiced_ms, pause_ms: speech_span_ms - voiced_ms };
}
