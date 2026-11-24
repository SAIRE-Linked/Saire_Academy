'use client';

import {useEffect, useState, type FormEvent} from 'react';
import {BrainCircuit} from 'lucide-react';
import {api} from '@/lib/session-api';

type Message = {role: 'learner' | 'mentor'; text: string};
type Thread = {mode: 'ai' | 'unconfigured'; provider: string | null; messages: Message[]};

export default function DashboardMentor({assignment, title, lesson}: {assignment?: string; title?: string; lesson?: string}) {
  const [thread, setThread] = useState<Thread | null>(null);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);
  const endpoint = assignment ? `/assignments/${encodeURIComponent(assignment)}/mentor/` : '';
  useEffect(() => {
    let active = true;
    if (endpoint) api<Thread>(endpoint).then(data => {if (active) setThread(data);},
      () => {if (active) setError('The project conversation could not be loaded.');});
    return () => {active = false;};
  }, [endpoint]);
  async function send(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || sending || thread?.mode !== 'ai') return;
    setSending(true); setError('');
    try {
      const reply = await api<{learner_message: Message; mentor_message: Message}>(endpoint, {message: input.trim(), use_learning_twin: false});
      setThread(previous => previous && ({...previous, messages: [...previous.messages, reply.learner_message, reply.mentor_message]}));
      setInput('');
    } catch {setError('Your message could not be sent. Your draft is still here.');}
    finally {setSending(false);}
  }
  return <aside className="workspace-mentor"><BrainCircuit size={28} aria-hidden="true"/><h2>Socratic Mentor</h2>
    <p className="mentor-context">{title || lesson || 'Study planning'}</p>
    {thread?.mode === 'ai' ? <>
      <div className="mentor-history" aria-live="polite">{thread.messages.slice(-4).map((item, i) =>
        <p key={i}><b>{item.role === 'mentor' ? 'Mentor' : 'You'}</b><br/>{item.text}</p>)}</div>
      <form onSubmit={send}><label htmlFor="workspace-question">Ask about this project</label>
        <textarea id="workspace-question" rows={3} maxLength={1200} value={input} onChange={event => setInput(event.target.value)}/>
        <small>Sent to {thread.provider || 'the configured AI provider'} and saved in your project conversation.</small>
        <button className="btn btn-primary" disabled={sending || !input.trim()}>{sending ? 'Sending…' : 'Ask for a hint'}</button></form>
    </> : <><h3>Study prompt</h3><p>{assignment ? 'Pick one requirement from the brief. What input and expected result would show that it works?' :
      lesson ? 'Before opening the lesson, write down one thing you already know about this topic and one question to answer.' :
      'Which prerequisite could you complete in your next study session?'}</p>
      <small>{assignment ? thread ? 'Live AI is unconfigured for this project.' : error ? '' : 'Checking project mentor availability…' : 'Start an unlocked project to open its mentor conversation.'}</small></>}
    {error && <p role="alert">{error}</p>}
    <a href={assignment ? `/assignments/?assignment=${encodeURIComponent(assignment)}#project-mentor` : '/assignments/'}>{assignment ? 'Open project conversation' : 'Explore assignments'} →</a>
  </aside>;
}
