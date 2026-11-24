import { api, ApiError } from './session-api';

export const SESSION_ENDED_KEY = 'saire-session-ended-v1';
export const SIGN_IN_URL = '/?signed_out=1#signin';

export async function endBrowserSession() {
  try { await api('/auth/session-logout/', {}); }
  catch (error) {
    // An expired session is already signed out. A CSRF or network failure while
    // still authenticated must be shown rather than pretending logout worked.
    if (!(error instanceof ApiError) || ![401, 403].includes(error.status)) throw error;
    let ended = false;
    try { await api('/auth/me/'); }
    catch (check) { ended = check instanceof ApiError && [401, 403].includes(check.status); }
    if (!ended) throw error;
  }
  try { localStorage.setItem(SESSION_ENDED_KEY, `${Date.now()}:${crypto.randomUUID()}`); } catch { /* storage optional */ }
  try {
    const channel = new BroadcastChannel(SESSION_ENDED_KEY);
    channel.postMessage('ended'); channel.close();
  } catch { /* older browsers use the storage event */ }
  window.dispatchEvent(new Event('saire:session-ended'));
  window.location.replace(SIGN_IN_URL);
}

export function watchSessionEnd(onEnd: () => void) {
  let ended = false;
  const complete = () => { if (!ended) { ended = true; onEnd(); } };
  const storage = (event: StorageEvent) => { if (event.key === SESSION_ENDED_KEY && event.newValue) complete(); };
  window.addEventListener('storage', storage);
  window.addEventListener('saire:session-ended', complete);
  let channel: BroadcastChannel | undefined;
  try { channel = new BroadcastChannel(SESSION_ENDED_KEY); channel.onmessage = event => { if (event.data === 'ended') complete(); }; }
  catch { /* storage listener remains available */ }
  return () => { window.removeEventListener('storage', storage); window.removeEventListener('saire:session-ended', complete); channel?.close(); };
}
