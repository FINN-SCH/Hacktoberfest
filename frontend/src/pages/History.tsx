import { useEffect, useState } from 'react';
import { request, message, type Schema } from '../api/client';
import { ErrorNotice, Loading, date, languages } from '../components/Common';
export function History({ profile, openReport, resume }: { profile: Schema<'ProfileOut'>; openReport: (id: number) => void; resume: (id: number) => void }) {
  const [rows, setRows] = useState<Schema<'SessionHistoryOut'>[] | null>(null), [error, setError] = useState<string | null>(null);
  useEffect(() => { let active = true; void request<Schema<'SessionHistoryOut'>[]>('/profiles/' + profile.id + '/sessions')
    .then(x => { if (active) setRows(x); }).catch(e => { if (active) setError(message(e)); }); return () => { active = false; }; }, [profile.id]);
  return <><p className="eyebrow">A record of your practice</p><h1>Every conversation counts.</h1><ErrorNotice error={error} />
    {!rows ? <Loading /> : !rows.length ? <div className="panel empty"><h2>Your first session belongs here.</h2><p>Start a conversation in Talk to build your history.</p></div> :
      <div className="history-list">{rows.map(s => <article className="panel" key={s.id}>
        <div className="row"><h2>{languages[s.target_language]} · {s.level} · {s.scenario.replaceAll('_', ' ')}</h2>{s.is_demo_data && <span className="badge">Demo data</span>}</div>
        <p className="caption">{date(s.started_at)} · {s.status}</p>
        <div className="row"><p>Grammar {s.scores.grammar.rating ?? '—'} / 5 · Fluency {s.scores.fluency.rating ?? '—'} / 5 · Vocabulary {s.scores.sufficient_sample ? s.vocab_rating ?? '—' : '—'} / 5</p>
          <button onClick={() => s.status === 'ended' ? openReport(s.id) : resume(s.id)}>{s.status === 'ended' ? 'View report' : 'Resume session'}</button></div>
        {!s.scores.sufficient_sample && <p className="caption">Not enough speech yet for ratings.</p>}
        {s.stale_exclusions > 0 && <p className="caption">Written feedback has {s.stale_exclusions} newer exclusions.</p>}
      </article>)}</div>}</>;
}
