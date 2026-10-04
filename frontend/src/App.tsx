import { lazy, Suspense, useEffect, useState } from 'react';
import { post, request, message, type Schema } from './api/client';
import { ErrorNotice } from './components/Common';
const Talk = lazy(() => import('./pages/Talk').then(m => ({ default: m.Talk })));
const History = lazy(() => import('./pages/History').then(m => ({ default: m.History })));
const Quiz = lazy(() => import('./pages/Quiz').then(m => ({ default: m.Quiz })));
const Analysis = lazy(() => import('./pages/Analysis').then(m => ({ default: m.Analysis })));
const Report = lazy(() => import('./pages/Report').then(m => ({ default: m.Report })));
const tabs = ['Talk', 'History', 'Quiz', 'Analysis'] as const;
type Tab = typeof tabs[number];
export default function App() {
  const [tab, setTab] = useState<Tab>('Talk'), [profiles, setProfiles] = useState<Schema<'ProfileOut'>[]>([]);
  const [profileId, setProfileId] = useState<number | null>(null), [loaded, setLoaded] = useState(false);
  const [creating, setCreating] = useState(false), [name, setName] = useState(''), [native, setNative] = useState('en');
  const [mode, setMode] = useState<Schema<'SessionCreate'>['explanation_mode']>('native'), [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null), [reportId, setReportId] = useState<number | null>(null);
  const [resumeId, setResumeId] = useState<number | null>(null);
  const profile = profiles.find(p => p.id === profileId);
  function choose(id: number | null) {
    setProfileId(id); setReportId(null); setCreating(false);
    if (id != null) { localStorage.setItem('tutor.profile', String(id)); const active = Number(localStorage.getItem('tutor.active.' + id)); setResumeId(active || null); }
  }
  useEffect(() => { let active = true; void request<Schema<'ProfileOut'>[]>('/profiles').then(rows => {
    if (!active) return;
    setProfiles(rows); const saved = Number(localStorage.getItem('tutor.profile'));
    choose(rows.find(p => p.id === saved)?.id ?? rows[0]?.id ?? null);
  }).catch(e => { if (active) setError(message(e)); }).finally(() => { if (active) setLoaded(true); }); return () => { active = false; }; }, []);
  async function create() {
    setBusy(true); setError(null);
    try {
      const created = await post<Schema<'ProfileOut'>>('/profiles', { name: name.trim(), native_language: native, default_explanation_mode: mode } satisfies Schema<'ProfileCreate'>);
      setProfiles(p => [...p, created]); choose(created.id); setName('');
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  function openReport(id: number) { setReportId(id); }
  return <div className="app-shell"><a className="skip-link" href="#main-content">Skip to content</a>
    <header className="app-header"><a className="wordmark" href="/">Language Tutor</a><span className="language-label">Deutsch / English</span></header>
    <div className="navigation-row"><nav aria-label="Main navigation">{tabs.map(item => <button key={item} aria-current={tab === item && !reportId ? 'page' : undefined} onClick={() => {
      setTab(item); setReportId(null); if (item === 'Talk' && profileId) setResumeId(Number(localStorage.getItem('tutor.active.' + profileId)) || null);
    }}>{item}</button>)}</nav>
      {!!profiles.length && <div className="profile-tools"><label><span className="sr-only">Current profile</span><select aria-label="Current profile" value={profileId ?? ''} onChange={e => choose(Number(e.target.value))}>{profiles.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><button className="text-button" onClick={() => setCreating(x => !x)}>New profile</button></div>}
    </div>
    <main id="main-content"><ErrorNotice error={error} />
      {!loaded ? <p>Loading profiles…</p> : (!profiles.length || creating) ? <>
        <p className="eyebrow">A space for your voice</p><h1>Let’s get acquainted.</h1><p className="intro">Choose a name and the language you’d like explanations in. Profiles are saved on this computer’s tutor server.</p>
        <form className="panel profile-form" onSubmit={e => { e.preventDefault(); void create(); }}><div className="form-grid">
          <label>Your name<input required maxLength={60} value={name} onChange={e => setName(e.target.value)} placeholder="Name" /></label>
          <label>Native language<select value={native} onChange={e => setNative(e.target.value)}>{Object.entries({ en: 'English', de: 'German', ar: 'Arabic', es: 'Spanish', fr: 'French', tr: 'Turkish', it: 'Italian', pt: 'Portuguese', ru: 'Russian', zh: 'Chinese' }).map(([v, label]) => <option key={v} value={v}>{label}</option>)}</select></label>
          <label>Default explanations<select value={mode} onChange={e => setMode(e.target.value as Schema<'SessionCreate'>['explanation_mode'])}><option value="native">My native language</option><option value="target">The language I’m practising</option></select></label>
        </div><button className="primary" disabled={busy || !name.trim()}>{busy ? 'Saving…' : 'Create profile'}</button>{!!profiles.length && <button type="button" onClick={() => setCreating(false)}>Cancel</button>}</form>
      </> : profile && <Suspense fallback={<p role="status">Loading...</p>}><div key={profile.id}>
        {reportId ? <Report key={reportId} id={reportId} onBack={() => { setReportId(null); setTab('History'); }} /> :
          tab === 'Talk' ? <Talk key={resumeId ?? 'new'} profile={profile} resumeId={resumeId} openReport={openReport} /> :
          tab === 'History' ? <History profile={profile} openReport={openReport} resume={id => { setResumeId(id); setTab('Talk'); }} /> :
          tab === 'Quiz' ? <Quiz profile={profile} /> : <Analysis profile={profile} openReport={openReport} />}
      </div></Suspense>}
    </main><footer>One conversation at a time. <span>Deutsch / English</span></footer>
  </div>;
}
