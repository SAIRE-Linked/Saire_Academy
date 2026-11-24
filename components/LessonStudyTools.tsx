'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/session-api';

export type Resource = { title: string; url: string; purpose: string };
export type LessonGuide = {
  explanation: string;
  demonstration: string;
  example: string;
  guided_exercise: string;
  independent_exercise: string;
  further_explanation: string;
};
type Score = {correct: number; total: number};
type CheckData = {
  questions: {id: number; prompt: string; options: string[]}[];
  can_answer: boolean;
  results: {before?: Score; after?: Score};
};
type CheckResponse = Pick<CheckData, 'results'> & {feedback: {correct: boolean; explanation: string}[]};

export function ResourceLinks({ links }: {links: Resource[]}) {
  if (!links.length) return null;
  return <section className="study-panel">
    <h3>Optional resources</h3>
    <ul>{links.map(link => <li key={link.url}><a href={link.url} target="_blank" rel="noreferrer">{link.title}</a>
      {' · '}{link.purpose}</li>)}</ul>
  </section>;
}

export function GuidedLesson({ guide }: {guide: LessonGuide}) {
  return <section className="study-panel">
    <h3>Learn it step by step</h3>
    <h4>1. Explain</h4><p>{guide.explanation}</p>
    <h4>2. Demonstrate</h4><p>{guide.demonstration}</p>
    {guide.example && <pre><code>{guide.example}</code></pre>}
    <h4>3. Try it with guidance</h4><p>{guide.guided_exercise}</p>
    <h4>4. Try it on your own</h4><p>{guide.independent_exercise}</p>
    {guide.further_explanation && <details><summary>Extra explanation</summary><p>{guide.further_explanation}</p></details>}
  </section>;
}

export function FormativePanel({ lesson, stage }: {lesson: string; stage: 'before' | 'after'}) {
  const [open, setOpen] = useState(false);
  const [check, setCheck] = useState<CheckData | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [feedback, setFeedback] = useState<CheckResponse['feedback']>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const path = `/academy/lessons/${encodeURIComponent(lesson)}/check/${stage}/`;

  useEffect(() => {
    if (!open) return;
    let active = true;
    api<CheckData>(path).then(
      data => { if (active) { setCheck(data); setError(''); } },
      cause => { if (active) setError(cause.message); },
    );
    return () => { active = false; };
  }, [path, open]);

  async function submit() {
    if (!check || busy) return;
    setBusy(true);
    setError('');
    try {
      const result = await api<CheckResponse>(path, {
        question_ids: check.questions.map(question => question.id),
        answers: check.questions.map(question => answers[question.id]),
      });
      setCheck({ ...check, results: result.results });
      setFeedback(result.feedback);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not save your check.');
    } finally {
      setBusy(false);
    }
  }

  return <details className="study-panel" onToggle={event => setOpen(event.currentTarget.open)}>
    <summary>{stage === 'before' ? 'Before you begin · quick practice check' : '5. Check understanding · quick after check'}</summary>
    <p>This optional practice saves your result for revision. It carries no grade and starts no timer.</p>
    {error && <p role="alert">{error}</p>}
    {open && !check && !error && <p role="status">Loading the practice check…</p>}
    {check && <>
      <div aria-live="polite">{check.results.before && <p>Before check {check.results.before.correct}/{check.results.before.total}</p>}
        {check.results.after && <p>After check {check.results.after.correct}/{check.results.after.total}</p>}
      </div>
      {!check.questions.length && <p>A practice check is being prepared for this lesson.</p>}
      {check.questions.length > 0 && !check.can_answer && <p>This check is closed for your current lesson stage.</p>}
      {check.can_answer && <form onSubmit={event => { event.preventDefault(); void submit(); }}>
        {check.questions.map((question, index) => <fieldset key={question.id}>
          <legend>{question.prompt}</legend>
          {question.options.map((option, choice) => <label className="study-choice" key={choice}>
            <input type="radio" name={`check-${stage}-${question.id}`} required
              checked={answers[question.id] === choice}
              onChange={() => { setAnswers(previous => ({...previous, [question.id]: choice})); setFeedback([]); }} />{option}
          </label>)}
          {feedback[index] && <p role="status">{feedback[index].correct ? 'Correct. ' : 'Review this idea. '}{feedback[index].explanation}</p>}
        </fieldset>)}
        <button className="btn btn-outline" disabled={busy || Object.keys(answers).length !== check.questions.length}>
          {busy ? 'Saving…' : 'Check my understanding'}
        </button>
      </form>}
    </>}
  </details>;
}
