/** Browser-only, ungraded Python. No learner code is interpolated into HTML. */
export const PYODIDE_VERSION = '0.29.5';
export const PYODIDE_PATH = `/python-runtime/v${PYODIDE_VERSION}/`;
export const MAX_CODE = 20_000;
export const MAX_INPUT = 8_000;
export const MAX_OUTPUT = 16_000;
export const RUN_TIMEOUT_MS = 10_000;
export const LOAD_TIMEOUT_MS = 90_000;

const workerSource = (index: string) => String.raw`
(async () => {
let py;
  try {
    importScripts(${JSON.stringify(index + 'pyodide.js')});
    py = await loadPyodide({indexURL: ${JSON.stringify(index)}});
  } catch (cause) {
    self.postMessage({type:'load-error', message:'Python could not load. ' + String(cause).slice(0,400)});
    throw cause;
  }
let started = false;
self.onmessage = async ({data}) => {
  if (started || data?.type !== 'run' || typeof data.id !== 'string' || typeof data.code !== 'string' || data.code.length > 20000 || typeof data.stdin !== 'string' || data.stdin.length > 8000) return;
  started = true;
  let output = '', truncated = false;
  const capture = text => {
    const room = 16000 - output.length;
    if (text.length > room) truncated = true;
    if (room > 0) output += text.slice(0, room);
  };
  const stdoutDecoder = new TextDecoder();
  const stderrDecoder = new TextDecoder();
  py.setStdout({write: bytes => {capture(stdoutDecoder.decode(bytes, {stream:true})); return bytes.length;}});
  py.setStderr({write: bytes => {capture(stderrDecoder.decode(bytes, {stream:true})); return bytes.length;}});
  const lines = data.stdin === '' ? [] : data.stdin.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n');
  let cursor = 0;
  py.setStdin({stdin: () => cursor < lines.length ? lines[cursor++] : null, isatty:false});
  const globals = py.runPython('dict()');
  globals.set('__name__', '__main__');
  let error = '';
  try {
    const result = await py.runPythonAsync(data.code, {globals, filename:'practice.py'});
    if (result && typeof result.destroy === 'function') result.destroy();
  } catch (cause) { error = String(cause).slice(-5000); }
  finally { globals.destroy(); }
  capture(stdoutDecoder.decode()); capture(stderrDecoder.decode());
  self.postMessage({type:'result', id:data.id, output, error, truncated});
};
self.postMessage({type:'ready'});
})().catch(() => {});
`;

export function createPracticeFrame(channel: string, parentOrigin: string): string {
  if (!/^[a-f0-9]{32}$/.test(channel)) throw new Error('Invalid practice channel.');
  const origin = new URL(parentOrigin);
  if (!['http:', 'https:'].includes(origin.protocol) || origin.origin !== parentOrigin) throw new Error('Invalid parent origin.');
  const index = new URL(PYODIDE_PATH, parentOrigin).href;
  const policy = `default-src 'none'; script-src 'nonce-${channel}' 'wasm-unsafe-eval' blob: ${index}; worker-src blob:; connect-src ${index}; img-src 'none'; media-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'`;
  // The frame has an opaque origin (no allow-same-origin). Its worker inherits
  // the restrictive CSP: the runtime can load, but Academy API requests cannot.
  const boot = `
const channel = ${JSON.stringify(channel)};
const parentOrigin = ${JSON.stringify(parentOrigin)};
const send = data => parent.postMessage({...data, channel}, parentOrigin);
const blob = new Blob([${JSON.stringify(workerSource(index))}], {type:'text/javascript'});
const workerURL = URL.createObjectURL(blob);
let worker = new Worker(workerURL, {type:'classic'});
let started = false, runID = '';
const stop = () => {if(worker) worker.terminate(); worker = null; URL.revokeObjectURL(workerURL);};
worker.onmessage = ({data}) => {
  if(data?.type === 'ready' && !started) send({type:'ready'});
  else if(data?.type === 'load-error' && !started) {stop(); send({type:'load-error', message:String(data.message || '').slice(0,500)});}
  else if(data?.type === 'result' && started && data.id === runID) {
    stop();
    send({type:'result', id:runID, output:String(data.output || '').slice(0,16000), error:String(data.error || '').slice(-5000), truncated:!!data.truncated});
  }
};
worker.onerror = event => {event.preventDefault(); stop(); send({type:'load-error', message:'Python could not load. Check your connection, then try again. ' + String(event.message || '').slice(0,350)});};
addEventListener('message', event => {
  if(event.source !== parent || event.origin !== parentOrigin || event.data?.channel !== channel) return;
  const data = event.data;
  if(data.type === 'stop') {stop(); return;}
  if(data.type !== 'run' || started || !worker || typeof data.id !== 'string' || typeof data.code !== 'string' || data.code.length > 20000 || typeof data.stdin !== 'string' || data.stdin.length > 8000) return;
  started = true; runID = data.id;
  worker.postMessage({type:'run', id:runID, code:data.code, stdin:data.stdin});
});`;
  return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${policy}"><meta name="referrer" content="no-referrer"></head><body><script nonce="${channel}">${boot}</script></body></html>`;
}

export type PracticeReply = {type: 'ready'} | {type:'load-error'; message:string} |
  {type:'result'; id:string; output:string; error:string; truncated:boolean};

export function readPracticeReply(data: unknown, channel: string, runID: string | null): PracticeReply | null {
  if (!data || typeof data !== 'object') return null;
  const value = data as Record<string, unknown>;
  if (value.channel !== channel) return null;
  if (value.type === 'ready') return {type:'ready'};
  if (value.type === 'load-error') return {type:'load-error', message:typeof value.message === 'string' ? value.message.slice(0,500) : 'Python could not load. Check your connection and try again.'};
  if (value.type !== 'result' || !runID || value.id !== runID || typeof value.output !== 'string' || typeof value.error !== 'string') return null;
  return {type:'result', id:runID, output:value.output.slice(0,MAX_OUTPUT), error:value.error.slice(-5000), truncated:!!value.truncated};
}
