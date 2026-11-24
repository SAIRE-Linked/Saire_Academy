'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/session-api';

type Note = {id: number; title: string; mistake: string; correction: string; updated_at: string};
type Draft = Pick<Note, 'title' | 'mistake' | 'correction'> & {id?: number};
const emptyDraft: Draft = {title: '', mistake: '', correction: ''};

export default function MistakesNotebook() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [confirm, setConfirm] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const path = '/academy/notes/';

  useEffect(() => {
    let active = true;
    api<Note[]>(path).then(
      data => { if (active) setNotes(data); },
      cause => { if (active) setError(cause.message); },
    );
    return () => { active = false; };
  }, []);

  async function save() {
    if (busy || !draft.title.trim() || !draft.mistake.trim()) return;
    setBusy(true); setError(''); setNotice('');
    try {
      const note = await api<Note>(path, {...draft, action: 'save'});
      setNotes(previous => [note, ...previous.filter(item => item.id !== note.id)]);
      setDraft(emptyDraft);
      setNotice('Note saved to your account.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not save the note.');
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    setBusy(true); setError(''); setNotice('');
    try {
      await api(path, {action: 'delete', id});
      setNotes(previous => previous.filter(note => note.id !== id));
      if (draft.id === id) setDraft(emptyDraft);
      setConfirm(null);
      setNotice('Note deleted.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not delete the note.');
    } finally {
      setBusy(false);
    }
  }

  return <>
    <h2>Mistakes notebook</h2>
    <p>Write down what you tried, what surprised you, and what you’ll try next. These are private account notes.</p>
    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    <form className="study-panel" onSubmit={event => { event.preventDefault(); void save(); }}>
      <h3>{draft.id ? 'Edit your note' : 'Add a note'}</h3>
      <label className="study-label">Title<input required maxLength={100} value={draft.title}
        onChange={event => setDraft({...draft, title: event.target.value})} /></label>
      <label className="study-label">What happened?<textarea required maxLength={1500} rows={3} value={draft.mistake}
        onChange={event => setDraft({...draft, mistake: event.target.value})} /></label>
      <label className="study-label">What will you change?<textarea maxLength={1500} rows={3} value={draft.correction}
        onChange={event => setDraft({...draft, correction: event.target.value})} /></label>
      <div className="study-actions">
        <button className="btn btn-primary" disabled={busy || !draft.title.trim() || !draft.mistake.trim()}>Save note</button>
        {draft.id && <button className="btn btn-outline" type="button" onClick={() => setDraft(emptyDraft)}>Cancel editing</button>}
      </div>
    </form>
    {notes.map(note => <section key={note.id} className="study-panel">
      <h3>{note.title}</h3><p>{note.mistake}</p>{note.correction && <p><strong>Next try: </strong>{note.correction}</p>}
      <div className="study-actions">
        <button className="btn btn-outline" disabled={busy} onClick={() => { setDraft(note); setConfirm(null); }}>Edit note</button>
        {confirm === note.id ? <>
          <button className="btn btn-outline" disabled={busy} onClick={() => void remove(note.id)}>Confirm delete</button>
          <button className="btn btn-outline" disabled={busy} onClick={() => setConfirm(null)}>Keep note</button>
        </> : <button className="btn btn-outline" disabled={busy} onClick={() => setConfirm(note.id)}>Delete note</button>}
      </div>
    </section>)}
  </>;
}
