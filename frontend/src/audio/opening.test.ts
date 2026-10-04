import { expect, it } from 'vitest';
import { transition, micEnabled } from './stateMachine';
it('keeps the mic disabled while fetching and speaking the saved opening turn', () => {
  const processing = transition('STOPPED', 'START_OPENING');
  expect(processing).toBe('PROCESSING');
  expect(micEnabled(processing)).toBe(false);
  const speaking = transition(processing, 'AUDIO_READY');
  expect(micEnabled(speaking)).toBe(false);
  expect(transition(speaking, 'PLAYBACK_ENDED')).toBe('LISTENING');
});
