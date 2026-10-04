import { useState } from 'react';
import { post, message, type Schema } from '../api/client';
import { highlightParts } from './highlights';
import { ErrorNotice } from './Common';

export function Transcript({ turns, onChange }: { turns: Schema<'TurnOut'>[]; onChange: () => Promise<void> }) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  async function exclude(path: string, id: number) {
    setBusy(id); setError(null);
    try { await post(path); await onChange(); } catch (e) { setError(message(e)); } finally { setBusy(null); }
  }
  return <section className="transcript" aria-label="Conversation transcript">
    <ErrorNotice error={error} />
    {turns.map(turn => <article className={'turn ' + (turn.misheard ? 'excluded' : '')} key={turn.turn_id}>
      {turn.kind === 'learner' && <div className="learner-bubble">
        <div className="row"><span className="eyebrow">Heard as</span>{turn.misheard ? <span className="badge">Misheard · excluded</span> :
          turn.transcript != null && <button className="text-button" disabled={busy != null} onClick={() => void exclude('/turns/' + turn.turn_id + '/misheard', turn.turn_id)}>Misheard</button>}</div>
        <p>{turn.transcript ? highlightParts(turn.transcript, turn.misheard ? [] : turn.corrections).map((part, i) =>
          part.highlighted ? <mark key={i}>{part.text}</mark> : <span key={i}>{part.text}</span>) : 'No transcript yet.'}</p>
        {turn.correction_status !== 'done' && <p className="caption">{turn.correction_status.replaceAll('_', ' ')}</p>}
        {turn.needs_clarification && <p className="notice">Please repeat. This turn is excluded from learning evidence.</p>}
      </div>}
      {!turn.misheard && turn.corrections.length > 0 && <details className="corrections" open>
        <summary>{turn.corrections.length} correction{turn.corrections.length === 1 ? '' : 's'} · hide or show</summary>
        {turn.corrections.map(c => <section className={'correction ' + (c.status === 'excluded' ? 'excluded' : '')} key={c.id}>
          <div className="row"><span className="badge">{c.kind === 'improvement' ? 'Suggestion · ' : ''}{c.topic_label}</span>
            {c.status === 'active' ? <button className="text-button" disabled={busy != null} onClick={() => void exclude('/mistakes/' + c.id + '/not-a-mistake', c.id)}>Not a mistake</button> : <span className="caption">Excluded</span>}</div>
          <p className="correction-pair"><del>{c.original}</del><span aria-hidden="true"> → </span><strong>{c.corrected}</strong></p>
          <p>{c.explanation}</p>
        </section>)}
      </details>}
      {turn.reply && <div className="tutor-bubble"><span className="eyebrow">Tutor</span><p>{turn.reply}</p></div>}
    </article>)}
  </section>;
}
