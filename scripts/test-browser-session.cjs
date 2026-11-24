const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
class ApiError extends Error {constructor(message,status){super(message);this.status=status;}}
const file=fs.readFileSync(require('node:path').resolve(__dirname,'../lib/browser-session.ts'),'utf8');
const compiled=ts.transpileModule(file,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
function fixture(responses) {
  const calls=[],events=new Map(),channels=[],redirects=[],saved=[];
  const window={addEventListener:(type,fn)=>{if(!events.has(type))events.set(type,new Set());events.get(type).add(fn);},
    removeEventListener:(type,fn)=>events.get(type)?.delete(fn),dispatchEvent:event=>{for(const fn of events.get(event.type)||[])fn(event);},
    location:{replace:url=>redirects.push(url)}};
  class BroadcastChannel {constructor(name){this.name=name;channels.push(this);} postMessage(data){this.sent=data;}close(){this.closed=true;}}
  const exports={};
  vm.runInNewContext(compiled,{exports,require:()=>({api:async(path,body)=>{calls.push({path,body});const value=responses.shift();if(value instanceof Error)throw value;return value;},ApiError}),
    window,localStorage:{setItem:(key,value)=>saved.push([key,value])},BroadcastChannel,crypto:{randomUUID:()=> 'test-event'},Date,Event:class Event{constructor(type){this.type=type;}}});
  return {exports,calls,window,channels,redirects,saved};
}
async function main(){
  const normal=fixture([{}]);await normal.exports.endBrowserSession();
  assert.equal(normal.calls[0].path,'/auth/session-logout/');assert.equal(normal.redirects[0],'/?signed_out=1#signin');assert.equal(normal.saved.length,1);
  const offline=fixture([new Error('offline')]);await assert.rejects(offline.exports.endBrowserSession());assert.equal(offline.redirects.length,0);
  const csrf=fixture([new ApiError('csrf',403),{username:'still-signed-in'}]);await assert.rejects(csrf.exports.endBrowserSession());assert.equal(csrf.saved.length,0);assert.equal(csrf.redirects.length,0);
  const expired=fixture([new ApiError('expired',403),new ApiError('signed-out',403)]);await expired.exports.endBrowserSession();assert.equal(expired.redirects.length,1);
  const listener=fixture([]);let count=0;const cleanup=listener.exports.watchSessionEnd(()=>count++);
  listener.window.dispatchEvent({type:'storage',key:'unrelated',newValue:'x'});assert.equal(count,0);
  listener.window.dispatchEvent({type:'storage',key:listener.exports.SESSION_ENDED_KEY,newValue:'event'});
  listener.channels[0].onmessage({data:'ended'});listener.window.dispatchEvent({type:'saire:session-ended'});assert.equal(count,1,'duplicate notifications must not redirect repeatedly');
  cleanup();assert.equal(listener.channels[0].closed,true);
  console.log('PASS: real-logout request, expired-session handling, no false success on CSRF/network failure, cross-tab signal and cleanup.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
