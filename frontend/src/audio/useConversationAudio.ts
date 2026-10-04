import { useCallback, useEffect, useRef, useState } from 'react';
import { useMicVAD } from '@ricky0123/vad-react';
import { measureTiming, type ClassifiedFrame, type SpeechTiming, SAMPLE_RATE, TIMING_VERSION } from './timing';
import { encodeWav } from './wav';
import { AudioPlayer } from './player';
import { transition, micEnabled, type ConversationEvent, type ConversationState } from './stateMachine';

export interface CapturedTurn {
  client_turn_id: string;
  audio: Blob;
  timing: SpeechTiming;
  timing_version: string;
  generation: number;
}
interface Options { onTurn: (turn: CapturedTurn) => Promise<void> | void }
const POSITIVE_THRESHOLD = 0.5;
const PRE_PAD_FRAMES = Math.floor(200 / 32); // pinned Silero v5: 512 samples at 16kHz

/** Mount in the conversation page. Start only from a user gesture; retain CapturedTurn for retries. */
export function useConversationAudio({ onTurn }: Options) {
  const [state, setState] = useState<ConversationState>('STOPPED');
  const [error, setError] = useState<string | null>(null);
  const stateRef = useRef<ConversationState>('STOPPED');
  const streamRef = useRef<MediaStream | null>(null);
  const frames = useRef<ClassifiedFrame[]>([]);
  const collecting = useRef(false);
  const sampleCount = useRef(0);
  const generation = useRef(0);
  const player = useRef(new AudioPlayer());
  const callback = useRef(onTurn);
  callback.current = onTurn;

  const clearFrames = useCallback(() => {
    frames.current = []; collecting.current = false; sampleCount.current = 0;
  }, []);
  const dispatch = useCallback((event: ConversationEvent) => {
    const next = transition(stateRef.current, event);
    stateRef.current = next;
    // Synchronous physical gating: React effects and VAD.pause() can finish later.
    if (!micEnabled(next)) streamRef.current?.getAudioTracks().forEach(track => { track.enabled = false; });
    setState(next);
  }, []);
  const fail = useCallback((reason: unknown) => {
    setError(reason instanceof Error ? reason.message : String(reason));
    dispatch('FAIL');
  }, [dispatch]);
  const acquireStream = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
    if (!micEnabled(stateRef.current)) {
      stream.getTracks().forEach(track => track.stop());
      throw new Error('Capture cancelled');
    }
    streamRef.current = stream;
    return stream;
  }, []);
  const pauseRef = useRef<() => Promise<void>>(async () => {});
  const vad = useMicVAD({
    model: 'v5', startOnLoad: false, baseAssetPath: '/vad/', onnxWASMBasePath: '/vad/',
    positiveSpeechThreshold: POSITIVE_THRESHOLD, negativeSpeechThreshold: 0.35,
    preSpeechPadMs: 200, redemptionMs: 1200, minSpeechMs: 400,
    submitUserSpeechOnPause: false,
    ortConfig: ort => { ort.env.wasm.numThreads = 1; },
    getStream: acquireStream,
    resumeStream: acquireStream,
    onFrameProcessed: (probabilities, frame) => {
      if (!micEnabled(stateRef.current)) return;
      const voiced = probabilities.isSpeech >= POSITIVE_THRESHOLD;
      frames.current.push({ voiced, samples: frame.length });
      if (voiced) collecting.current = true;
      if (!collecting.current) frames.current = frames.current.slice(-PRE_PAD_FRAMES);
      sampleCount.current = collecting.current ? sampleCount.current + frame.length : 0;
      if (sampleCount.current > SAMPLE_RATE * 180) {
        fail(new Error('Speech segment exceeds three minutes. Stop and start a shorter turn.'));
      }
    },
    onVADMisfire: clearFrames,
    onSpeechEnd: audio => {
      if (!micEnabled(stateRef.current)) return;
      dispatch('SPEECH_END'); // blocks subsequent callbacks before any await
      const currentGeneration = generation.current;
      try {
        const count = frames.current.reduce((sum, frame) => sum + frame.samples, 0);
        if (count !== audio.length) throw new Error('VAD frame alignment mismatch; timing unavailable');
        const timing = measureTiming(frames.current);
        if (!timing || timing.speech_span_ms > audio.length * 1000 / SAMPLE_RATE) throw new Error('Invalid speech timing');
        const turn: CapturedTurn = {
          client_turn_id: crypto.randomUUID(),
          audio: new Blob([encodeWav(audio)], { type: 'audio/wav' }),
          timing, timing_version: TIMING_VERSION, generation: currentGeneration,
        };
        clearFrames();
        void pauseRef.current().then(async () => {
          if (currentGeneration === generation.current && stateRef.current === 'PROCESSING') await callback.current(turn);
        }).catch(reason => { if (currentGeneration === generation.current) fail(reason); });
      } catch (reason) { clearFrames(); fail(reason); }
    },
  });
  pauseRef.current = vad.pause;

  // Serialize starts/pauses: permission acquisition or model setup may complete after Stop.
  const gate = useRef(Promise.resolve());
  useEffect(() => {
    if (vad.loading || vad.errored) return;
    gate.current = gate.current.then(async () => {
      if (micEnabled(stateRef.current)) {
        clearFrames();
        await vad.start();
        if (!micEnabled(stateRef.current)) await vad.pause();
      } else {
        await vad.pause();
        clearFrames();
      }
    }).catch(reason => {
      if (stateRef.current !== 'STOPPED') fail(reason);
    });
  }, [state, vad.loading, vad.errored, vad.start, vad.pause, clearFrames, fail]);

  useEffect(() => {
    return () => {
      generation.current++;
      stateRef.current = 'STOPPED';
      streamRef.current?.getTracks().forEach(track => track.stop());
      void player.current.dispose();
    };
  }, []);

  const start = async ({ opening = false }: { opening?: boolean } = {}) => {
    if (stateRef.current !== 'STOPPED') return;
    if (vad.loading || vad.errored) { setError(vad.errored || 'Speech detector is still loading'); return; }
    const currentGeneration = ++generation.current;
    try {
      // Must be called in the Start button handler to unlock playback.
      await player.current.unlock();
      if (currentGeneration !== generation.current) return;
      setError(null);
      dispatch(opening ? 'START_OPENING' : 'START');
      return currentGeneration;
    } catch (reason) {
      if (currentGeneration === generation.current) setError(String(reason));
    }
  };
  const stop = () => {
    generation.current++;
    dispatch('STOP');
    player.current.stop();
    streamRef.current?.getTracks().forEach(track => track.stop());
    clearFrames();
  };
  const playReply = async (audio: Blob, expectedGeneration: number) => {
    if (expectedGeneration !== generation.current || stateRef.current !== 'PROCESSING') return;
    dispatch('AUDIO_READY');
    try {
      await pauseRef.current();
      if (expectedGeneration !== generation.current || (stateRef.current as ConversationState) !== 'SPEAKING') return;
      await player.current.play(audio);
      if (expectedGeneration === generation.current) dispatch('PLAYBACK_ENDED');
    } catch (reason) {
      if (expectedGeneration === generation.current) fail(reason);
    }
  };
  const retry = async () => {
    if (stateRef.current !== 'ERROR') return;
    try {
      await player.current.unlock();
      setError(null);
      dispatch('RETRY');
    } catch (reason) { fail(reason); }
  };
  return { state, error: error || vad.errored || null, loading: vad.loading,
    userSpeaking: micEnabled(state) && vad.userSpeaking,
    start, stop, retry, playReply, fail, generation: generation.current };
}
