const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const {renderToStaticMarkup} = require('react-dom/server');
const cache = new Map();
function load(relative) {
  const file = path.resolve(__dirname,'..',relative);
  if (cache.has(file)) return cache.get(file).exports;
  const code = ts.transpileModule(fs.readFileSync(file,'utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
  const mod = new Module(file,module); mod.filename=file;mod.paths=Module._nodeModulePaths(path.dirname(file));cache.set(file,mod);
  mod.require = name => {
    if (name.startsWith('@/')) return load(name.slice(2)+(name.includes('components/') ? '.tsx' : '.ts'));
    const relative = path.resolve(path.dirname(file), name+'.ts');
    if (name.startsWith('.') && fs.existsSync(relative)) return load(path.relative(path.resolve(__dirname,'..'),relative));
    return Module.prototype.require.call(mod,name);
  };
  mod._compile(code,file); return mod.exports;
}
const runtime = load('lib/python-practice.ts');
const channel = 'a'.repeat(32), origin='https://academy.example';
const document = runtime.createPracticeFrame(channel,origin);
assert.throws(()=>runtime.createPracticeFrame('" onload="bad',origin));
assert.throws(()=>runtime.createPracticeFrame(channel,'javascript:alert(1)'));
assert.throws(()=>runtime.createPracticeFrame(channel,origin+'/extra'));
assert.match(document,/default-src 'none'/);
assert.match(document,/connect-src https:\/\/academy\.example\/python-runtime\/v0\.29\.5\//);
assert.doesNotMatch(document,/connect-src 'self'|'unsafe-inline'|'unsafe-eval'|allow-same-origin/);

function frame() {
  let handler, worker, source, revoked=false; const messages=[];
  const parent={postMessage:(message,target)=>messages.push({message,target})};
  class Blob {constructor(parts){this.parts=parts;}}
  class Worker {constructor(url,options){worker=this;this.options=options;this.sent=[];this.terminated=false;}
    postMessage(data){this.sent.push(data);} terminate(){this.terminated=true;}}
  const URL={createObjectURL:blob=>{source=blob.parts.join('');return 'blob:opaque-runner';},revokeObjectURL:()=>{revoked=true;}};
  const boot=document.match(/<script nonce="[^"]+">([\s\S]+)<\/script>/)[1];
  vm.runInNewContext(boot,{Blob,Worker,URL,parent,addEventListener:(type,fn)=>{handler=fn;}});
  return {worker,messages,parent,source,post:data=>handler({source:parent,origin,data:{channel,...data}}),raw:handler,get revoked(){return revoked;}};
}
const f=frame();assert.equal(f.worker.options.type,'classic');
f.raw({source:{},origin,data:{channel,type:'run',id:'1',code:'print(1)',stdin:''}});
f.raw({source:f.parent,origin:'https://other.example',data:{channel,type:'run',id:'1',code:'print(1)',stdin:''}});
f.post({channel:'wrong',type:'run',id:'1',code:'print(1)',stdin:''});
assert.equal(f.worker.sent.length,0,'untrusted message must not start execution');
f.worker.onmessage({data:{type:'ready'}});assert.equal(f.messages[0].target,origin);
assert.equal(f.messages[0].message.channel,channel);
f.post({type:'run',id:'1',code:'x'.repeat(runtime.MAX_CODE+1),stdin:''});assert.equal(f.worker.sent.length,0);
f.post({type:'run',id:'1',code:'print("</script>")',stdin:'Ada\n'});assert.equal(f.worker.sent.length,1);
f.post({type:'run',id:'2',code:'print(2)',stdin:''});assert.equal(f.worker.sent.length,1,'one run per worker');
f.worker.onmessage({data:{type:'result',id:'wrong',output:'fake',error:''}});assert.equal(f.messages.length,1);
f.worker.onmessage({data:{type:'result',id:'1',output:'x'.repeat(20000),error:'',truncated:true}});
assert.equal(f.messages[1].message.output.length,runtime.MAX_OUTPUT);assert.equal(f.worker.terminated,true);assert.equal(f.revoked,true);
assert.equal(runtime.readPracticeReply({channel:'wrong',type:'ready'},channel,null),null);
assert.equal(runtime.readPracticeReply({channel,type:'result',id:'old',output:'x',error:''},channel,'new'),null);
assert.equal(runtime.readPracticeReply({channel,type:'result',id:'new',output:{html:'bad'},error:''},channel,'new'),null);
assert.equal(runtime.readPracticeReply({channel,type:'result',id:'new',output:'<b>text</b>',error:'e'.repeat(6000)},channel,'new').error.length,5000);
const stopped=frame();stopped.post({type:'stop'});assert.equal(stopped.worker.terminated,true);
const failed=frame();failed.worker.onerror({preventDefault(){}});assert.equal(failed.messages[0].message.type,'load-error');

const Practice=load('components/PythonPractice.tsx').default;
const html=renderToStaticMarkup(React.createElement(Practice,{owner:'test',lessonId:'p1-l1',example:'print("Hello")\n'}));
assert.match(html,/Load Python/);assert.match(html,/Practice · not graded/);assert.match(html,/own IDE, Git/);
assert.doesNotMatch(html,/<iframe|srcDoc=|type="submit"/,'runtime must be opt-in, not a grading form');
const Controls=load('components/AccountControls.tsx').default;
const signedIn=renderToStaticMarkup(React.createElement(Controls,{username:'learner'}));
const signedOut=renderToStaticMarkup(React.createElement(Controls,{username:null}));
assert.match(signedIn,/>Log out</);assert.match(signedOut,/href="\/#signin"/);assert.match(signedOut,/>Sign in</);
async function checkStreams() {
  let input, output, captured, destroyed=false;
  const globals={set(){},destroy(){destroyed=true;}};
  const py={setStdin(value){input=value.stdin;},setStdout(value){output=value.write;},setStderr(){},runPython(){return globals;},
    async runPythonAsync(){captured=[input(),input(),input()];output(new TextEncoder().encode('Hello, learner!\n'));}};
  const replies=[];const self={postMessage:value=>replies.push(value)};
  const code=f.source.replace(/importScripts\([^;]+\);/, 'const loadPyodide = injectedLoad;');
  await vm.runInNewContext(code,{self,injectedLoad:async()=>py,TextDecoder});
  await self.onmessage({data:{type:'run',id:'streams',code:'print(1)',stdin:'Ada\r\nLerato\n'}});
  assert.deepEqual(captured,['Ada','Lerato',null]);
  assert.equal(replies[1].output,'Hello, learner!\n');assert.equal(replies[1].error,'');assert.equal(destroyed,true);
  console.log('PASS: runtime isolation/protocol, bounded output, fresh-worker cleanup, input/output streams, lazy editor and visible account controls.');
}
checkStreams().catch(error=>{console.error(error);process.exitCode=1;});
