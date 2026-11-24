'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/session-api';
import AcademyNavigation from '@/components/AcademyNavigation';
import { count } from '@/lib/academy-display';
import AccountControls from '@/components/AccountControls';
import { watchSessionEnd, SIGN_IN_URL } from '@/lib/browser-session';
import './pathways.css';

type Unit = {
  position: number; year: number; module_id: number; title: string; summary: string;
  course_slug: string; module_position: number; lesson_count: number;
  readiness: 'authored_slice' | 'outline'; scope: string; shared: boolean; outcomes: string[];
  progress: {status: string; project_unlocked?: boolean; lessons_passed?: number; requirements?: {title: string; complete: boolean}[];
    final_project?: {title: string; pass_score: number; status: string} | null};
};
type Pathway = {slug: string; title: string; description: string; disclaimer: string; units: Unit[]};
const statusLabels: Record<string,string> = {
  locked: 'Locked', lessons: 'Lessons available', final_project: 'Final project ready', completed: 'Completed',
  coming_soon: 'Planned', awaiting_project: 'Project not yet published', admin_preview: 'Admin testing access',
};

export default function PathwaysPage() {
  const [paths, setPaths] = useState<Pathway[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [year, setYear] = useState('all');
  const [readyOnly, setReadyOnly] = useState(false);
  async function load() {
    setLoading(true); setError('');
    try { setPaths(await api<Pathway[]>('/pathways/')); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Pathways could not load.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  useEffect(() => watchSessionEnd(() => { setPaths([]); window.location.replace(SIGN_IN_URL); }), []);
  return <div className="pathway-page">
    <a className="pathway-skip" href="#pathway-content">Skip to pathways</a>
    <header><a href="/" className="pathway-brand">SAIRE<span> Academy</span></a><AcademyNavigation compact active="/pathways/" /><AccountControls /></header>
    <main id="pathway-content">
      <div className="pathway-intro"><span className="eyebrow">LEARN WITH A PURPOSE</span><h1>Choose your next<br/><span>useful skill.</span></h1><p>Explore AI Engineering and Computing &amp; IT. Shared modules keep the same lessons, project and saved progress across both pathways.</p><p className="pathway-motivation">Small, understood steps become skills you can trust.</p></div>
      {paths.length > 0 && <section className="pathway-availability" aria-label="Published curriculum">{paths.map(path => {
        const authored = path.units.filter(unit => unit.readiness === 'authored_slice').length;
        return <a key={path.slug} href={'#title-' + path.slug}><strong>{path.title}</strong>
          <span>{count(authored, 'module')} with lessons · {count(path.units.length - authored, 'outline')} only</span></a>;
      })}</section>}
      <aside className="pathway-policy" aria-label="How progression works"><strong>Your learning rules</strong><p>Setup labs are untimed. Starting a lesson starts its 14-day iteration. A missed lesson deadline fails the primary attempt; its one 7-day supplementary window ends 21 days after the original start, with the configured grade cap (70% by default).</p><p>Pass each lesson and the module’s reviewed final project before moving on. The new projects have their own 14-day deadlines. Outline units have no lessons to start. Sign in to see your personal access state.</p></aside>
      <form className="pathway-filters" onSubmit={event => event.preventDefault()} aria-label="Filter learning units">
        <label>Search units<input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Try data, Python or systems"/></label>
        <label>Study stage<select value={year} onChange={e => setYear(e.target.value)}><option value="all">All stages</option><option value="1">Foundation year</option><option value="2">Second year</option></select></label>
        <label className="pathway-check"><input type="checkbox" checked={readyOnly} onChange={e => setReadyOnly(e.target.checked)}/> Authored lessons only</label>
      </form>
      {loading && <p role="status">Loading pathways…</p>}
      {error && <div role="alert"><p>{error}</p><button type="button" onClick={() => void load()}>Try again</button></div>}
      {!loading && !error && !paths.length && <p>No pathways are published yet. Ask the Academy administrator to publish the curriculum.</p>}
      {paths.map(path => {
        const units = path.units.filter(unit => (year === 'all' || String(unit.year) === year)
          && (!readyOnly || unit.readiness === 'authored_slice')
          && `${unit.title} ${unit.summary} ${unit.outcomes.join(' ')}`.toLowerCase().includes(search.toLowerCase()));
        return <section key={path.slug} className="pathway-section" aria-labelledby={`title-${path.slug}`}>
          <div className="pathway-heading"><div><h2 id={`title-${path.slug}`}>{path.title}</h2><p>{path.description}</p></div><span>{path.units.filter(u => u.readiness === 'authored_slice').length} modules with lessons · {path.units.filter(u => u.readiness === 'outline').length} outlines</span></div>
          <p className="pathway-disclaimer">{path.disclaimer}</p>
          <p>Order below is a study recommendation. The required earlier modules and final projects are enforced by the Academy.</p>
          <div className="pathway-grid">{units.map(unit => <article key={unit.module_id} className={`pathway-unit ${unit.readiness}`}>
            <div className="pathway-unit-top"><span>YEAR {unit.year} · {String(unit.position).padStart(2,'0')}</span><span>{unit.readiness === 'outline' ? 'Outline only' : `${count(unit.lesson_count, 'authored lesson')}`}</span></div>
            <h3>{unit.title}</h3><p>{unit.summary}</p>
            {unit.shared && <p className="pathway-shared">Shared module · one set of progress</p>}
            <p className="pathway-scope">{unit.scope}</p>
            {unit.outcomes.length > 0 && <details><summary>What you will be able to do</summary><ul>{unit.outcomes.map(outcome => <li key={outcome}>{outcome}</li>)}</ul></details>}
            {unit.readiness !== 'outline' && <div className="pathway-state"><strong>{statusLabels[unit.progress.status] ?? unit.progress.status}</strong><span>{unit.progress.lessons_passed ?? 0}/{unit.lesson_count} lessons passed</span>
              {unit.progress.final_project && <p>Final project: {unit.progress.final_project.title} · pass {unit.progress.final_project.pass_score}% · {unit.progress.final_project.status === 'passed' ? 'passed' : !unit.progress.project_unlocked && unit.progress.status !== 'admin_preview' ? 'locked' : unit.progress.final_project.status.replaceAll('_',' ')}</p>}
              {unit.progress.requirements?.some(r => !r.complete) && <p>Required first: {unit.progress.requirements.filter(r => !r.complete).map(r => r.title).join(', ')}, including the final project.</p>}
            </div>}
            <a className="pathway-open" href={`/dashboard/?course=${encodeURIComponent(unit.course_slug)}&view=roadmap`}>{unit.readiness === 'outline' ? 'View course outline' : 'Open course roadmap'} <span aria-hidden="true">→</span></a>
          </article>)}</div>
          {!units.length && <p role="status">No units match these filters.</p>}
        </section>;
      })}
    </main><footer>Understand one step. Build one thing. Explain it clearly.</footer>
  </div>;
}
