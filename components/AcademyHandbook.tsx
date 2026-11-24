'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/session-api';

export type Orientation = {version: string; acknowledged: boolean};
type Policy = {
  orientation: Orientation;
  lesson_days: number;
  supplementary_days: number;
  grade_cap: number;
  mentor_hourly: string;
  mentor_daily: string;
  support_email: string;
};

function handbookEntries(policy: Policy) {
  return [
    {title: 'Getting Ready and lesson deadlines',
      text: `Read and acknowledge the rules before starting new graded work. Finish your module’s required setup checklist. Setup, the tour and practice checks use no timed attempt. Starting a lesson gives you ${policy.lesson_days} days. Django uses its own clock. Reopening a lesson keeps the same deadline.`},
    {title: 'Missed deadline and supplementary attempt',
      text: `The first attempt fails when its deadline passes without a pass. You can begin one supplementary attempt until ${policy.supplementary_days} days after the original deadline. Starting it later leaves less time. Credited marks are capped at ${policy.grade_cap}% under the current configuration. The lesson uses the raw result to determine a pass. Existing attempts keep their saved cap.`},
    {title: 'Module progression and project grading',
      text: 'Pass the lessons in order and then pass the module’s final project. Getting Ready and the roadmap show the configured module pass mark. Project clocks start separately. ProofLoop weights are 50% verified tests, 30% code defence, 10% code quality and 10% deadline compliance. An instructor records the official review. Late deductions follow the assignment’s configured deadline policy.'},
    {title: 'Project CLI commands and Git submission',
      text: 'Install the CLI from the source tree. Use a password-enabled account. OAuth-only learners can use the browser Project lab, or ask the Academy about a password for CLI use. Replace PROJECT-SLUG with the value from saire list. Run test and submit in the project folder. Commit and push your changes to the approved GitHub repository first. The CLI submits the exact commit hash.',
      code: 'python -m pip install -e ./tools\nsaire login --server http://127.0.0.1:8000/api/v1\nsaire list\nsaire start PROJECT-SLUG\nsaire test\nsaire submit PROJECT-SLUG\nsaire grade PROJECT-SLUG\nsaire logout'},
    {title: 'Mentor and Code Defence practice',
      text: `Live Mentor requests are limited to ${policy.mentor_hourly} and ${policy.mentor_daily} per learner. Try one small change before asking. Say what you expected, what happened, and what you need help with. Code Defence practice has its own 8/hour limit. Use the sharing controls before sending practice text to the AI provider. Your instructor and the graded rubric determine official marks.`},
    {title: 'Academic integrity',
      text: 'Submit your own work and be ready to explain it. Credit tutorials and permitted help. Use the Mentor for hints. Keep credentials, private code and personal information out of practice text. An instructor-approved worker verifies supported submissions independently.'},
    {title: 'Late work, technical problems and accommodations',
      text: 'Contact the Academy early. Include the lesson or project, deadline, when the problem started and the exact error, with private details removed. Ask about an accessible editor, text instructions, keyboard access or a reviewed timing arrangement. Support and timing arrangements are handled by the Academy directly.'},
    {title: 'Administrator testing',
      text: 'Django superusers can preview content and bypass orientation, setup and curriculum locks for testing. Use a normal learner account to test the progression rules. Staff accounts without superuser access follow the learner gates.'},
  ];
}

export default function AcademyHandbook({ orientation, refresh }: {
  orientation: Orientation; refresh: () => Promise<void>;
}) {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [query, setQuery] = useState('');
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    api<Policy>('/academy/handbook/').then(
      data => { if (active) setPolicy(data); },
      cause => { if (active) setError(cause.message); },
    );
    return () => { active = false; };
  }, [orientation.version]);

  async function acknowledge() {
    if (!policy || !confirm || busy) return;
    setBusy(true);
    setError('');
    try {
      const accepted = await api<Orientation>('/academy/orientation/', {version: policy.orientation.version, accept: true});
      setPolicy({...policy, orientation: accepted});
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not save acknowledgment.');
    } finally {
      setBusy(false);
    }
  }

  if (!policy) return <p role={error ? 'alert' : 'status'}>{error || 'Loading the handbook…'}</p>;
  const entries = handbookEntries(policy).filter(entry =>
    [entry.title, entry.text, entry.code].join(' ').toLowerCase().includes(query.trim().toLowerCase()));
  return <>
    <h2>Academy Handbook</h2>
    <label className="study-label">Search rules and commands
      <input type="search" value={query} onChange={event => setQuery(event.target.value)} />
    </label>
    <p role="status">{entries.length} sections</p>
    {entries.map(entry => <section key={entry.title} className="study-panel">
      <h3>{entry.title}</h3><p>{entry.text}</p>
      {entry.code && <><pre><code>{entry.code}</code></pre><p>For a hosted installation, use your Academy’s HTTPS API address.</p></>}
    </section>)}
    <p>{policy.support_email ? <a href={`mailto:${policy.support_email}`}>Email Academy support</a>
      : 'For help, use the contact channel provided by your instructor or Academy administrator.'}</p>
    <form className="study-panel" onSubmit={event => { event.preventDefault(); void acknowledge(); }}>
      <h3>Rules acknowledgment</h3>
      {policy.orientation.acknowledged ? <p role="status">Acknowledged · {policy.orientation.version}</p> : <>
        <label className="study-choice"><input type="checkbox" checked={confirm}
          onChange={event => setConfirm(event.target.checked)} /> I have read this version of the Academy rules.</label>
        <button className="btn btn-primary" disabled={!confirm || busy}>{busy ? 'Saving…' : 'Acknowledge rules'}</button>
      </>}
      {error && <p role="alert">{error}</p>}
    </form>
  </>;
}
