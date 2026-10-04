import { describe, expect, it } from 'vitest';
import { measureTiming } from './timing';
import { encodeWav } from './wav';
import { transition, micEnabled } from './stateMachine';

describe('timing from audio samples', () => {
  it('excludes padding and trailing silence but retains an internal pause', () => {
    const frames = [false, true, true, false, true, false, false].map(voiced => ({ voiced, samples: 512 }));
    expect(measureTiming(frames)).toEqual({ speech_span_ms: 128, voiced_ms: 96, pause_ms: 32 });
  });
  it('rejects silence and invalid frame sizes', () => {
    expect(measureTiming([{ voiced: false, samples: 512 }])).toBeNull();
    expect(() => measureTiming([{ voiced: true, samples: -1 }])).toThrow();
  });
  it('uses frame lengths rather than frame count', () => {
    expect(measureTiming([{ voiced: true, samples: 1600 }, { voiced: false, samples: 800 },
      { voiced: true, samples: 1600 }])).toEqual({ speech_span_ms: 250, voiced_ms: 200, pause_ms: 50 });
  });
});
describe('WAV', () => {
  it('writes PCM16 mono 16kHz with clipping and signed little endian samples', () => {
    const view = new DataView(encodeWav(new Float32Array([-2, -1, 0, 1, 2])));
    expect(view.getUint32(24, true)).toBe(16000);
    expect(view.getUint16(22, true)).toBe(1);
    expect(view.getUint16(34, true)).toBe(16);
    expect(view.getUint32(40, true)).toBe(10);
    expect(view.getInt16(44, true)).toBe(-32768);
    expect(view.getInt16(48, true)).toBe(0);
    expect(view.getInt16(52, true)).toBe(32767);
  });
  it('rejects empty/nonfinite audio', () => {
    expect(() => encodeWav(new Float32Array())).toThrow();
    expect(() => encodeWav(new Float32Array([NaN]))).toThrow();
  });
});
describe('half-duplex state machine', () => {
  it('gates capture through processing, speech, errors and stop', () => {
    let state = transition('STOPPED', 'START');
    expect(micEnabled(state)).toBe(true);
    state = transition(state, 'SPEECH_END');
    expect(state).toBe('PROCESSING'); expect(micEnabled(state)).toBe(false);
    expect(transition(state, 'SPEECH_END')).toBe(state);
    state = transition(state, 'AUDIO_READY');
    expect(state).toBe('SPEAKING'); expect(micEnabled(state)).toBe(false);
    state = transition(state, 'PLAYBACK_ENDED');
    expect(state).toBe('LISTENING');
    expect(transition(state, 'FAIL')).toBe('ERROR');
    expect(micEnabled('ERROR')).toBe(false);
    expect(transition('STOPPED', 'AUDIO_READY')).toBe('STOPPED');
  });
  it('never restarts from a late playback event after stop', () => {
    const stopped = transition('SPEAKING', 'STOP');
    expect(transition(stopped, 'PLAYBACK_ENDED')).toBe('STOPPED');
  });
});
