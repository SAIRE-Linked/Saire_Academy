'use client';

import { useEffect, useState } from 'react';
import { Github } from 'lucide-react';
import { dashboardDestination } from '@/lib/academy-display';
import { api } from '@/lib/session-api';
import { watchSessionEnd } from '@/lib/browser-session';

export default function AcademySignIn() {
  const [destination, setDestination] = useState('/dashboard/');
  const [returning, setReturning] = useState(false);
  const [providers, setProviders] = useState<string[] | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [loggedOut, setLoggedOut] = useState(false);

  useEffect(() => {
    let active = true, ended = false;
    const stop = watchSessionEnd(() => { ended = true; setSignedIn(false); setLoggedOut(true); });
    const requested = new URLSearchParams(window.location.search).get('next');
    setDestination(dashboardDestination(requested));
    setReturning(Boolean(requested));
    setLoggedOut(new URLSearchParams(window.location.search).get('signed_out') === '1');
    api<{ providers: string[] }>('/auth/csrf/').then(
      data => setProviders(data.providers),
      () => setUnavailable(true),
    );
    api('/auth/me/').then(() => { if (active && !ended) setSignedIn(true); }, () => {});
    return () => { active = false; stop(); };
  }, []);

  return (
    <section className="entry-card" id="signin" aria-labelledby="signin-title">
      <p className="entry-eyebrow">YOUR LEARNING SPACE</p>
      <h2 id="signin-title">{signedIn ? 'Welcome back' : 'Sign in to the Academy'}</h2>
      {loggedOut && !signedIn && <p role="status">You’re logged out. Sign in below to continue learning.</p>}
      {returning && <p role="status">{signedIn ? 'Your requested Academy page is ready.' : 'Sign in to open your requested Academy page. You will return there after signing in.'}</p>}
      <p>Open your roadmap, project lab, Mentor and Learning Twin from your dashboard.</p>
      {signedIn ? <a className="entry-button" href={destination}>{returning ? "Continue to your requested page" : "Open your dashboard"}</a> : (
        <div className="entry-provider-list">
          {['google', 'github'].map(provider => {
            const name = provider === 'google' ? 'Google' : 'GitHub';
            const icon = provider === 'google' ? <span aria-hidden="true" className="entry-google">G</span> : <Github size={20} aria-hidden="true" />;
            return providers?.includes(provider) ? (
              <a className="entry-button" key={provider} href={`/accounts/${provider}/login/?next=${encodeURIComponent(destination)}`}>
                {icon} Continue with {name}
              </a>
            ) : (
              <button className="entry-button" type="button" key={provider} disabled>
                {icon} Continue with {name}
              </button>
            );
          })}
          {unavailable && <p role="status">Sign-in is temporarily unavailable.</p>}
          {providers && providers.length < 2 && <p role="status">Disabled providers need credentials in the Academy settings.</p>}
          <a className="entry-pilot" href={`/accounts/login/?next=${encodeURIComponent(destination)}`}>Use a pilot account</a>
        </div>
      )}
    </section>
  );
}
