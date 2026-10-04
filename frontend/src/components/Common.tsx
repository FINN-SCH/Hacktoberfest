import type { Schema } from '../api/client';

export const languages = { de: 'German', en: 'English' } as const;
export function LanguagePicker({ value, onChange }: { value: Schema<'SessionCreate'>['target_language']; onChange: (v: Schema<'SessionCreate'>['target_language']) => void }) {
  return <label>Practice language<select value={value} onChange={e => onChange(e.target.value as Schema<'SessionCreate'>['target_language'])}>
    <option value="de">German</option><option value="en">English</option>
  </select></label>;
}
export function ErrorNotice({ error }: { error: string | null }) {
  return error ? <div className="notice error" role="alert">{error}</div> : null;
}
export function Loading() { return <p className="muted" role="status">Loading your practice…</p>; }
export function date(value: string | null | undefined) {
  return value ? new Date(value.endsWith('Z') || /[+-]\d\d:\d\d$/.test(value) ? value : value + 'Z').toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—';
}
export function number(value: number | null | undefined, suffix = '') { return value == null ? '—' : value.toFixed(1) + suffix; }
export function Scores({ scores, vocab }: { scores: Schema<'SessionScores'>; vocab: number | null }) {
  return <>
    {!scores.sufficient_sample && <p className="notice">Not enough speech yet. Ratings need at least 5 eligible turns and 60 seconds of voiced speech.</p>}
    <div className="ratings">{[['Grammar', scores.grammar.rating], ['Fluency', scores.fluency.rating], ['Vocabulary', scores.sufficient_sample ? vocab : null]].map(([label, rating]) =>
      <div key={label}><span>{label}</span><strong>{rating ?? '—'}<small>{rating != null ? ' / 5' : ''}</small></strong></div>)}</div>
    <dl className="metrics">
      <div><dt>Error-free turns</dt><dd>{number(scores.grammar.error_free_turn_pct, '%')}</dd></div>
      <div><dt>Errors / 100 words</dt><dd>{number(scores.grammar.errors_per_100_words)}</dd></div>
      <div><dt>Words / minute</dt><dd>{number(scores.fluency.wpm)}</dd></div>
      <div><dt>Pause ratio</dt><dd>{number(scores.fluency.pause_ratio == null ? null : scores.fluency.pause_ratio * 100, '%')}</dd></div>
    </dl>
    <p className="caption">{scores.assessed_turns} of {scores.learner_turns} turns assessed · {scores.eligible_turns} eligible · {Math.round(scores.eligible_voiced_ms / 1000)}s voiced speech</p>
    <p className="caption">Fluency is a timing heuristic ({scores.fluency.heuristic_version}), not a pronunciation assessment.</p>
  </>;
}
