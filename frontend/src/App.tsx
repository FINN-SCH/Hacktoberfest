import { useState } from 'react';

const tabs = ['Talk', 'History', 'Quiz', 'Analysis'] as const;
export default function App() {
  const [tab, setTab] = useState<typeof tabs[number]>('Talk');
  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="wordmark" href="/">Language Tutor</a>
        <span className="language-label">Deutsch / English</span>
      </header>
      <nav aria-label="Main navigation">
        {tabs.map(item => <button key={item} type="button" aria-current={tab === item ? 'page' : undefined}
          onClick={() => setTab(item)}>{item}</button>)}
      </nav>
      <main id="main-content">
        <p className="eyebrow">A little practice, every day</p>
        <h1>{tab === 'Talk' ? 'Make room for conversation.' : tab}</h1>
        <p className="intro">{tab === 'Talk'
          ? 'Practise speaking German or English, then reflect on what you learned.'
          : 'Your ' + tab.toLowerCase() + ' will appear here.'}</p>
        <section className="placeholder" aria-label={tab + ' preview'}>
          <h2>{tab === 'Talk' ? 'Your next conversation starts here' : tab + ' overview'}</h2>
          <p>Session setup and learning features are being connected.</p>
        </section>
      </main>
      <footer>One conversation at a time.</footer>
    </div>
  );
}
