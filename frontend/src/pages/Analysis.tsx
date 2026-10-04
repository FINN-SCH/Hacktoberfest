import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { request, message, type Schema } from '../api/client';
import { LanguagePicker, ErrorNotice, Loading, date, number } from '../components/Common';
export function Analysis({ profile, openReport }: { profile: Schema<'ProfileOut'>; openReport: (id: number) => void }) {
  const [language, setLanguage] = useState<Schema<'SessionCreate'>['target_language']>('de'), [data, setData] = useState<Schema<'AnalysisOut'> | null>(null);
  const [error, setError] = useState<string | null>(null), [revision, setRevision] = useState(0);
  useEffect(() => { let active = true; setData(null); setError(null);
    void request<Schema<'AnalysisOut'>>('/profiles/' + profile.id + '/analysis?language=' + language).then(x => { if (active) setData(x); }).catch(e => { if (active) setError(message(e)); });
    return () => { active = false; };
  }, [profile.id, language, revision]);
  const chart = data?.progress.map((s, i) => ({ name: String(i + 1), errorFree: s.scores.grammar.error_free_turn_pct, errors: s.scores.grammar.errors_per_100_words })) ?? [];
  return <><p className="eyebrow">See the pattern, choose a focus</p><h1>Your learning, over time.</h1>
    <div className="row controls"><LanguagePicker value={language} onChange={setLanguage} /><button onClick={() => setRevision(x => x + 1)}>Refresh</button></div>
    <ErrorNotice error={error} />{!data ? <Loading /> : <>
      <section className="panel"><h2>Topics to watch</h2>{!data.topic_frequency.length ? <p>No eligible errors in ended sessions yet.</p> :
        <div className="table-scroll"><table><thead><tr><th>Topic</th><th>Errors</th><th>Share</th><th>Sessions</th><th>Last seen</th></tr></thead><tbody>{data.topic_frequency.map(t =>
          <tr key={t.topic}><td>{t.label}</td><td>{t.errors}</td><td>{number(t.share * 100, '%')}</td><td>{t.sessions}</td><td>{date(t.last_seen)}</td></tr>)}</tbody></table></div>}</section>
      <section className="panel"><h2>Progress across {data.session_count} sessions</h2><p className="caption">Left axis: error-free turns (%). Right axis: errors per 100 words. Missing values mean no eligible speech.</p>
        {!!chart.length && <div className="chart" aria-label="Error-free percentage and errors per hundred words over sessions"><ResponsiveContainer width="100%" height={280}>
          <LineChart data={chart} margin={{ top: 15, right: 5, bottom: 5, left: -20 }}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis yAxisId="percent" domain={[0, 100]} /><YAxis yAxisId="errors" orientation="right" /><Tooltip /><Legend />
            <Line yAxisId="percent" type="linear" dataKey="errorFree" name="Error-free %" stroke="#246b58" strokeWidth={2} connectNulls={false} />
            <Line yAxisId="errors" type="linear" dataKey="errors" name="Errors / 100 words" stroke="#a66032" strokeWidth={2} connectNulls={false} />
          </LineChart></ResponsiveContainer></div>}
        <div className="table-scroll"><table><thead><tr><th>Session</th><th>Grammar</th><th>Fluency</th><th>Vocabulary</th><th>Error-free</th><th>Errors / 100</th></tr></thead><tbody>{data.progress.map((s, i) =>
          <tr key={s.id}><td><button className="text-button" onClick={() => openReport(s.id)}>{i + 1} · {date(s.started_at)}</button>{s.is_demo_data && <span className="badge">Demo</span>}</td>
            <td>{s.scores.grammar.rating ?? '—'}</td><td>{s.scores.fluency.rating ?? '—'}</td><td>{s.scores.sufficient_sample ? s.vocab_rating ?? '—' : '—'}{s.stale_exclusions > 0 ? ' *' : ''}</td><td>{number(s.scores.grammar.error_free_turn_pct, '%')}</td><td>{number(s.scores.grammar.errors_per_100_words)}</td></tr>)}</tbody></table></div>
        <p className="caption">Ratings are out of 5. — means insufficient sample or unavailable feedback. * Written feedback predates an exclusion.</p>
      </section>
      <div className="two-columns"><section className="panel"><h2>Recurring topics</h2>{!data.recurring.length && <p>No topic has appeared in two sessions yet.</p>}{data.recurring.map(t =>
        <div key={t.topic}><h3>{t.label}</h3><p className="caption">{t.errors} errors across {t.sessions} sessions</p>{t.examples.map((e, i) => <p key={i}>“{e.original}” → “{e.corrected}” <span className="caption">({e.count}×)</span></p>)}</div>)}</section>
        <section className="panel"><h2>Signs of improvement</h2>{!data.improving.length ? <p>No earlier topics have cleared the last two qualifying sessions yet.</p> : <ul>{data.improving.map(t => <li key={t.topic}>{t.label}</li>)}</ul>}
          <p className="caption">Absent from the last two sessions, each with at least five eligible turns.</p></section></div>
      <section className="panel"><h2>Your next focus</h2>{data.session_count < 2 ? <p>Complete 2 sessions to unlock your written analysis.</p> : <>
        {data.latest_attempt_failed && <p className="notice">The latest written analysis failed. Any previous analysis is shown below; current statistics remain available.</p>}
        {!data.written && !data.latest_attempt_failed && <p>Analysis is being prepared. Refresh shortly.</p>}
        {data.written && <><p className="caption">Based on {data.based_on_sessions} sessions · Generated {date(data.generated_at)}</p>
          {data.stale_exclusions > 0 && <p className="notice">{data.stale_exclusions} exclusions since this analysis. The tables already reflect them.</p>}
          <p>{data.written.summary}</p><h3>Strengths</h3>{data.written.strengths.map((s, i) => <p key={i}><strong>{s.text}</strong><br />{s.evidence}</p>)}
          {data.written.focus_areas.map((f, i) => <div className="focus-area" key={i}><h3>{data.topic_frequency.find(t => t.topic === f.topic)?.label ?? f.topic}</h3><p>{f.why}</p><p className="focus">{f.tip}</p></div>)}</>}
      </>}</section>
    </>}
  </>;
}
