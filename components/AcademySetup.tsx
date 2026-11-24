'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/session-api';
import { ResourceLinks, type Resource } from './LessonStudyTools';

export type SetupModule = {id: number; name: string; module_id?: number};
type Setup = {
  title: string; introduction: string; outcomes: string[];
  revision: number | null; required: boolean; completed: boolean;
  steps: {id: number; heading: string; instructions: string; command: string; verification: string}[];
  template: string[]; resources: Resource[];
  final_project: {title: string; duration_days: number; module_pass_score: number} | null;
};

export default function AcademySetup({ modules, phase, refresh }: {
  modules: SetupModule[]; phase?: number; refresh: () => Promise<void>;
}) {
  const available = modules.filter(module => module.module_id !== undefined);
  const [id, setId] = useState(available.find(module => module.id === phase)?.module_id ?? available[0]?.module_id);
  const [setup, setSetup] = useState<Setup | null>(null);
  const [checked, setChecked] = useState<number[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (id === undefined) return;
    let active = true;
    setSetup(null);
    setChecked([]);
    setError('');
    api<Setup>(`/academy/modules/${id}/setup/`).then(
      data => { if (active) setSetup(data); },
      cause => { if (active) setError(cause.message); },
    );
    return () => { active = false; };
  }, [id]);

  async function complete() {
    if (!setup || checked.length !== setup.steps.length || busy) return;
    setBusy(true);
    setError('');
    try {
      setSetup(await api<Setup>(`/academy/modules/${id}/setup/`, { revision: setup.revision, checked }));
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not save your setup checklist.');
    } finally {
      setBusy(false);
    }
  }

  return <>
    <h2>Getting Ready</h2>
    <p>Install and check the tools before starting graded work. Your lesson timer starts separately.</p>
    {id !== undefined && <label className="study-label">Choose a module
      <select value={id} disabled={busy} onChange={event => setId(Number(event.target.value))}>
        {available.map(module => <option key={module.module_id} value={module.module_id}>{module.name}</option>)}
      </select>
    </label>}
    {error && <p role="alert">{error}</p>}
    {!setup && !error && <p role="status">{id === undefined ? 'Choose a course with a published module.' : 'Loading the setup lab…'}</p>}
    {setup && <>
      <section className="study-panel">
        <h3>{setup.title}</h3><p>{setup.introduction}</p>
        <h4>What you’ll be able to do</h4>
        {setup.outcomes.length ? <ul>{setup.outcomes.map(outcome => <li key={outcome}>{outcome}</li>)}</ul>
          : <p>The author can add outcomes in Django Admin.</p>}
        {setup.final_project && <p>Final project: {setup.final_project.title} · {setup.final_project.module_pass_score}% to pass · {setup.final_project.duration_days} days from project start.</p>}
      </section>
      <ResourceLinks links={setup.resources} />
      {setup.template.length > 0 && <section className="study-panel">
        <h3>Setup checklist template</h3><p>Use this plan until a module-specific lab is published.</p>
        <ol>{setup.template.map(item => <li key={item}>{item}</li>)}</ol>
      </section>}
      {setup.steps.length > 0 && <form onSubmit={event => { event.preventDefault(); void complete(); }}>
        {setup.steps.map((step, index) => <section className="study-panel" key={step.id}>
          <h3>{index + 1}. {step.heading}</h3><p>{step.instructions}</p>
          {step.command && <pre><code>{step.command}</code></pre>}
          <label className="study-choice">
            <input type="checkbox" checked={setup.completed || checked.includes(step.id)} disabled={setup.completed || busy}
              onChange={event => {
                const value = event.target.checked;
                setChecked(current => value ? [...current, step.id] : current.filter(item => item !== step.id));
              }} />
            {step.verification}
          </label>
        </section>)}
        {setup.completed ? <p role="status">Setup checklist complete. Open My classroom when you are ready.</p>
          : <button className="btn btn-primary" disabled={busy || checked.length !== setup.steps.length}>
            {busy ? 'Saving…' : 'Confirm my setup'}
          </button>}
      </form>}
    </>}
  </>;
}
