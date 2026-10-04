export type ConversationState = 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'STOPPED' | 'ERROR';
export type ConversationEvent = 'START' | 'START_OPENING' | 'STOP' | 'SPEECH_END' | 'AUDIO_READY' | 'PLAYBACK_ENDED' | 'FAIL' | 'RETRY';

export function micEnabled(state: ConversationState): boolean { return state === 'LISTENING'; }
export function transition(state: ConversationState, event: ConversationEvent): ConversationState {
  if (event === 'STOP') return 'STOPPED';
  if (event === 'FAIL') return state === 'STOPPED' ? 'STOPPED' : 'ERROR';
  if (state === 'STOPPED' && event === 'START_OPENING') return 'PROCESSING';
  if (state === 'STOPPED' && event === 'START') return 'LISTENING';
  if (state === 'LISTENING' && event === 'SPEECH_END') return 'PROCESSING';
  if (state === 'PROCESSING' && event === 'AUDIO_READY') return 'SPEAKING';
  if (state === 'SPEAKING' && event === 'PLAYBACK_ENDED') return 'LISTENING';
  if (state === 'ERROR' && event === 'RETRY') return 'PROCESSING';
  return state;
}
