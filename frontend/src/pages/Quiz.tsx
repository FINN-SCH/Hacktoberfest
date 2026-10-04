import { useState } from 'react';
import { post, message, type Schema } from '../api/client';
import { LanguagePicker, ErrorNotice } from '../components/Common';

export function Quiz({ profile }: { profile: Schema<'ProfileOut'> }) {
  const [language, setLanguage] = useState<Schema<'SessionCreate'>['target_language']>('de');
  const [quiz, setQuiz] = useState<Schema<'QuizOut'> | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<Schema<'QuizAttemptOut'> | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState<string | null>(null);
  async function create() {
    setBusy(true); setError(null); setQuiz(null); setResult(null); setAnswers({});
    try { setQuiz(await post<Schema<'QuizOut'>>('/quizzes', { profile_id: profile.id, language } satisfies Schema<'QuizCreate'>)); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function grade() {
    if (!quiz) return;
    setBusy(true); setError(null);
    try { setResult(await post<Schema<'QuizAttemptOut'>>('/quizzes/' + quiz.id + '/attempts', { answers } satisfies Schema<'QuizAnswers'>)); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <><p className="eyebrow">Small corrections, lasting progress</p><h1>Make it stick.</h1>
    <p className="intro">A short quiz built from your own conversations.</p>
    <div className="row controls"><LanguagePicker value={language} onChange={v => { setLanguage(v); setQuiz(null); setResult(null); }} /><button className="primary" disabled={busy} onClick={() => void create()}>{busy ? 'Working…' : quiz ? 'Create another quiz' : 'Create my quiz'}</button></div>
    <ErrorNotice error={error} />
    {quiz && <form onSubmit={e => { e.preventDefault(); void grade(); }}>
      {quiz.questions.map((q, i) => {
        const outcome = result?.results.find(r => r.id === q.id);
        return <fieldset className="panel question" key={q.id} disabled={busy || !!result}>
          <legend>{i + 1}. {q.question}</legend>
          {q.kind === 'mc' ? q.options.map(o => <label className="option" key={o.id}><input type="radio" name={q.id} value={o.id} checked={answers[q.id] === o.id} onChange={() => setAnswers(a => ({ ...a, [q.id]: o.id }))} />{o.text}</label>) :
            <label>Your answer<input autoComplete="off" value={answers[q.id] ?? ''} onChange={e => setAnswers(a => ({ ...a, [q.id]: e.target.value }))} /></label>}
          {outcome && <div className="quiz-result"><strong>{outcome.status === 'correct' ? 'Correct' : outcome.status === 'wrong' ? 'Keep practising' : 'Skipped — source excluded'}</strong>
            {outcome.status !== 'skipped_source_excluded' && <><p>Answer: {outcome.correct_answer}</p><p>{outcome.explanation}</p>
              <p className="caption">Practising this because you said: “{outcome.source_original}” → “{outcome.source_corrected}”.</p></>}
          </div>}
        </fieldset>;
      })}
      {!result && <button className="primary" disabled={busy} type="submit">Check answers</button>}
      {result && <p className="focus" role="status">{result.correct} of {result.total} correct. Excluded sources do not count toward your score.</p>}
    </form>}
  </>;
}
