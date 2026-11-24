'use client';

import { useEffect, useState } from 'react';
import { count } from '@/lib/academy-display';
import { api } from '@/lib/session-api';
import AcademyHandbook, { type Orientation } from './AcademyHandbook';
import AcademySetup, { type SetupModule } from './AcademySetup';
import MistakesNotebook from './MistakesNotebook';
import '@/app/academy-study.css';

export type HubSection = 'welcome' | 'handbook' | 'setup' | 'glossary' | 'notebook' | 'revision';
const tabs: [HubSection, string][] = [
  ['welcome', 'Welcome tour'], ['handbook', 'Handbook'], ['setup', 'Getting Ready'],
  ['glossary', 'Glossary'], ['notebook', 'Mistakes notebook'], ['revision', 'Revision and milestones'],
];
const tour = [
  ['Get oriented', 'Read the Handbook and acknowledge the rules. You can replay this tour whenever you like.'],
  ['Check your tools', 'Getting Ready explains what to install and how to check that it works. You can complete setup before any timed work.'],
  ['Open My classroom', 'Choose the next unlocked lesson. Try the before check, then start the timed lesson when ready. Read, practise and finish the graded check.'],
  ['Build and explain', 'Use Project lab to submit a commit and prepare a Code Defence. The instructor review decides whether the next module opens.'],
  ['Review and ask for help', 'Use the notebook and revision suggestions. The Handbook explains support and accessibility options.'],
];

function WelcomeTour({ select }: {select: (section: HubSection) => void}) {
  const [step, setStep] = useState<number | null>(0);
  return <section className="study-panel">
    <h2>Welcome to SAIRE Academy</h2>
    {step === null ? <p>The tour is available here whenever you want a refresher.</p> :
      <div aria-live="polite">
        <p>Step {step + 1} of {tour.length}</p><h3>{tour[step][0]}</h3><p>{tour[step][1]}</p>
      </div>}
    <div className="study-actions">
      {step === null ? <button className="btn btn-outline" onClick={() => setStep(0)}>Replay tour</button> : <>
        <button className="btn btn-outline" disabled={step === 0} onClick={() => setStep(step - 1)}>Back</button>
        <button className="btn btn-outline" onClick={() => setStep(step + 1 < tour.length ? step + 1 : null)}>
          {step + 1 < tour.length ? 'Next tour step' : 'Finish tour'}
        </button>
        <button className="btn btn-outline" onClick={() => setStep(null)}>Skip tour</button>
      </>}
      <button className="btn btn-primary" onClick={() => select('handbook')}>Read the Handbook</button>
    </div>
  </section>;
}

type StudyTools = {
  glossary: {term: string; definition: string; example: string}[];
  revision: {lesson: string; reason: string}[];
  achievements: {title: string; evidence: string}[];
};

function StudyEvidence({ glossary }: {glossary: boolean}) {
  const [data, setData] = useState<StudyTools | null>(null);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    api<StudyTools>('/academy/study-tools/').then(
      value => { if (active) setData(value); },
      cause => { if (active) setError(cause.message); },
    );
    return () => { active = false; };
  }, []);
  if (!data) return <p role={error ? 'alert' : 'status'}>{error || 'Loading study tools…'}</p>;
  if (glossary) {
    const terms = data.glossary.filter(entry => [entry.term, entry.definition, entry.example].join(' ').toLowerCase().includes(query.trim().toLowerCase()));
    return <>
      <h2>Glossary</h2>
      <label className="study-label">Search terms<input type="search" value={query} onChange={event => setQuery(event.target.value)} /></label>
      <p role="status">{count(terms.length, 'term')}</p>
      <dl>{terms.map(entry => <div className="study-panel" key={entry.term}>
        <dt><strong>{entry.term}</strong></dt><dd>{entry.definition}{entry.example && <p>{entry.example}</p>}</dd>
      </div>)}</dl>
    </>;
  }
  return <>
    <h2>Revision and milestones</h2>
    <section className="study-panel"><h3>What to revisit</h3>
      {data.revision.length ? <ul>{data.revision.map(item => <li key={item.lesson}><strong>{item.lesson}</strong> · {item.reason}</li>)}</ul>
        : <p>Complete a practice check or lesson to build evidence for suggestions.</p>}
    </section>
    <section className="study-panel"><h3>Your milestones</h3>
      {data.achievements.length ? <ul>{data.achievements.map(item => <li key={item.title}><strong>{item.title}</strong> · {item.evidence}</li>)}</ul>
        : <p>Confirm your first program in Getting Ready or complete a challenge review to earn a milestone.</p>}
    </section>
    <p>Try recalling one idea before reopening your notes. A small recall attempt shows you where to practise next.</p>
  </>;
}

export default function AcademyHub({ section, select, modules, phase, orientation, refresh }: {
  section: HubSection; select: (section: HubSection) => void; modules: SetupModule[];
  phase?: number; orientation: Orientation; refresh: () => Promise<void>;
}) {
  return <section className="academy-study page-content">
    <h1>Study Hub</h1>
    <nav className="study-actions" aria-label="Study Hub">
      {tabs.map(([id, label]) => <button key={id} className={`btn ${section === id ? 'btn-primary' : 'btn-outline'}`}
        aria-pressed={section === id} onClick={() => select(id)}>{label}</button>)}
    </nav>
    {section === 'welcome' && <WelcomeTour select={select} />}
    {section === 'handbook' && <AcademyHandbook orientation={orientation} refresh={refresh} />}
    {section === 'setup' && <AcademySetup key={phase ?? 0} modules={modules} phase={phase} refresh={refresh} />}
    {section === 'notebook' && <MistakesNotebook />}
    {(section === 'glossary' || section === 'revision') && <StudyEvidence glossary={section === 'glossary'} />}
  </section>;
}
