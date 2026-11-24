'use client';

import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '@/lib/session-api';
import { endBrowserSession, watchSessionEnd } from '@/lib/browser-session';

export default function AccountControls({username, onLogout}: {username?: string | null; onLogout?: () => Promise<void>}) {
  const [account, setAccount] = useState<string | null | undefined>(username);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const version = useRef(0);
  useEffect(() => watchSessionEnd(() => { version.current++; setAccount(null); }), []);
  useEffect(() => {
    if (username !== undefined) { setAccount(username); return; }
    let active = true;
    const request = ++version.current;
    api<{username: string}>('/auth/me/').then(
      data => { if (active && request === version.current) setAccount(data.username); },
      cause => { if (active && request === version.current) { setAccount(null); if (!(cause instanceof ApiError && [401,403].includes(cause.status))) setError('Account service unavailable.'); } },
    );
    return () => { active = false; };
  }, [username]);
  async function logout() {
    if (busy) return;
    setBusy(true); setError('');
    try { await (onLogout ?? endBrowserSession)(); }
    catch { setError('Could not log out. Check your connection and try again.'); setBusy(false); }
  }
  return <div className="account-controls">
    {account === undefined ? <span role="status">Checking account…</span> : account ? <>
      <span className="account-name">{account}</span>
      <button type="button" className="btn btn-outline" disabled={busy} onClick={() => void logout()}>{busy ? 'Logging out…' : 'Log out'}</button>
    </> : <a className="btn btn-outline" href="/#signin">Sign in</a>}
    {error && <span className="account-error" role="alert">{error}</span>}
  </div>;
}
