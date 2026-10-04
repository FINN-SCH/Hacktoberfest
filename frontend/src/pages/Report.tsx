import { useCallback, useEffect, useState } from 'react';
import { request, post, message, type Schema } from '../api/client';
import { ErrorNotice, Loading, Scores, date, languages } from '../components/Common';
import { Transcript } from '../components/Transcript';

export function Report({ id, onBack }: { id: number; onBack: () => void }) {
  const [report, setReport] = useState<Schema<'ReportOut'> | null>(null);
  const [error, setError] = useState<string | null>(null), [busy, setBusy] = useState(false);
  const load = useCallback(async () => { setReport(await request<Schema<'ReportOut'>>('/sessions/' + id + '/report')); }, [id]);
  useEffect(() => { void load().catch(e => setError(message(e))); }, [load]);
  async function regenerate() {
    setBusy(true); setError(null);
    try { setReport(await post<Schema<'ReportOut'>>('/sessions/' + id + '/report/regenerate')); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <>
    <button className="text-button" onClick={onBack}>← Back</button>
    <p className="eyebrow">Your conversation, reflected</p><h1>Session report</h1>
    <ErrorNotice error={error} />
    {!report ? <Loading /> : <>
      <p className="intro">{languages[report.session.target_language]} · {report.session.level} · {date(report.session.started_at)}
        {report.session.is_demo_data && <span className="badge">Demo data</span>}</p>
      <section className="panel"><Scores scores={report.scores} vocab={report.vocab_rating} /></section>
      <section className="panel">
        <div className="row"><h2>A focus for next time</h2><button disabled={busy || report.session.status !== 'ended'} onClick={() => void regenerate()}>{busy ? 'Generating…' : 'Regenerate'}</button></div>
        {report.stale_exclusions > 0 && <p className="notice">{report.stale_exclusions} exclusions since this summary was generated. Scores already reflect them; regenerate to refresh the written feedback.</p>}
        {report.snapshot_status === 'failed' && <p className="notice">Written feedback could not be generated. Your transcript and computed scores are saved.</p>}
        {report.summary && <><ul>{report.summary.weaknesses.map((x, i) => <li key={i}>{x}</li>)}</ul><p className="focus">{report.summary.next_focus}</p></>}
        {report.vocab_evidence.map((e, i) => <blockquote key={i}>“{e.quote}”<p>{e.explanation}</p><cite>Turn {report.transcript.find(t => t.turn_id === e.turn_id)?.seq ?? e.turn_id}</cite></blockquote>)}
        <p className="caption">Generated {date(report.snapshot_generated_at)}</p>
      </section>
      <h2>Conversation</h2><Transcript turns={report.transcript} onChange={load} />
    </>}
  </>;
}
