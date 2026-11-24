'use client';

import { useEffect, useId, useRef, useState } from 'react';
import { createPracticeFrame, readPracticeReply, MAX_CODE, MAX_INPUT, RUN_TIMEOUT_MS, LOAD_TIMEOUT_MS, PYODIDE_VERSION } from '@/lib/python-practice';

type Pending = {id:string; code:string; stdin:string};
type Frame = {channel:string; document:string};

export default function PythonPractice({lessonId, example, owner}: {lessonId:string; example:string; owner:string}) {
  const id = useId();
  const storageKey = `saire-python-practice-v1:${encodeURIComponent(owner)}:${encodeURIComponent(lessonId)}`;
  const [code, setCode] = useState(example || 'print("Hello, SAIRE!")\n');
  const [stdin, setStdin] = useState('');
  const [hydrated, setHydrated] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [phase, setPhase] = useState<'idle'|'loading'|'ready'|'running'|'finished'>('idle');
  const [status, setStatus] = useState('Load Python when you are ready to practise.');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [frame, setFrame] = useState<Frame | null>(null);
  const iframe = useRef<HTMLIFrameElement>(null);
  const channel = useRef('');
  const pending = useRef<Pending | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const saving = useRef(true);
  const state = useRef(phase); state.current = phase;

  function clearTimer() { if (timer.current) clearTimeout(timer.current); timer.current = null; }
  function destroy() {
    clearTimer();
    iframe.current?.contentWindow?.postMessage({type:'stop', channel:channel.current}, '*');
    channel.current = ''; pending.current = null;
    setFrame(null);
  }
  function stop(message = 'Stopped. Your code is still in the editor.') {
    destroy(); setPhase('idle'); setStatus(message);
  }
  useEffect(() => {
    try {
      const draft = localStorage.getItem(storageKey);
      if (draft !== null) setCode(draft.slice(0,MAX_CODE));
    } catch { /* editing remains available without storage */ }
    setHydrated(true);
    const logout = () => { saving.current = false; stop('Logged out.'); setCode(''); setStdin(''); setOutput(''); setError(''); };
    window.addEventListener('saire:session-ended', logout);
    return () => { destroy(); window.removeEventListener('saire:session-ended', logout); };
  }, []);
  useEffect(() => { if (hydrated && saving.current) { try { localStorage.setItem(storageKey,code); } catch { /* optional browser storage */ } } }, [code,hydrated,storageKey]);

  function sendRun() {
    if (!pending.current || !iframe.current?.contentWindow) return;
    clearTimer(); setPhase('running'); setStatus('Running your practice code…');
    iframe.current.contentWindow.postMessage({type:'run', channel:channel.current, ...pending.current}, '*');
    timer.current = setTimeout(() => stop('Stopped after 10 seconds. Check for an endless loop, then try again.'), RUN_TIMEOUT_MS);
  }
  useEffect(() => {
    const receive = (event: MessageEvent) => {
      if (!channel.current || event.source !== iframe.current?.contentWindow || event.origin !== 'null') return;
      const reply = readPracticeReply(event.data, channel.current, pending.current?.id ?? null);
      if (!reply) return;
      if (reply.type === 'ready') {
        if (state.current !== 'loading') return;
        clearTimer();
        if (pending.current) sendRun();
        else { setPhase('ready'); setStatus('Python is ready. Change the example and choose Run Python.'); }
      } else if (reply.type === 'load-error') {
        destroy(); setPhase('idle'); setError(reply.message); setStatus('Editor available; Python has not loaded.');
      } else {
        setOutput(reply.output + (reply.truncated ? '\n[Output shortened to 16,000 characters.]' : ''));
        setError(reply.error); destroy(); setPhase('finished');
        setStatus(reply.error ? 'Practice finished with an error. Read the message and try a small change.' : 'Practice finished. Compare the output with your prediction.');
      }
    };
    window.addEventListener('message', receive);
    return () => window.removeEventListener('message', receive);
  }, []);

  function load(runAfterLoad = false) {
    destroy(); setEnabled(true); setError(''); setOutput('');
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    const value = Array.from(bytes, item => item.toString(16).padStart(2,'0')).join('');
    channel.current = value;
    if (runAfterLoad) pending.current = {id:crypto.randomUUID(), code, stdin};
    setFrame({channel:value, document:createPracticeFrame(value,window.location.origin)});
    setPhase('loading'); setStatus('Loading Python. The first download can take a little time…');
    timer.current = setTimeout(() => { stop('Python took too long to load. Try again, or download your code for a local IDE.'); }, LOAD_TIMEOUT_MS);
  }
  function run() {
    if (phase === 'loading' || phase === 'running' || !code.trim()) return;
    setError(''); setOutput('');
    if (phase === 'ready' && iframe.current?.contentWindow && channel.current) { pending.current = {id:crypto.randomUUID(),code,stdin}; sendRun(); }
    else load(true); // A fresh worker gives each run a clean Python environment.
  }
  function reset() { stop('Example restored.'); setCode(example || 'print("Hello, SAIRE!")\n'); setStdin(''); setOutput(''); setError(''); }
  function download() {
    const url = URL.createObjectURL(new Blob([code],{type:'text/x-python;charset=utf-8'}));
    const link = document.createElement('a'); link.href = url; link.download = `${lessonId.replace(/[^a-zA-Z0-9_-]/g,'_')}-practice.py`;
    document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url),1000);
  }
  const busy = phase === 'loading' || phase === 'running';
  return <section className="python-practice" aria-labelledby={`${id}-title`}>
    <div className="practice-heading"><div><span className="eyebrow">TRY IT HERE</span><h3 id={`${id}-title`}>Python practice studio</h3></div><span className="practice-badge">Practice · not graded</span></div>
    <p>Predict the output, change one thing, then run the example. Practice runs never award marks or unlock a lesson.</p>
    <label htmlFor={`${id}-code`}>Your Python code</label>
    <textarea id={`${id}-code`} className="practice-editor" value={code} maxLength={MAX_CODE} onChange={e => setCode(e.target.value)} onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); if (enabled) run(); } }} spellCheck={false} autoCapitalize="off" autoComplete="off" rows={10} />
    <small>Draft saved only in this browser for this account and lesson. Use four spaces for indentation; Tab moves focus. Ctrl+Enter runs after loading Python.</small>
    <details className="practice-input"><summary>Input values for input() (optional)</summary><label htmlFor={`${id}-input`}>One value per line, in the order your program asks</label><textarea id={`${id}-input`} value={stdin} maxLength={MAX_INPUT} onChange={e => setStdin(e.target.value)} rows={3} /><p>Missing values produce EOFError. They do not open a browser prompt.</p></details>
    <div className="practice-actions">
      {!enabled ? <button type="button" className="btn btn-primary" onClick={() => load()}>Load Python</button> : <button type="button" className="btn btn-primary" disabled={busy || !code.trim()} onClick={run}>{phase === 'loading' ? 'Loading Python…' : phase === 'running' ? 'Running…' : 'Run Python'}</button>}
      <button type="button" className="btn btn-outline" disabled={!busy} onClick={() => stop()}>Stop</button>
      <button type="button" className="btn btn-outline" onClick={reset}>Reset example</button>
      <button type="button" className="btn btn-outline" onClick={download}>Download .py</button>
    </div>
    <p className="practice-status" role="status" aria-live="polite">{status}</p>
    <label htmlFor={`${id}-output`}>Output</label>
    <pre id={`${id}-output`} className="practice-output" role="region" aria-label="Python output" tabIndex={0}>{output || (phase === 'finished' ? 'No output was printed. Use print(...) to display a value.' : 'Your program’s output will appear here.')}</pre>
    {error && <div className="practice-error" role="alert"><strong>Python message</strong><pre>{error}</pre></div>}
    <p className="practice-footnote">Python runs in your browser. The first load downloads the bundled Pyodide runtime (v{PYODIDE_VERSION}) from the Academy; later loads can use your browser’s cache. Desktop tools and extra packages may need your local IDE. For end-of-module projects, use your own IDE, Git and the ProofLoop submission workflow.</p>
    {frame && <iframe key={frame.channel} ref={iframe} title="Isolated Python practice runtime" sandbox="allow-scripts" referrerPolicy="no-referrer" srcDoc={frame.document} aria-hidden="true" tabIndex={-1} className="practice-runtime" />}
  </section>;
}
