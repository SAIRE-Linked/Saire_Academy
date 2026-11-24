'use client';

import { useEffect, useState } from 'react';

type Request = <T>(path: string, body?: object) => Promise<T>;
type Defence = {
  commit_sha: string;
  repository_url: string;
  questions: string[];
  answers: string[];
  revision: number;
  status: 'draft' | 'submitted' | 'reviewed';
  editable: boolean;
  submitted_at: string | null;
  practice_provider: 'gemini' | 'openai' | null;
};
type PracticeFeedback = { observation: string; evidence_gap: string; next_step: string };

export default function CodeDefenceRoom({ assignment, submissionId, request, onChanged }: {
  assignment: string;
  submissionId: number;
  request: Request;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [record, setRecord] = useState<Defence | null>(null);
  const [answers, setAnswers] = useState<string[]>([]);
  const [reload, setReload] = useState(0);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const path = `/assignments/${encodeURIComponent(assignment)}/submissions/${submissionId}/defence/`;

  useEffect(() => {
    if (!open) return;
    let active = true;
    setError('');
    request<Defence>(path).then(
      data => {
        if (active) {
          setRecord(data);
          setAnswers(data.answers);
        }
      },
      cause => { if (active) setError(cause.message); },
    );
    return () => { active = false; };
  }, [open, path, reload, request]);

  function reloadSaved() {
    setRecord(null);
    setConfirm(false);
    setNotice('');
    setReload(value => value + 1);
  }

  async function save(action: 'save' | 'submit') {
    if (!record?.editable || busy) return;
    setError('');
    setNotice('');
    setBusy(true);
    try {
      const data = await request<Defence>(path, {
        action, revision: record.revision, questions: record.questions, answers,
      });
      setRecord(data);
      setAnswers(data.answers);
      setConfirm(false);
      setNotice(action === 'submit' ? 'Defence handed in for instructor review.' : 'Draft saved to your account.');
      onChanged();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The defence could not be saved.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="proofloop-defence" aria-label="Code Defence Room">
      <button type="button" className="proofloop-secondary" aria-expanded={open}
        onClick={() => {
          if (!open) { setRecord(null); setNotice(''); }
          setOpen(!open);
          setConfirm(false);
        }} disabled={busy}>
        {open ? 'Close Code Defence Room' : 'Open Code Defence Room'}
      </button>
      {open && <div className="proofloop-defence-content">
        <h3>Code Defence Room</h3>
        {error && <p role="alert" className="proofloop-mentor-error">{error}</p>}
        {error && <button type="button" className="proofloop-secondary" onClick={reloadSaved}>Reload saved copy</button>}
        {notice && <p role="status">{notice}</p>}
        {!record && !error && <p role="status">Opening your defence…</p>}
        {record && <>
          <p>Explain the decisions in commit {record.repository_url.startsWith('https://github.com/') ? (
            <a href={`${record.repository_url}/commit/${record.commit_sha}`} target="_blank" rel="noreferrer">
              <code>{record.commit_sha.slice(0, 12)}</code>
            </a>
          ) : <code>{record.commit_sha.slice(0, 12)}</code>}. Use function names, tests, or specific trade-offs as evidence.</p>
          {record.submitted_at && <p>Handed in {new Date(record.submitted_at).toLocaleString()}.</p>}
          {record.status === 'reviewed' && !record.submitted_at && <p>This commit was already reviewed before a written defence was handed in.</p>}
          <div className="proofloop-defence-answers">
            {record.questions.map((question, index) => (
              <div key={index}>
                <label htmlFor={`defence-${submissionId}-${index}`}><strong>{index + 1}. {question}</strong></label>
                <textarea id={`defence-${submissionId}-${index}`} rows={4} maxLength={2000}
                  readOnly={!record.editable || busy} value={answers[index] ?? ''}
                  onChange={event => {
                    const value = event.target.value;
                    setAnswers(current => current.map((answer, i) => i === index ? value : answer));
                    setConfirm(false);
                  }} />
              </div>
            ))}
          </div>
          {record.editable && <div className="proofloop-defence-actions">
            <button type="button" className="proofloop-secondary" disabled={busy} onClick={() => void save('save')}>Save draft</button>
            {confirm ? <>
              <p role="status">Handing in makes these answers read-only and visible to your instructor.</p>
              <button type="button" className="proofloop-primary" disabled={busy} onClick={() => void save('submit')}>Confirm hand-in</button>
              <button type="button" className="proofloop-secondary" disabled={busy} onClick={() => setConfirm(false)}>Keep editing</button>
            </> : <button type="button" className="proofloop-primary" disabled={busy || !answers.every(answer => answer.trim())}
              onClick={() => setConfirm(true)}>Hand in defence</button>}
          </div>}
          <DefencePractice path={path} record={record} submissionId={submissionId} request={request} />
        </>}
      </div>}
    </section>
  );
}

function DefencePractice({ path, record, submissionId, request }: {
  path: string;
  record: Defence;
  submissionId: number;
  request: Request;
}) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [consent, setConsent] = useState(false);
  const [feedback, setFeedback] = useState<PracticeFeedback | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const provider = record.practice_provider === 'gemini' ? 'Gemini' : 'OpenAI';

  async function getPractice(mode: 'question' | 'feedback') {
    if (busy || (mode === 'feedback' && (!question || !answer.trim() || !consent))) return;
    setBusy(true);
    setError('');
    try {
      if (mode === 'question') {
        const result = await request<{ question: string }>(`${path}practice/`, { mode });
        setQuestion(result.question);
        setAnswer('');
        setFeedback(null);
      } else {
        setConsent(false);
        setFeedback(await request<PracticeFeedback>(`${path}practice/`, {
          mode, question, answer, share_practice_answer: true,
        }));
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Practice is temporarily unavailable.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <details className="proofloop-defence-practice">
      <summary>Practise before your review</summary>
      <p>Start with one rubric question. Name a decision, point to evidence, and explain what you would change next.</p>
      <blockquote>{record.questions[0]}</blockquote>
      {record.practice_provider && <>
        <p>Optional {provider} coaching. Practice stays separate from your official defence and grades.</p>
        <button type="button" className="proofloop-secondary" disabled={busy} onClick={() => void getPractice('question')}>
          Generate practice question
        </button>
        {question && <>
          <p><strong>{question}</strong></p>
          <label htmlFor={`practice-${submissionId}`}>Your practice answer</label>
          <textarea id={`practice-${submissionId}`} value={answer} maxLength={1200} rows={3} disabled={busy}
            onChange={event => { setAnswer(event.target.value); setConsent(false); setFeedback(null); }} />
          <label className="proofloop-defence-consent">
            <input type="checkbox" checked={consent} disabled={busy} onChange={event => setConsent(event.target.checked)} />
            Share this practice question and answer with {provider} for this request. Keep private code and credentials out of the answer.
          </label>
          <button type="button" className="proofloop-secondary" disabled={busy || !consent || !answer.trim()} onClick={() => void getPractice('feedback')}>
            Get practice feedback
          </button>
        </>}
        {busy && <p role="status">Preparing practice…</p>}
        {error && <p role="alert" className="proofloop-mentor-error">{error}</p>}
        {feedback && <dl aria-live="polite">
          <dt>What you explained</dt><dd>{feedback.observation}</dd>
          <dt>Evidence to add</dt><dd>{feedback.evidence_gap}</dd>
          <dt>What to practise next</dt><dd>{feedback.next_step}</dd>
        </dl>}
      </>}
      {!record.practice_provider && <p>The guided practice checklist is available here. Live coaching needs a configured AI provider.</p>}
    </details>
  );
}
