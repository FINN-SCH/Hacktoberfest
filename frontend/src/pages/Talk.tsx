import { useEffect, useRef, useState } from 'react';
import { ApiError, request, post, speech, message, type Schema } from '../api/client';
import { useConversationAudio, type CapturedTurn } from '../audio/useConversationAudio';
import type { SpeechTiming } from '../audio/timing';
import { LanguagePicker, ErrorNotice, languages } from '../components/Common';
import { Transcript } from '../components/Transcript';

interface Pending { client_turn_id: string; timing: SpeechTiming; audio?: Blob }
const storageKey = (id: number) => 'tutor.pending.' + id;
function readPending(id: number): Pending | null {
  try {
    const value = JSON.parse(localStorage.getItem(storageKey(id)) ?? 'null') as Pending | null;
    if (value && typeof value.client_turn_id === 'string' && value.timing &&
        [value.timing.speech_span_ms, value.timing.voiced_ms, value.timing.pause_ms].every(Number.isSafeInteger)) return value;
  } catch { /* corrupted or inaccessible browser storage */ }
  return null;
}
function persistPending(id: number, value: Pending | null) {
  if (value) localStorage.setItem(storageKey(id), JSON.stringify({ client_turn_id: value.client_turn_id, timing: value.timing }));
  else localStorage.removeItem(storageKey(id));
}
export function Talk({ profile, resumeId, openReport }: { profile: Schema<'ProfileOut'>; resumeId: number | null; openReport: (id: number) => void }) {
  const [language, setLanguage] = useState<Schema<'SessionCreate'>['target_language']>('de');
  const [level, setLevel] = useState<Schema<'SessionCreate'>['level']>('A2'), [scenario, setScenario] = useState<Schema<'SessionCreate'>['scenario']>('cafe');
  const [mode, setMode] = useState<Schema<'SessionCreate'>['explanation_mode']>(profile.default_explanation_mode);
  const [session, setSession] = useState<Schema<'SessionOut'> | null>(null);
  const [turns, setTurns] = useState<Schema<'TurnOut'>[]>([]);
  const [busy, setBusy] = useState(false), [error, setError] = useState<string | null>(null);
  const [check, setCheck] = useState<string | null>(null), [restoring, setRestoring] = useState(!!resumeId);
  const sessionRef = useRef<Schema<'SessionOut'> | null>(null);
  const pending = useRef<Pending | null>(null), replyId = useRef<number | null>(null);
  const active = useRef(true), action = useRef(0), networkBusy = useRef(false);
  const audio = useConversationAudio({ onTurn: async (captured: CapturedTurn) => {
    const current = sessionRef.current;
    if (!current) return;
    pending.current = { client_turn_id: captured.client_turn_id, timing: captured.timing, audio: captured.audio };
    persistPending(current.id, pending.current);
    await sendPending(current.id, captured.generation);
  } });
  useEffect(() => { active.current = true; return () => { active.current = false; action.current++; }; }, []);
  async function reload(id = sessionRef.current?.id) {
    if (!id) return;
    const next = await request<Schema<'TurnOut'>[]>('/sessions/' + id + '/turns');
    if (active.current && sessionRef.current?.id === id) setTurns(next);
    return next;
  }
  useEffect(() => {
    if (!resumeId) return;
    let cancelled = false; setRestoring(true);
    void (async () => {
      try {
        const saved = await request<Schema<'SessionOut'>>('/sessions/' + resumeId);
        if (cancelled) return;
        if (saved.profile_id !== profile.id) throw new Error('Choose the profile that owns this session.');
        if (saved.status === 'ended') { openReport(saved.id); return; }
        sessionRef.current = saved; setSession(saved); pending.current = readPending(saved.id);
        const rows = await request<Schema<'TurnOut'>[]>('/sessions/' + saved.id + '/turns');
        if (cancelled) return;
        setTurns(rows); replyId.current = rows.at(-1)?.turn_id ?? null;
      } catch (e) { if (!cancelled) setError(message(e)); }
      finally { if (!cancelled) setRestoring(false); }
    })();
    return () => { cancelled = true; };
  }, [resumeId, profile.id]); // openReport is only invoked for this loaded session.

  async function play(id: number, generation: number) {
    replyId.current = id;
    const blob = await speech(id);
    if (!active.current) return;
    await audio.playReply(blob, generation);
  }
  async function waitForTurn(sessionId: number, clientId: string, token: number) {
    for (let i = 0; i < 30; i++) {
      if (!active.current || action.current !== token) throw new Error('Session paused.');
      const result = await request<Schema<'TurnOut'>>('/sessions/' + sessionId + '/turns/by-client/' + encodeURIComponent(clientId));
      if (result.correction_status !== 'processing') return result;
      await new Promise(resolve => setTimeout(resolve, 1500));
    }
    throw new Error('This turn is still processing. Use Retry to check its status.');
  }
  async function sendPending(id: number, generation: number) {
    const item = pending.current;
    if (!item || networkBusy.current) return;
    const token = ++action.current;
    networkBusy.current = true; setBusy(true); setError(null);
    try {
      const form = new FormData();
      form.set('client_turn_id', item.client_turn_id);
      for (const [key, value] of Object.entries(item.timing)) form.set(key, String(value));
      if (item.audio) form.set('audio', item.audio, 'turn.wav');
      let result = await request<Schema<'TurnOut'>>('/sessions/' + id + '/turns', { method: 'POST', body: form });
      if (result.correction_status === 'processing') result = await waitForTurn(id, item.client_turn_id, token);
      if (!active.current || action.current !== token) return;
      await reload(id);
      if (result.correction_status !== 'done') throw new Error('This turn failed. Retry the saved recording.');
      await play(result.turn_id, generation);
      // Metadata is retained until the next segment so a reload can replay a lost reply.
    } catch (e) {
      if (active.current && action.current === token) { setError(message(e)); audio.fail(e); await reload(id).catch(() => {}); }
    } finally { if (active.current) setBusy(false); networkBusy.current = false; }
  }
  async function start() {
    if (busy) return;
    setBusy(true); setError(null);
    try {
      audio.stop();
      const generation = await audio.start({ opening: true });
      if (generation === undefined) return;
      const created = await post<Schema<'SessionStartOut'>>('/sessions', {
        profile_id: profile.id, target_language: language, level, scenario, explanation_mode: mode,
      } satisfies Schema<'SessionCreate'>);
      if (!active.current) return;
      sessionRef.current = created.session; setSession(created.session);
      localStorage.setItem('tutor.active.' + profile.id, String(created.session.id));
      await reload(created.session.id);
      await play(created.opening_turn_id, generation);
    } catch (e) { if (active.current) { setError(message(e)); audio.fail(e); } }
    finally { if (active.current) setBusy(false); }
  }
  async function retry() {
    if (busy) return;
    const current = sessionRef.current; if (!current) { audio.stop(); return; }
    setBusy(true); setError(null);
    try {
      audio.stop();
      const generation = await audio.start({ opening: true });
      if (generation === undefined) return;
      const item = pending.current;
      if (item) {
        let saved: Schema<'TurnOut'> | null = null;
        try { saved = await request<Schema<'TurnOut'>>('/sessions/' + current.id + '/turns/by-client/' + encodeURIComponent(item.client_turn_id)); }
        catch (e) { if (!(e instanceof ApiError && e.status === 404)) throw e; }
        if (saved?.correction_status === 'processing') saved = await waitForTurn(current.id, item.client_turn_id, action.current);
        if (saved?.correction_status === 'done') { await reload(); await play(saved.turn_id, generation); }
        else {
          if (!item.audio && saved?.correction_status !== 'analysis_failed')
            throw new Error('The recording is no longer in memory. Choose Continue with a new turn to record again.');
          await sendPending(current.id, generation);
        }
      } else if (replyId.current) {
        const rows = await reload();
        const last = rows?.at(-1);
        if (last && last.correction_status !== 'done')
          throw new Error('This unfinished turn has no saved recording on this browser. Continue with a new turn.');
        await play(replyId.current, generation);
      } else { audio.stop(); await audio.start(); }
    } catch (e) { if (active.current) { setError(message(e)); audio.fail(e); } }
    finally { if (active.current) setBusy(false); }
  }
  async function continueListening() {
    if (busy) return;
    audio.stop(); setError(null); pending.current = null;
    if (sessionRef.current) persistPending(sessionRef.current.id, null);
    await audio.start();
  }
  async function end() {
    const current = sessionRef.current; if (!current || busy) return;
    audio.stop(); setBusy(true); setError(null); action.current++;
    try {
      await post<Schema<'ReportOut'>>('/sessions/' + current.id + '/end');
      localStorage.removeItem('tutor.active.' + profile.id); persistPending(current.id, null);
      if (active.current) openReport(current.id);
    } catch (e) { if (active.current) setError(message(e)); }
    finally { if (active.current) setBusy(false); }
  }
  async function checkAudio() {
    setCheck(null); setError(null);
    let context: AudioContext | null = null;
    try {
      context = new AudioContext(); await context.resume();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(t => t.stop());
      const tone = context.createOscillator(), gain = context.createGain();
      gain.gain.value = 0.06; tone.frequency.value = 440; tone.connect(gain); gain.connect(context.destination);
      tone.start(); tone.stop(context.currentTime + 0.2);
      await new Promise<void>(resolve => { tone.onended = () => resolve(); });
      setCheck('Microphone permission granted. If you heard the tone, playback is ready too.');
    } catch (e) { setError(message(e)); }
    finally { if (context) await context.close(); }
  }
  return <><p className="eyebrow">A little practice, every day</p><h1>{session ? 'You have the floor.' : 'Make room for conversation.'}</h1>
    <ErrorNotice error={error || audio.error} />
    {restoring ? <p role="status">Restoring your session…</p> : !session ? <>
      <p className="intro">Practise speaking German or English. Get a gentle correction, keep talking, and find your next focus.</p>
      <section className="panel"><h2>Set the scene</h2><div className="form-grid">
        <LanguagePicker value={language} onChange={setLanguage} />
        <label>Your level<select value={level} onChange={e => setLevel(e.target.value as Schema<'SessionCreate'>['level'])}>{['A1', 'A2', 'B1', 'B2'].map(x => <option key={x}>{x}</option>)}</select></label>
        <label>Scenario<select value={scenario} onChange={e => setScenario(e.target.value as Schema<'SessionCreate'>['scenario'])}><option value="cafe">At a café</option><option value="job_interview">Job interview</option><option value="doctor">At the doctor</option><option value="free_talk">Free conversation</option></select></label>
        <label>Explanations<select value={mode} onChange={e => setMode(e.target.value as Schema<'SessionCreate'>['explanation_mode'])}><option value="native">My native language ({profile.native_language})</option><option value="target">The language I’m practising</option></select></label>
      </div><div className="row actions"><button className="primary" disabled={busy || audio.loading} onClick={() => void start()}>{busy ? 'Starting…' : audio.loading ? 'Preparing speech detector…' : 'Start conversation'}</button>
        <button disabled={busy} onClick={() => void checkAudio()}>Check microphone & sound</button></div>
        {check && <p role="status">{check}</p>}<p className="caption">Wait for the tutor, then speak naturally. A short pause sends your turn. Headphones help prevent echoes.</p>
        <p className="caption">Speech is processed by the configured providers. Only transcripts and learning feedback are kept by the app.</p>
      </section>
    </> : <>
      <div className="row session-heading"><p>{languages[session.target_language]} · {session.level} · {session.scenario.replaceAll('_', ' ')}</p><button disabled={busy} onClick={() => void end()}>{busy && audio.state === 'STOPPED' ? 'Preparing report…' : 'End session'}</button></div>
      <section className={'voice-status state-' + audio.state.toLowerCase()} aria-live="polite"><span className={'voice-dot ' + (audio.userSpeaking ? 'pulse' : '')} />
        <div><strong>{audio.state === 'LISTENING' ? audio.userSpeaking ? 'I’m listening…' : 'Your turn. Speak when you’re ready.' : audio.state === 'PROCESSING' ? 'Thinking about your turn…' : audio.state === 'SPEAKING' ? 'Listen to your tutor.' : audio.state === 'ERROR' ? 'Let’s try that again.' : 'Conversation paused.'}</strong>
          <p className="caption">{audio.state === 'LISTENING' ? 'A short pause sends your recording.' : 'The microphone is paused.'}</p></div></section>
      <div className="row actions">
        {(['STOPPED', 'ERROR'].includes(audio.state) || !!error) && <><button className="primary" disabled={busy || audio.loading} onClick={() => void retry()}>Retry / resume reply</button><button disabled={busy || audio.loading} onClick={() => void continueListening()}>Continue with a new turn</button></>}
        {audio.state === 'LISTENING' && <button onClick={audio.stop}>Pause microphone</button>}
      </div>
      <Transcript turns={turns} onChange={async () => { await reload(); }} />
    </>}
  </>;
}
